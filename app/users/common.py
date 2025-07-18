import secrets
import string


def generate_user_code(length: int = 7) -> str:
    alphabet = string.ascii_letters + string.digits  # a-zA-Z0-9
    return "".join(secrets.choice(alphabet) for _ in range(length))
