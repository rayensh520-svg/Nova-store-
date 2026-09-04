from flask import session


def create_session(user):
    session.clear()

    session["user_id"] = user["id"]
    session["user_role"] = user["role"]


def destroy_session():
    session.clear()


def get_current_user_id():
    return session.get("user_id")


def get_current_user_role():
    return session.get("user_role")


def is_authenticated():
    return "user_id" in session
