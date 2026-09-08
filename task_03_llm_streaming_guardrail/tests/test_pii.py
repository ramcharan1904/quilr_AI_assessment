from app.pii_detector import redact

def test_email():
    assert redact("alice@example.com") == "[REDACTED]"

def test_ssn():
    assert redact("123-45-6789") == "[REDACTED]"

def test_card():
    assert redact("4111 1111 1111 1111") == "[REDACTED]"
