import os
import re
import sqlite3
from functools import wraps
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from chatbot import CampusMateBot

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "instance", "campusmate_users.db")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("CAMPUSMATE_SECRET_KEY", "change-this-secret-key-before-deployment")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
bot = CampusMateBot()


def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_db() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"reply": "Please log in to use CampusMate."}), 401
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


@app.route("/")
def home():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("index.html", full_name=session.get("full_name", "Student"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("home"))
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not full_name or not email or not password or not confirm_password:
            flash("Please fill in all fields.", "error")
        elif not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
            flash("Please enter a valid email address.", "error")
        elif len(password) < 8:
            flash("Password must contain at least 8 characters.", "error")
        elif password != confirm_password:
            flash("Passwords do not match.", "error")
        else:
            try:
                with get_db() as connection:
                    cursor = connection.execute(
                        "INSERT INTO users (full_name, email, password_hash) VALUES (?, ?, ?)",
                        (full_name, email, generate_password_hash(password))
                    )
                    session.clear()
                    session["user_id"] = cursor.lastrowid
                    session["full_name"] = full_name
                return redirect(url_for("home"))
            except sqlite3.IntegrityError:
                flash("An account with this email already exists. Please log in.", "error")
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("home"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        with get_db() as connection:
            user = connection.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["full_name"] = user["full_name"]
            return redirect(url_for("home"))
        flash("Incorrect email or password.", "error")
    return render_template("login.html")


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/api/chat", methods=["POST"])
@login_required
def chat():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"reply": "Please type a question."}), 400
    return jsonify({"reply": bot.get_response(message)})


@app.route("/api/departments", methods=["GET"])
@login_required
def get_departments():
    return jsonify(bot.get_departments())


init_db()

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
