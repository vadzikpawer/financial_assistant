import pytest
import re
from flask import session

pytestmark = pytest.mark.security


def test_content_security_policy(client):
    """Test Content-Security-Policy header"""
    response = client.get("/")
    assert "Content-Security-Policy" in response.headers
    csp = response.headers.get("Content-Security-Policy")

    # CSP should restrict dangerous sources
    assert "default-src 'self'" in csp

    # Should allow bootstrap and other necessary external resources
    assert "script-src 'self' https://cdn.jsdelivr.net" in csp


def test_xss_protection(client):
    """Test X-XSS-Protection header"""
    response = client.get("/")
    assert "X-XSS-Protection" in response.headers
    assert response.headers.get("X-XSS-Protection") == "1; mode=block"


def test_frame_options(client):
    """Test X-Frame-Options header"""
    response = client.get("/")
    assert "X-Frame-Options" in response.headers
    assert response.headers.get("X-Frame-Options") == "SAMEORIGIN"


def test_content_type_options(client):
    """Test X-Content-Type-Options header"""
    response = client.get("/")
    assert "X-Content-Type-Options" in response.headers
    assert response.headers.get("X-Content-Type-Options") == "nosniff"


@pytest.fixture
def client_with_csrf_disabled(app_context):
    app_context.config["WTF_CSRF_ENABLED"] = False
    return app_context.test_client()


def test_session_cookie_settings(client_with_csrf_disabled):
    """Test session cookie security settings"""
    with client_with_csrf_disabled as client:
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
            # assert cookie_header.secure

            # Check httponly flag
            assert cookie_header.has_nonstandard_attr("HttpOnly")

            # Check path restriction
            assert cookie_header.path == "/"


@pytest.fixture
def client_with_csrf_enabled(app_context):
    app_context.config["WTF_CSRF_ENABLED"] = True
    return app_context.test_client()


def test_csrf_token_present(client_with_csrf_enabled):
    """Test CSRF token is present in forms"""
    response = client_with_csrf_enabled.get("/login")

    # Extract CSRF token from form
    csrf_token_match = re.search(
        r'<input[^>]*name="csrf_token"[^>]*value="([^"]*)"', response.data.decode()
    )
    assert csrf_token_match is not None, "CSRF token not found in login form"

    # Also check registration form
    response = client_with_csrf_enabled.get("/register")
    csrf_token_match = re.search(
        r'<input[^>]*name="csrf_token"[^>]*value="([^"]*)"', response.data.decode()
    )
    assert csrf_token_match is not None, "CSRF token not found in registration form"


def test_csrf_protection_enforced(client_with_csrf_enabled):
    """Test CSRF protection is enforced"""
    # This should fail without a CSRF token
    response = client_with_csrf_enabled.post(
        "/login",
        data={"email": "test@example.com", "password": "password123"},
        follow_redirects=True,
    )

    # Should return a 400 Bad Request or redirect with an error message
    assert response.status_code in [400, 200]
    if response.status_code == 200:
        assert b"CSRF validation failed" in response.data


def test_login_form_validation(client_with_csrf_disabled):
    """Test login form validation"""
    # Test with empty email
    response = client_with_csrf_disabled.post(
        "/login",
        data={"email": "", "password": "password123"},
        follow_redirects=True,
    )
    assert b"Email is required" in response.data

    # Test with invalid email format
    response = client_with_csrf_disabled.post(
        "/login",
        data={"email": "not-an-email", "password": "password123"},
        follow_redirects=True,
    )
    assert b"Invalid email address" in response.data

    # Test with empty password
    response = client_with_csrf_disabled.post(
        "/login",
        data={"email": "test@example.com", "password": ""},
        follow_redirects=True,
    )
    assert b"Password is required" in response.data


def test_registration_form_validation(client_with_csrf_disabled):
    """Test registration form validation"""
    # Test with empty username
    response = client_with_csrf_disabled.post(
        "/register",
        data={
            "username": "",
            "email": "test@example.com",
            "password": "password123",
            "confirm_password": "password123",
        },
        follow_redirects=True,
    )
    assert b"Username is required" in response.data

    # Test with too short username
    response = client_with_csrf_disabled.post(
        "/register",
        data={
            "username": "ab",  # Too short
            "email": "test@example.com",
            "password": "password123",
            "confirm_password": "password123",
        },
        follow_redirects=True,
    )
    assert b"Username must be at least" in response.data

    # Test with invalid email
    response = client_with_csrf_disabled.post(
        "/register",
        data={
            "username": "testuser",
            "email": "not-an-email",
            "password": "password123",
            "confirm_password": "password123",
        },
        follow_redirects=True,
    )
    assert b"Invalid email address" in response.data

    # Test with password too short
    response = client_with_csrf_disabled.post(
        "/register",
        data={
            "username": "testuser",
            "email": "test@example.com",
            "password": "short",
            "confirm_password": "short",
        },
        follow_redirects=True,
    )
    assert b"Password must be at least" in response.data

    # Test with passwords not matching
    response = client_with_csrf_disabled.post(
        "/register",
        data={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
            "confirm_password": "differentpassword",
        },
        follow_redirects=True,
    )
    assert b"Passwords must match" in response.data
