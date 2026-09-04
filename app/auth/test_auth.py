from app.auth.validation import (
    validate_email,
    validate_password,
    validate_role,
)


def test_validation():
    assert validate_email("test@example.com")
    assert validate_password("12345678")
    assert validate_role("buyer")
    assert not validate_role("admin")

    print("NOVA AUTH VALIDATION: OK")


if __name__ == "__main__":
    test_validation()
