from datetime import datetime

import bcrypt
import pandas as pd

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
        users.insert_one(
            {
                "username": username,
                "password": hashed_psw,
                "created_at": datetime.utcnow(),
                "last_login": None,
            }
        )
        return True


def login_user(username: str, psw: str) -> bool:
    client = init_connection()
    users = client["pfn"]["users"]
    usr = users.find_one({"username": username})
    if usr and verify_psw(psw, usr["password"]):
        users.update_one(
            {"username": username}, {"$set": {"last_login": datetime.utcnow()}}
        )
        return True
    else:
        return False


def get_user_transactions(user_id: str) -> pd.DataFrame:
    transactions = init_connection()["pfn"]["transactions"]
    user_transactions = transactions.find({"user_id": user_id})
    df = pd.DataFrame(list(user_transactions))

    cols = ["ticker", "transaction_type", "quantity", "price", "date"]

    if df.empty:
        return pd.DataFrame(columns=cols)
    if "asset" in df.columns:
        df["ticker"] = df["asset"].apply(lambda x: x.get("ticker", ""))
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%d-%m-%Y")
    df.index += 1

    missing_cols = [col for col in cols if col not in df.columns]
    if missing_cols:
        for col in missing_cols:
            df[col] = ""

    return df[cols]
