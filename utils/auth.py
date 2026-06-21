# LED_retrofit_V2/utils/auth.py

import streamlit as st
from datetime import datetime
from zoneinfo import ZoneInfo

from utils.db import supabase


# =====================================================
# SESSION INITIALIZATION
# =====================================================

def initialize_session():

    defaults = {
        "logged_in": False,
        "user_id": None,
        "username": None,
        "role": None,
        "project": None,
        "email": None
    }

    for key, value in defaults.items():

        if key not in st.session_state:
            st.session_state[key] = value


# =====================================================
# IST TIME
# =====================================================

def ist_now():

    return datetime.now(
        ZoneInfo("Asia/Kolkata")
    )


# =====================================================
# LOAD USER PROFILE
# =====================================================

def load_profile(user_id):

    try:

        result = (
            supabase
            .table("profiles")
            .select("*")
            .eq("id", user_id)
            .execute()
        )

        if result.data:
            return result.data[0]

        return None

    except Exception:

        return None


# =====================================================
# LOGIN HISTORY
# =====================================================

def write_login_history(
    user_id,
    username,
    role,
    project,
    action="LOGIN"
):

    try:

        (
            supabase
            .table("login_history")
            .insert(
                {
                    "user_id": user_id,
                    "username": username,
                    "role": role,
                    "project": project,
                    "action": action,
                    "login_time": ist_now().isoformat()
                }
            )
            .execute()
        )

    except Exception as e:

        print(
            f"LOGIN_HISTORY ERROR : {e}"
        )


# =====================================================
# AUDIT LOG
# =====================================================

def write_audit_log(
    action,
    remarks="",
    table_name="auth",
    record_id=None,
    old_data=None,
    new_data=None
):

    try:

        (
            supabase
            .table("audit_log")
            .insert(
                {
                    "table_name": table_name,
                    "action": action,
                    "record_id": record_id,
                    "old_data": old_data,
                    "new_data": new_data,
                    "remarks": remarks,
                    "user_id": st.session_state.get("user_id"),
                    "username": st.session_state.get("username"),
                    "project": st.session_state.get("project"),
                    "created_at": ist_now().isoformat()
                }
            )
            .execute()
        )

    except Exception as e:

        print(
            f"AUDIT ERROR : {e}"
        )


# =====================================================
# LOGIN USER
# =====================================================

def login_user(
    email,
    password
):

    try:

        response = (
            supabase.auth.sign_in_with_password(
                {
                    "email": email,
                    "password": password
                }
            )
        )

        user = response.user

        if not user:

            return (
                False,
                "Invalid Email or Password"
            )

        profile = load_profile(
            user.id
        )

        if not profile:

            return (
                False,
                "Profile not found"
            )

        is_active = profile.get(
            "is_active",
            True
        )

        if not is_active:

            return (
                False,
                "User Disabled"
            )

        st.session_state.logged_in = True
        st.session_state.user_id = user.id
        st.session_state.username = profile["username"]
        st.session_state.role = profile["role"]
        st.session_state.project = profile["project"]
        st.session_state.email = email

        write_login_history(
            user.id,
            profile["username"],
            profile["role"],
            profile["project"],
            "LOGIN"
        )

        write_audit_log(
            action="LOGIN",
            remarks="User Logged In"
        )

        return (
            True,
            "Login Successful"
        )

    except Exception as e:

        return (
            False,
            str(e)
        )


# =====================================================
# LOGOUT USER
# =====================================================

def logout_user():

    try:

        write_login_history(
            st.session_state.get("user_id"),
            st.session_state.get("username"),
            st.session_state.get("role"),
            st.session_state.get("project"),
            "LOGOUT"
        )

        write_audit_log(
            action="LOGOUT",
            remarks="User Logged Out"
        )

        supabase.auth.sign_out()

    except Exception as e:

        print(
            f"LOGOUT ERROR : {e}"
        )

    keys = [
        "logged_in",
        "user_id",
        "username",
        "role",
        "project",
        "email"
    ]

    for key in keys:

        if key in st.session_state:
            del st.session_state[key]

    st.rerun()


# =====================================================
# SECURITY
# =====================================================

def require_login():

    if not st.session_state.get(
        "logged_in",
        False
    ):
        st.error(
            "Please Login First"
        )
        st.stop()


def require_admin():

    require_login()

    if (
        st.session_state.get("role")
        not in [
            "admin",
            "super_admin"
        ]
    ):

        st.error(
            "Admin Access Required"
        )

        st.stop()


def require_super_admin():

    require_login()

    if (
        st.session_state.get("role")
        != "super_admin"
    ):

        st.error(
            "Super Admin Access Required"
        )

        st.stop()


# =====================================================
# ROLE HELPERS
# =====================================================

def get_current_user():

    return (
        st.session_state
        .get("username")
    )


def get_current_role():

    return (
        st.session_state
        .get("role")
    )


def get_current_project():

    return (
        st.session_state
        .get("project")
    )


# =====================================================
# PROJECT ACCESS
# =====================================================

def get_allowed_projects():

    role = get_current_role()

    if role in [
        "admin",
        "super_admin"
    ]:

        return [
            "SRTPL",
            "DTPL",
            "TEL"
        ]

    return [
        st.session_state.get(
            "project"
        )
    ]


# =====================================================
# DELETE PERMISSION
# =====================================================

def can_delete():

    return (
        get_current_role()
        == "super_admin"
    )


# =====================================================
# EDIT PERMISSION
# =====================================================

def can_edit():

    return (
        get_current_role()
        in [
            "vendor",
            "super_admin"
        ]
    )


# =====================================================
# VIEW ALL PROJECTS
# =====================================================

def can_view_all_projects():

    return (
        get_current_role()
        in [
            "admin",
            "super_admin"
        ]
    )