"""Regression tests for CampusMate college knowledge and conversation handling."""
import unittest
from chatbot import CampusMateBot
from app import app


class CampusMateKnowledgeBaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bot = CampusMateBot()

    def test_department_hods_are_separate(self):
        self.assertIn("Dr. Basappa Kodada", self.bot.get_response("Who is the HOD of AI & ML?"))
        self.assertIn("Deepak D", self.bot.get_response("Who is the HOD of AI & DS?"))
        self.assertNotIn("Dr. Basappa Kodada", self.bot.get_response("Who is the HOD of AI & DS?"))

    def test_first_year_subject_filter(self):
        answer = self.bot.get_response("Show First Year Mathematics faculty")
        self.assertIn("Mathematics Faculty", answer)
        self.assertIn("Dr. Prameela Kolake", answer)
        self.assertNotIn("Chemistry:", answer)
        self.assertNotIn("Physics:", answer)

    def test_hostel_wardens_are_separated(self):
        boys = self.bot.get_response("Show boys hostel wardens")
        girls = self.bot.get_response("Show girls hostel wardens")
        self.assertIn("Shabarish Kumar B. V.", boys)
        self.assertIn("Manoj Kumar", boys)
        self.assertNotIn("Meera P.", boys)
        self.assertIn("Meera P.", girls)
        self.assertIn("Usha K.", girls)
        self.assertNotIn("Shabarish Kumar B. V.", girls)

    def test_bus_routes(self):
        self.assertIn("Mr. Subramanya", self.bot.get_response("Route 2 details"))
        self.assertIn("Mrs. Bhavya", self.bot.get_response("Route 14 details"))

    def test_all_canteen_details(self):
        self.assertIn("7:30 AM", self.bot.get_response("CEC Canteen timings"))
        self.assertIn("8:45 PM", self.bot.get_response("Can Cafe timings"))
        self.assertIn("4:30 PM", self.bot.get_response("Can Express timings"))
        self.assertIn("₹10–₹50 per person", self.bot.get_response("Can Express price"))

    def test_library_staff(self):
        answer = self.bot.get_response("Show library staff")
        for name in ["Bhavani K", "Santhosh", "Lokesh", "Chaithra"]:
            self.assertIn(name, answer)

    def test_fees_and_admission_intents_do_not_conflict(self):
        self.assertIn("₹95,000", self.bot.get_response("What is the KCET fee?"))
        self.assertIn("Accepted entrance examinations", self.bot.get_response("Which entrance exams are accepted?"))

    def test_scholarships_point_to_official_site(self):
        answer = self.bot.get_response("What scholarships are available?")
        self.assertIn("https://www.cec.edu.in/", answer)
        self.assertIn("have not been provided", answer)

    def test_small_talk(self):
        self.assertIn("Welcome to CampusMate", self.bot.get_response("hello"))
        self.assertIn("doing great", self.bot.get_response("how are you"))
        self.assertIn("most welcome", self.bot.get_response("thank you"))
        self.assertIn("Goodbye", self.bot.get_response("bye"))


class CampusMateAuthTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True, WTF_CSRF_ENABLED=False, SECRET_KEY="test-secret")
        self.client = app.test_client()
        # Use a separate temporary test database for each test.
        import tempfile
        self.temp_dir = tempfile.TemporaryDirectory()
        import app as app_module
        self.old_db_path = app_module.DB_PATH
        app_module.DB_PATH = self.temp_dir.name + "/test_users.db"
        app_module.init_db()

    def tearDown(self):
        import app as app_module
        app_module.DB_PATH = self.old_db_path
        self.temp_dir.cleanup()

    def test_register_then_logout_then_login(self):
        response = self.client.post("/register", data={
            "full_name": "Test Student", "email": "student@example.com",
            "password": "securepass123", "confirm_password": "securepass123"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Chat with CampusMate", response.data)
        self.client.post("/logout", follow_redirects=True)
        response = self.client.post("/login", data={
            "email": "student@example.com", "password": "securepass123"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Chat with CampusMate", response.data)

    def test_chat_requires_login(self):
        response = self.client.post("/api/chat", json={"message": "hello"})
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main(verbosity=2)
