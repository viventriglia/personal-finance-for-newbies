import bcrypt

from mongo import init_connection


def hash_psw(psw: str) -> str:
    return bcrypt.hashpw(psw.encode(), bcrypt.gensalt()).decode()


def verify_psw(psw: str, hashed_psw: str) -> bool:
    return bcrypt.checkpw(psw.encode(), hashed_psw.encode())


def register_user(username: str, psw: str) -> bool:
    client = init_connection()
    users = client["pfn"]["users"]
    if users.find_one({"username": username}):
        return False
    else:
        hashed_psw = hash_psw(psw)
        users.insert_one({"username": username, "password": hashed_psw})
        return True


def login_user(username: str, psw: str) -> bool:
    client = init_connection()
    users = client["pfn"]["users"]
    usr = users.find_one({"username": username})
    if usr and verify_psw(psw, usr["password"]):
        return True
    else:
        return False
