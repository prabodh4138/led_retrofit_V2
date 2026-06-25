import streamlit as st
from modules.dashboard import show_dashboard
from modules.entry import show_entry_form
from modules.reports import show_reports
from modules.target_master import show_target_master
from modules.pole_transactions import show_pole_transactions

from utils.auth import (
    initialize_session,
    login_user,
    logout_user,
    require_login
)

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="LED Retrofit V2",
    page_icon="💡",
    layout="wide"
)

# =====================================================
# SESSION INIT
# =====================================================

initialize_session()

# =====================================================
# LOGIN SCREEN
# =====================================================

if not st.session_state.logged_in:

    st.title("💡 LED Retrofit V2")

    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:

        st.subheader("User Login")

        email = st.text_input(
            "Email",
            placeholder="Enter Email"
        )

        password = st.text_input(
            "Password",
            type="password"
        )

        login_btn = st.button(
            "Login",
            use_container_width=True
        )

        if login_btn:

            if not email or not password:

                st.error(
                    "Email and Password required"
                )

            else:

                success, message = login_user(
                    email,
                    password
                )

                if success:

                    st.success(message)

                    st.rerun()

                else:

                    st.error(message)

    st.stop()

# =====================================================
# SECURED AREA
# =====================================================

require_login()

# =====================================================
# SIDEBAR
# =====================================================

with st.sidebar:

    st.title("LED Retrofit V2")

    st.markdown("---")

    st.write(
        f"👤 {st.session_state.username}"
    )

    st.write(
        f"🔑 {st.session_state.role}"
    )

    st.write(
        f"📁 {st.session_state.project}"
    )

    st.markdown("---")

    role = st.session_state.role

    # ---------------------------------------------
    # Vendor Menu
    # ---------------------------------------------

    if role == "vendor":

        menu = st.radio(
            "Navigation",
            [
                "Dashboard",
                "Entry Form",
                "Pending Matrix",
                "Completed Matrix",
                "Reports"
            ]
        )

    # ---------------------------------------------
    # Admin Menu
    # ---------------------------------------------

    elif role == "admin":

        menu = st.radio(
            "Navigation",
            [
                "Dashboard",
                "Pending Matrix",
                "Completed Matrix",
                "Reports",
                "Progress Report",
                "Audit Log"
            ]
        )

    # ---------------------------------------------
    # Super Admin Menu
    # ---------------------------------------------

    elif role == "super_admin":

        menu = st.radio(
            "Navigation",
            [
                "Dashboard",
                "Entry Form",
                "Pending Matrix",
                "Completed Matrix",
                "Reports",
                "Progress Report",
                "Audit Log",
                "User Management",
                "Target Master",
                "Pole Management",
                "Pole Transactions"
            ]
        )

    else:

        menu = "Dashboard"

    st.markdown("---")

    if st.button(
        "Logout",
        use_container_width=True
    ):
        logout_user()

# =====================================================
# MAIN SCREEN
# =====================================================

st.title(f"{menu}")

# =====================================================
# PLACEHOLDER MODULES
# =====================================================

if menu == "Dashboard":

    show_dashboard()

elif menu == "Entry Form":

    show_entry_form()

elif menu == "Pending Matrix":

    from modules.pending import show_pending_matrix

    show_pending_matrix()

elif menu == "Completed Matrix":

    from modules.completed import show_completed_matrix

    show_completed_matrix()

elif menu == "Reports":

    show_reports()

elif menu == "Progress Report":

    from modules.progress_report import show_progress_report

    show_progress_report()

elif menu == "Audit Log":

    from modules.audit_log import show_audit_log
    show_audit_log()

elif menu == "User Management":

    from modules.user_management import show_user_management
    show_user_management()

elif menu == "Target Master":

    show_target_master()
elif menu == "Pole Transactions":

    from modules.pole_transactions import show_pole_transactions
    show_pole_transactions()