import streamlit as st
import pandas as pd

from utils.db import supabase


# =====================================================
# LOAD AUDIT LOG
# =====================================================

def load_audit_log():

    result = (
        supabase
        .table("audit_log")
        .select("*")
        .order(
            "created_at",
            desc=True
        )
        .execute()
    )

    return pd.DataFrame(result.data)


# =====================================================
# MAIN SCREEN
# =====================================================

def show_audit_log():

    st.subheader(
        "Audit Log"
    )

    role = st.session_state.role

    if role == "vendor":

        st.warning(
            "Audit Log is available only for Admin users."
        )

        return

    df = load_audit_log()

    if df.empty:

        st.info(
            "No audit records found."
        )

        return

    # ==========================================
    # FILTERS
    # ==========================================

    st.markdown(
        "### Filters"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        project_filter = st.selectbox(
            "Project",
            ["All"]
            +
            sorted(
                df["project"]
                .dropna()
                .unique()
                .tolist()
            )
        )

    with col2:

        action_filter = st.selectbox(
            "Action",
            ["All"]
            +
            sorted(
                df["action"]
                .dropna()
                .unique()
                .tolist()
            )
        )

    with col3:

        user_filter = st.selectbox(
            "User",
            ["All"]
            +
            sorted(
                df["username"]
                .dropna()
                .unique()
                .tolist()
            )
        )

    # ==========================================
    # APPLY FILTERS
    # ==========================================

    filtered_df = df.copy()

    if project_filter != "All":

        filtered_df = filtered_df[
            filtered_df["project"]
            == project_filter
        ]

    if action_filter != "All":

        filtered_df = filtered_df[
            filtered_df["action"]
            == action_filter
        ]

    if user_filter != "All":

        filtered_df = filtered_df[
            filtered_df["username"]
            == user_filter
        ]

    # ==========================================
    # KPI SUMMARY
    # ==========================================

    st.markdown(
        "### Audit Summary"
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        st.metric(
            "Total Records",
            len(filtered_df)
        )

    with c2:

        insert_count = len(
            filtered_df[
                filtered_df["action"]
                == "INSERT"
            ]
        )

        st.metric(
            "INSERT",
            insert_count
        )

    with c3:

        update_count = len(
            filtered_df[
                filtered_df["action"]
                == "UPDATE"
            ]
        )

        st.metric(
            "UPDATE",
            update_count
        )

    st.divider()

    # ==========================================
    # AUDIT TABLE
    # ==========================================

    display_cols = [

        "created_at",

        "project",

        "username",

        "table_name",

        "action",

        "record_id",

        "remarks"

    ]

    st.markdown(
        "### Audit Records"
    )

    st.dataframe(
        filtered_df[
            display_cols
        ],
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # ==========================================
    # RECORD DETAILS
    # ==========================================

    st.markdown(
        "### Record Details"
    )

    selected_id = st.selectbox(
        "Select Audit Record",
        filtered_df["id"]
        .tolist()
    )

    selected_record = (
        filtered_df[
            filtered_df["id"]
            == selected_id
        ]
        .iloc[0]
    )

    tab1, tab2 = st.tabs(
        [
            "New Data",
            "Old Data"
        ]
    )

    with tab1:

        st.json(
            selected_record[
                "new_data"
            ]
        )

    with tab2:

        st.json(
            selected_record[
                "old_data"
            ]
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
        label="Download Audit Log CSV",
        data=csv_data,
        file_name="audit_log.csv",
        mime="text/csv"
    )