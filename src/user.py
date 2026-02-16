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
    user_transactions = list(transactions.find({"user_id": user_id}))
    df = pd.DataFrame(user_transactions)

    if df.empty:
        return pd.DataFrame(
            columns=[
                "_id",
                "ticker_yf",
                "transaction_type",
                "shares",
                "price",
                "transaction_date",
                "fees",
            ]
        )

    df["_id"] = df["_id"].astype(str)

    if "transaction_type" in df.columns:
        df.loc[df["transaction_type"] == "Sell", "shares"] *= -1

    cols = [
        "_id",
        "ticker_yf",
        "transaction_type",
        "shares",
        "price",
        "transaction_date",
        "fees",
    ]
    df["transaction_date"] = pd.to_datetime(df["transaction_date"]).dt.date

    return df[cols].reset_index(drop=True)
