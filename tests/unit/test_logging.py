"""Unit tests for structured logging and secret scrubbing."""

from embedcraft.infrastructure.logging import redact_sensitive_data


def test_redact_sensitive_api_keys():
    event = {
        "event": "Sending request",
        "api_key": "sk-secret12345678901234567890",
        "auth_header": "Bearer sk-98765432101234567890",
        "normal_field": "hello world",
    }
    redacted = redact_sensitive_data(None, None, event)

    assert redacted["api_key"] == "[REDACTED]"
    assert "sk-" not in redacted["auth_header"]
    assert "[REDACTED]" in redacted["auth_header"]
    assert redacted["normal_field"] == "hello world"


def test_redact_nested_dict_secrets():
    event = {
        "event": "Provider config",
        "config": {
            "password": "supersecretpassword",
            "openai_api_key": "some-key",
            "port": 8080,
        },
    }
    redacted = redact_sensitive_data(None, None, event)
    assert redacted["config"]["password"] == "[REDACTED]"
    assert redacted["config"]["openai_api_key"] == "[REDACTED]"
    assert redacted["config"]["port"] == 8080
