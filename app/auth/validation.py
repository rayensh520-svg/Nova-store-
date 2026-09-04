import re

MIN_PASSWORD_LENGTH = 8

def normalize_email(email: str) -> str:
return email.strip().lower()

def validate_email(email: str) -> bool:
email = normalize_email(email)

return bool(
    re.fullmatch(
        r"[^@\s]+@[^@\s]+\.[^@\s]+",
        email
    )
)

def validate_password(password: str) -> bool:
if not isinstance(password, str):
return False

return len(password) >= MIN_PASSWORD_LENGTH

def validate_full_name(full_name: str) -> bool:
if not isinstance(full_name, str):
return False

name = " ".join(full_name.split())

return 2 <= len(name) <= 100

def validate_role(role: str) -> bool:
return role in {"buyer", "seller"}
