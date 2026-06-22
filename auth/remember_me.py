import hashlib
import json
import secrets
from datetime import datetime, timedelta

from config.paths import data_dir


def remember_file_path():
    return data_dir() / "remember_me.json"


TOKEN_VALID_DAYS = 30


def _hash_token(token):
    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()


def generate_token():
    return secrets.token_urlsafe(32)


def save_remember_data(username, token):
    remember_path = remember_file_path()
    remember_path.parent.mkdir(exist_ok=True)

    remember_path.write_text(
        json.dumps(
            {
                "username": username,
                "token": token,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def load_remember_data():
    remember_path = remember_file_path()

    if not remember_path.exists():
        return None

    try:
        data = json.loads(
            remember_path.read_text(
                encoding="utf-8"
            )
        )
    except (json.JSONDecodeError, OSError):
        clear_remember_data()
        return None

    username = data.get("username")
    token = data.get("token")

    if not username or not token:
        clear_remember_data()
        return None

    return {
        "username": username,
        "token": token,
    }


def clear_remember_data():
    remember_path = remember_file_path()

    if remember_path.exists():
        remember_path.unlink()


def get_expiry_time():
    return (
        datetime.now()
        + timedelta(days=TOKEN_VALID_DAYS)
    ).strftime("%Y-%m-%d %H:%M:%S")
