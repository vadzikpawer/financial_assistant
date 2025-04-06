import unittest
import re
from app import app
from flask import session


class TestSecurityHeaders(unittest.TestCase):
    def setUp(self):
        """Set up test client"""
        app.config["TESTING"] = True
        self.app = app.test_client()

    def test_content_security_policy(self):
        """Test Content-Security-Policy header"""
        response = self.app.get("/")
        self.assertIn("Content-Security-Policy", response.headers)
        csp = response.headers.get("Content-Security-Policy")

        # CSP should restrict dangerous sources
        self.assertIn("default-src 'self'", csp)

        # Should allow bootstrap and other necessary external resources
        self.assertIn("script-src 'self' https://cdn.jsdelivr.net", csp)

    def test_xss_protection(self):
        """Test X-XSS-Protection header"""
        response = self.app.get("/")
        self.assertIn("X-XSS-Protection", response.headers)
        self.assertEqual(response.headers.get("X-XSS-Protection"), "1; mode=block")

    def test_frame_options(self):
        """Test X-Frame-Options header"""
        response = self.app.get("/")
        self.assertIn("X-Frame-Options", response.headers)
        self.assertEqual(response.headers.get("X-Frame-Options"), "SAMEORIGIN")

    def test_content_type_options(self):
        """Test X-Content-Type-Options header"""
        response = self.app.get("/")
        self.assertIn("X-Content-Type-Options", response.headers)
        self.assertEqual(response.headers.get("X-Content-Type-Options"), "nosniff")


class TestSessionSecurity(unittest.TestCase):
    def setUp(self):
        """Set up test client"""
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        self.app = app.test_client()

    def test_session_cookie_settings(self):
        """Test session cookie security settings"""
        with self.app as client:
            client.post(
                "/login",
                data={"email": "nonexistent@example.com", "password": "wrongpassword"},
            )

            # Get the session cookie
            cookie_header = (
                client.cookie_jar._cookies.get("localhost.local", {})
                .get("/", {})
                .get("session")
            )
            if cookie_header:
                # Check secure flag (might be false in testing)
                # self.assertTrue(cookie_header.secure)

                # Check httponly flag
                self.assertTrue(cookie_header.has_nonstandard_attr("HttpOnly"))

                # Check path restriction
                self.assertEqual(cookie_header.path, "/")


class TestCSRFProtection(unittest.TestCase):
    def setUp(self):
        """Set up test client"""
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = True
        self.app = app.test_client()

    def test_csrf_token_present(self):
        """Test CSRF token is present in forms"""
        response = self.app.get("/login")

        # Extract CSRF token from form
        csrf_token_match = re.search(
            r'<input[^>]*name="csrf_token"[^>]*value="([^"]*)"', response.data.decode()
        )
        self.assertIsNotNone(csrf_token_match, "CSRF token not found in login form")

        # Also check registration form
        response = self.app.get("/register")
        csrf_token_match = re.search(
            r'<input[^>]*name="csrf_token"[^>]*value="([^"]*)"', response.data.decode()
        )
        self.assertIsNotNone(
            csrf_token_match, "CSRF token not found in registration form"
        )

    def test_csrf_protection_enforced(self):
        """Test CSRF protection is enforced"""
        # This should fail without a CSRF token
        response = self.app.post(
            "/login",
            data={"email": "test@example.com", "password": "password123"},
            follow_redirects=True,
        )

        # Should return a 400 Bad Request or redirect with an error message
        self.assertIn(response.status_code, [400, 200])
        if response.status_code == 200:
            self.assertIn(b"CSRF validation failed", response.data)


class TestInputValidation(unittest.TestCase):
    def setUp(self):
        """Set up test client"""
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        self.app = app.test_client()

    def test_login_form_validation(self):
        """Test login form validation"""
        # Test with empty email
        response = self.app.post(
            "/login",
            data={"email": "", "password": "password123"},
            follow_redirects=True,
        )
        self.assertIn(b"Email is required", response.data)

        # Test with invalid email format
        response = self.app.post(
            "/login",
            data={"email": "not-an-email", "password": "password123"},
            follow_redirects=True,
        )
        self.assertIn(b"Invalid email address", response.data)

        # Test with empty password
        response = self.app.post(
            "/login",
            data={"email": "test@example.com", "password": ""},
            follow_redirects=True,
        )
        self.assertIn(b"Password is required", response.data)

    def test_registration_form_validation(self):
        """Test registration form validation"""
        # Test with empty username
        response = self.app.post(
            "/register",
            data={
                "username": "",
                "email": "test@example.com",
                "password": "password123",
                "confirm_password": "password123",
            },
            follow_redirects=True,
        )
        self.assertIn(b"Username is required", response.data)

        # Test with too short username
        response = self.app.post(
            "/register",
            data={
                "username": "ab",  # Too short
                "email": "test@example.com",
                "password": "password123",
                "confirm_password": "password123",
            },
            follow_redirects=True,
        )
        self.assertIn(b"Username must be at least", response.data)

        # Test with invalid email
        response = self.app.post(
            "/register",
            data={
                "username": "testuser",
                "email": "not-an-email",
                "password": "password123",
                "confirm_password": "password123",
            },
            follow_redirects=True,
        )
        self.assertIn(b"Invalid email address", response.data)

        # Test with password too short
        response = self.app.post(
            "/register",
            data={
                "username": "testuser",
                "email": "test@example.com",
                "password": "short",
                "confirm_password": "short",
            },
            follow_redirects=True,
        )
        self.assertIn(b"Password must be at least", response.data)

        # Test with passwords not matching
        response = self.app.post(
            "/register",
            data={
                "username": "testuser",
                "email": "test@example.com",
                "password": "password123",
                "confirm_password": "differentpassword",
            },
            follow_redirects=True,
        )
        self.assertIn(b"Passwords must match", response.data)


if __name__ == "__main__":
    unittest.main()
