# CampusMate – AI College Assistant

CampusMate is a Flask-based college information chatbot for Canara Engineering College. It uses a local JSON knowledge base and TF-IDF question matching, plus explicit rules for structured college queries and conversational greetings. It is not connected to an external generative AI API.

## Features

- Student registration, login and logout.
- SQLite user database; passwords are stored as Werkzeug password hashes, not plain text.
- Login-protected chatbot and department API.
- Natural small talk: greetings, "how are you?", help, thanks and goodbye.
- Purple-and-white responsive interface with the CampusMate robot mascot at the bottom of the chat composer and in the sidebar.
- Department-wise HOD, teaching faculty and technical staff information.
- Hostel rules and separately listed boys' and girls' hostel wardens.
- Bus routes 1–12 and 14, with the information supplied by the user.
- CEC Canteen, Can Cafe and Can Express details as supplied by the user.
- Library facilities and library staff.
- College timings, events, holidays and academic calendar.
- Fees, scholarship website reference and B.E./B.Tech admission information.
- Unknown or unavailable information is not invented.

## Project structure

```text
CampusMate/
├── app.py
├── chatbot.py
├── requirements.txt
├── staff_data.json
├── faq_data.json
├── hostel_rules.json
├── bus_routes.json
├── canteen_data.json
├── library_data.json
├── college_info.json
├── academic_calendar.json
├── holiday_data.json
├── fee_data.json
├── admission_data.json
├── events_data.json
├── templates/
│   ├── index.html
│   ├── login.html
│   └── register.html
├── static/
│   ├── style.css
│   ├── script.js
│   └── images/campusmate-robot.png
├── instance/                 # SQLite database is created here at runtime
└── test_chatbot.py
```

## Requirements

- Python 3.11 recommended.
- Internet connection is needed on first load for Google Fonts; the chatbot itself uses local data.

## Run on Windows / VS Code

Open the extracted `CampusMate` folder in VS Code, then open Terminal and run:

```powershell
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000` in your browser. The first page is the registration/login page. Register with your name, email and a password of at least 8 characters. After registration, CampusMate opens the chatbot dashboard. Use Logout to return to the login page.

If PowerShell blocks virtual-environment activation, run this once in the same terminal:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

## Run tests

```powershell
python -m unittest -v test_chatbot.py
```

The tests cover department separation, first-year subject filtering, hostel warden separation, bus routes, canteen details, library staff, fees/admissions, scholarship links, small talk and authentication.

## Security notes

- Passwords are hashed with Werkzeug's password hashing utilities.
- SQLite database is local to this project and is created automatically at `instance/campusmate_users.db`.
- Before deploying publicly, set a long random `CAMPUSMATE_SECRET_KEY` environment variable and use HTTPS. This local demonstration does not include email verification or password reset.
- Do not upload the `instance/campusmate_users.db` file to a public repository because it contains registered user account records (passwords are hashed).

## Information accuracy

The JSON files contain information supplied in the project conversation and/or extracted from the user-provided college materials. Some dates, fees, rules and timings may be time-sensitive. Verify current official college notices before relying on them. Missing information is intentionally not guessed.
