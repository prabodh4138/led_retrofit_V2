import streamlit as st
import pandas as pd

from utils.db import supabase


# =====================================================
# LOAD DATA
# =====================================================

def load_work_progress():

    result = (
        supabase
        .table("vw_work_progress")
        .select("*")
        .execute()
    )

    return pd.DataFrame(result.data)


# =====================================================
# MAIN REPORTS
# =====================================================

def show_reports():

    st.subheader(
        "LED Retrofit Reports"
    )

    df = load_work_progress()

    if df.empty:

        st.warning(
            "No report data available."
        )

        return

    # ==========================================
    # ROLE FILTER
    # ==========================================

    role = st.session_state.role
    user_project = st.session_state.project

    if (
        role == "vendor"
        and user_project != "ALL"
    ):

        df = df[
            df["project"]
            == user_project
        ]

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
                .unique()
                .tolist()
            )
        )

    with col2:

        team_filter = st.selectbox(
            "Team",
            ["All"]
            +
            sorted(
                df["team"]
                .unique()
                .tolist()
            )
        )

    with col3:

        status_filter = st.selectbox(
            "Status",
            ["All"]
            +
            sorted(
                df["status"]
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

    if team_filter != "All":

        filtered_df = filtered_df[
            filtered_df["team"]
            == team_filter
        ]

    if status_filter != "All":

        filtered_df = filtered_df[
            filtered_df["status"]
            == status_filter
        ]

    # ==========================================
    # KPI SUMMARY
    # ==========================================

    st.markdown(
        "### Report Summary"
    )

    total_target = int(
        filtered_df["target_qty"].sum()
    )

    total_dismantled = int(
        filtered_df["dismantled_qty"].sum()
    )

    total_installed = int(
        filtered_df["installed_qty"].sum()
    )

    progress_pct = round(
        (
            total_installed
            /
            total_target
            * 100
        )
        if total_target > 0
        else 0,
        2
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            "Target",
            total_target
        )

    with c2:
        st.metric(
            "Dismantled",
            total_dismantled
        )

    with c3:
        st.metric(
            "Installed",
            total_installed
        )

    with c4:
        st.metric(
            "Progress %",
            progress_pct
        )

    st.divider()

    # ==========================================
    # PROJECT REPORT
    # ==========================================

    st.markdown(
        "### Project Wise Report"
    )

    project_report = (
        filtered_df
        .groupby(
            "project",
            as_index=False
        )
        .agg(
            {
                "target_qty": "sum",
                "dismantled_qty": "sum",
                "installed_qty": "sum",
                "pending_dismantle": "sum",
                "pending_installation": "sum"
            }
        )
    )

    st.dataframe(
        project_report,
        use_container_width=True,
        hide_index=True
    )

    # ==========================================
    # TEAM REPORT
    # ==========================================

    st.markdown(
        "### Team Wise Report"
    )

    team_report = (
        filtered_df
        .groupby(
            "team",
            as_index=False
        )
        .agg(
            {
                "target_qty": "sum",
                "dismantled_qty": "sum",
                "installed_qty": "sum",
                "pending_dismantle": "sum",
                "pending_installation": "sum"
            }
        )
    )

    st.dataframe(
        team_report,
        use_container_width=True,
        hide_index=True
    )

    # ==========================================
    # STATUS SUMMARY
    # ==========================================

    st.markdown(
        "### Status Summary"
    )

    status_report = (
        filtered_df
        .groupby(
            "status",
            as_index=False
        )
        .size()
    )

    st.dataframe(
        status_report,
        use_container_width=True,
        hide_index=True
    )

    # ==========================================
    # WORK PACKAGE REPORT
    # ==========================================

    st.markdown(
        "### Work Package Report"
    )

    display_cols = [

        "project",

        "team",

        "day_range",

        "chainage",

        "mapping_id",

        "fixture_old",

        "fixture_new",

        "target_qty",

        "dismantled_qty",

        "installed_qty",

        "pending_dismantle",

        "pending_installation",

        "status"

    ]

    st.dataframe(
        filtered_df[
            display_cols
        ],
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # ==========================================
    # EXPORT CSV
    # ==========================================

    csv_data = (
        filtered_df
        .to_csv(index=False)
    )

    st.download_button(
        label="Download Report CSV",
        data=csv_data,
        file_name="led_retrofit_report.csv",
        mime="text/csv"
    )