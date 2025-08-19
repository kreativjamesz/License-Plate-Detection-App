import os, json, bcrypt

DATA_DIR = "app/data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")

def _ensure():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(USERS_FILE):
        admin_hash = bcrypt.hashpw(b"admin123", bcrypt.gensalt())
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump([{"id": 1, "username": "admin", "password_hash": admin_hash.decode("latin1")}], f, indent=2)

def _load():
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def _save(data):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

class JSONStore:
    def __init__(self):
        _ensure()

    def create_user(self, username: str, password_hash: bytes) -> int:
        users = _load()
        new_id = (max([u["id"] for u in users]) + 1) if users else 1
        users.append({"id": new_id, "username": username, "password_hash": password_hash.decode("latin1")})
        _save(users)
        return new_id

    def get_user(self, username: str):
        users = _load()
        for u in users:
            if u["username"] == username:
                return {"id": u["id"], "username": u["username"], "password_hash": u["password_hash"].encode("latin1")}
        return None
