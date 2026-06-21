import streamlit as st
import pandas as pd

from utils.db import supabase
from utils.auth import require_login


# =====================================================
# LOAD SUMMARY
# =====================================================

def load_summary():

    result = (
        supabase
        .table("vw_user_summary")
        .select("*")
        .execute()
    )

    if result.data:
        return result.data[0]

    return None


# =====================================================
# LOAD USERS
# =====================================================

def load_users():

    result = (
        supabase
        .table("vw_user_management")
        .select("*")
        .execute()
    )

    return pd.DataFrame(result.data)


# =====================================================
# UPDATE USER
# =====================================================

def update_user(
    user_id,
    role,
    project,
    is_active
):

    return (
        supabase
        .table("profiles")
        .update(
            {
                "role": role,
                "project": project,
                "is_active": is_active,
                "updated_at": pd.Timestamp.now(),
                "updated_by":
                st.session_state.username
            }
        )
        .eq("id", user_id)
        .execute()
    )


# =====================================================
# MAIN SCREEN
# =====================================================

def show_user_management():

    require_login()

    role = st.session_state.role

    if role == "vendor":

        st.error(
            "Access Denied"
        )

        return

    st.subheader(
        "User Management"
    )

    # ==========================================
    # KPI SUMMARY
    # ==========================================

    summary = load_summary()

    if summary:

        c1, c2, c3 = st.columns(3)

        with c1:

            st.metric(
                "Total Users",
                summary["total_users"]
            )

            st.metric(
                "Vendor Users",
                summary["vendor_users"]
            )

        with c2:

            st.metric(
                "Active Users",
                summary["active_users"]
            )

            st.metric(
                "Admin Users",
                summary["admin_users"]
            )

        with c3:

            st.metric(
                "Inactive Users",
                summary["inactive_users"]
            )

            st.metric(
                "Super Admin",
                summary["super_admin_users"]
            )

    st.divider()

    # ==========================================
    # USERS
    # ==========================================

    df = load_users()

    if df.empty:

        st.warning(
            "No users found"
        )

        return

    # ==========================================
    # FILTERS
    # ==========================================

    col1, col2, col3 = st.columns(3)

    with col1:

        project_filter = st.selectbox(
            "Project",
            [
                "All"
            ]
            +
            sorted(
                df["project"]
                .unique()
                .tolist()
            )
        )

    with col2:

        role_filter = st.selectbox(
            "Role",
            [
                "All"
            ]
            +
            sorted(
                df["role"]
                .unique()
                .tolist()
            )
        )

    with col3:

        status_filter = st.selectbox(
            "Status",
            [
                "All",
                "Active",
                "Inactive"
            ]
        )

    filtered_df = df.copy()

    if project_filter != "All":

        filtered_df = filtered_df[
            filtered_df["project"]
            == project_filter
        ]

    if role_filter != "All":

        filtered_df = filtered_df[
            filtered_df["role"]
            == role_filter
        ]

    if status_filter == "Active":

        filtered_df = filtered_df[
            filtered_df["is_active"]
            == True
        ]

    elif status_filter == "Inactive":

        filtered_df = filtered_df[
            filtered_df["is_active"]
            == False
        ]

    st.markdown(
        "### Users"
    )

    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # ==========================================
    # EDIT USER
    # ==========================================

    if role == "super_admin":

        st.markdown(
            "### Edit User"
        )

        usernames = (
            filtered_df["username"]
            .tolist()
        )

        selected_user = st.selectbox(
            "Select User",
            usernames
        )

        user_row = (
            filtered_df[
                filtered_df["username"]
                == selected_user
            ]
            .iloc[0]
        )

        new_role = st.selectbox(
            "Role",
            [
                "vendor",
                "admin"
            ],
            index=
            0
            if user_row["role"]
            == "vendor"
            else 1
        )

        project_options = [
            "SRTPL",
            "DTPL",
            "TEL",
            "ALL"
        ]

        project_index = (
            project_options.index(
                user_row["project"]
            )
            if user_row["project"]
            in project_options
            else 0
        )

        new_project = st.selectbox(
            "Project",
            project_options,
            index=project_index
        )

        new_status = st.checkbox(
            "Active",
            value=user_row["is_active"]
        )

        if st.button(
            "Update User",
            use_container_width=True
        ):

            try:

                update_user(
                    user_row["id"],
                    new_role,
                    new_project,
                    new_status
                )

                st.success(
                    "User Updated Successfully"
                )

                st.rerun()

            except Exception as e:

                st.error(
                    str(e)
                )

    st.divider()

    # ==========================================
    # EXPORT
    # ==========================================

    csv_data = (
        filtered_df
        .to_csv(index=False)
    )

    st.download_button(
        "Download Users CSV",
        csv_data,
        file_name="users.csv",
        mime="text/csv"
    )