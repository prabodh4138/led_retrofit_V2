import streamlit as st
import pandas as pd
import plotly.express as px

from utils.db import supabase


# =====================================================
# LOAD DATA
# =====================================================

def load_dashboard_summary():

    result = (
        supabase
        .table("vw_dashboard_summary")
        .select("*")
        .execute()
    )

    return pd.DataFrame(result.data)


def load_project_progress():

    result = (
        supabase
        .table("vw_project_progress")
        .select("*")
        .execute()
    )

    return pd.DataFrame(result.data)


def load_team_progress():

    result = (
        supabase
        .table("vw_team_progress")
        .select("*")
        .execute()
    )

    return pd.DataFrame(result.data)


def load_work_progress():

    result = (
        supabase
        .table("vw_work_progress")
        .select("*")
        .execute()
    )

    return pd.DataFrame(result.data)


# =====================================================
# MAIN DASHBOARD
# =====================================================

def show_dashboard():

    st.subheader(
        "LED Retrofit Dashboard"
    )

    role = st.session_state.role
    user_project = st.session_state.project

    # ==========================================
    # LOAD DATA
    # ==========================================

    summary_df = load_dashboard_summary()

    project_df = load_project_progress()

    team_df = load_team_progress()

    work_df = load_work_progress()

    # ==========================================
    # ROLE FILTER
    # ==========================================

    if (
        role == "vendor"
        and user_project != "ALL"
    ):

        work_df = work_df[
            work_df["project"]
            == user_project
        ]

        project_df = project_df[
            project_df["project"]
            == user_project
        ]

    if work_df.empty:

        st.warning(
            "No dashboard data available."
        )

        return

    # ==========================================
    # KPI CALCULATIONS
    # ==========================================

    total_target = int(
        work_df["target_qty"].sum()
    )

    total_dismantled = int(
        work_df["dismantled_qty"].sum()
    )

    total_installed = int(
        work_df["installed_qty"].sum()
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

    completed_packages = int(
        (
            work_df["status"]
            == "COMPLETED"
        ).sum()
    )

    pending_packages = int(
        (
            work_df["status"]
            != "COMPLETED"
        ).sum()
    )

    # ==========================================
    # KPI CARDS
    # ==========================================

    st.markdown(
        "### Overall Progress"
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        st.metric(
            "Total Target",
            f"{total_target:,}"
        )

        st.metric(
            "Total Installed",
            f"{total_installed:,}"
        )

    with c2:

        st.metric(
            "Total Dismantled",
            f"{total_dismantled:,}"
        )

        st.metric(
            "Progress %",
            f"{progress_pct}%"
        )

    with c3:

        st.metric(
            "Completed Packages",
            completed_packages
        )

        st.metric(
            "Pending Packages",
            pending_packages
        )

    st.divider()

    # ==========================================
    # PROJECT PROGRESS
    # ==========================================

    st.markdown(
        "### Project Progress"
    )

    fig_project = px.bar(
        project_df,
        x="project",
        y="installed_qty",
        text="installed_qty",
        title="Installed Quantity by Project"
    )

    fig_project.update_layout(
        height=400
    )

    st.plotly_chart(
        fig_project,
        use_container_width=True
    )

    # ==========================================
    # TEAM PROGRESS
    # ==========================================

    st.markdown(
        "### Team Progress"
    )

    fig_team = px.bar(
        team_df,
        x="team",
        y="installed_qty",
        text="installed_qty",
        title="Installed Quantity by Team"
    )

    fig_team.update_layout(
        height=400
    )

    st.plotly_chart(
        fig_team,
        use_container_width=True
    )

    # ==========================================
    # STATUS DISTRIBUTION
    # ==========================================

    st.markdown(
        "### Status Distribution"
    )

    status_df = (
        work_df["status"]
        .value_counts()
        .reset_index()
    )

    status_df.columns = [
        "status",
        "count"
    ]

    fig_status = px.pie(
        status_df,
        names="status",
        values="count",
        title="Package Status"
    )

    st.plotly_chart(
        fig_status,
        use_container_width=True
    )

    st.divider()

    # ==========================================
    # TOP PENDING WORK
    # ==========================================

    st.markdown(
        "### Pending Work Matrix"
    )

    pending_df = (
        work_df[
            work_df["status"]
            != "COMPLETED"
        ]
        .copy()
    )

    pending_df = (
        pending_df
        .sort_values(
            by=[
                "pending_installation",
                "pending_dismantle"
            ],
            ascending=[
                False,
                False
            ]
        )
    )

    display_cols = [
        "project",
        "team",
        "day_range",
        "chainage",
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
        pending_df[
            display_cols
        ],
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # ==========================================
    # PROJECT SUMMARY
    # ==========================================

    st.markdown(
        "### Project Summary"
    )

    st.dataframe(
        project_df,
        use_container_width=True,
        hide_index=True
    )

    # ==========================================
    # TEAM SUMMARY
    # ==========================================

    st.markdown(
        "### Team Summary"
    )

    st.dataframe(
        team_df,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # ==========================================
    # EXPORT
    # ==========================================

    csv_data = (
        work_df
        .to_csv(index=False)
    )

    st.download_button(
        label="Download Dashboard CSV",
        data=csv_data,
        file_name="dashboard_export.csv",
        mime="text/csv"
    )