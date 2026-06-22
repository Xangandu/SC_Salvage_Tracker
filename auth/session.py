current_user = None
current_role = None
current_login_id = None


def set_session(user, login_id=None):
    global current_user, current_role, current_login_id

    current_user = user
    current_role = user["role_name"] if user else None
    current_login_id = login_id


def clear_session():
    global current_user, current_role, current_login_id

    current_user = None
    current_role = None
    current_login_id = None


def get_user():
    return current_user


def get_role():
    return current_role


def get_user_id():
    if current_user:
        return current_user["id"]
    return None


def get_login_id():
    return current_login_id
