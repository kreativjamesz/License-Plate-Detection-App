import bcrypt
from app.services.json_store import JSONStore

def _store():
    return JSONStore()

def register_user(username: str, password: str):
    if not username or not password:
        return False, "Username and password are required."
    if _store().get_user(username):
        return False, "Username already exists."
    pw_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    _store().create_user(username, pw_hash)
    return True, "Registered successfully."

def login_user(username: str, password: str):
    user = _store().get_user(username)
    if not user:
        return False, "User not found."
    if not bcrypt.checkpw(password.encode("utf-8"), user["password_hash"]):
        return False, "Wrong password."
    return True, "Login success."
