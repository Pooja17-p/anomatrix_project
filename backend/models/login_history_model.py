from config import login_history_collection
from datetime import datetime


def save_login_history(data):

    data["timestamp"] = datetime.now()

    login_history_collection.insert_one(data)


def get_user_logins(username):

    return list(
        login_history_collection.find(
            {"username": username},
            {"_id": 0}
        )
    )