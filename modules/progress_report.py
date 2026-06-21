import streamlit as st
import pandas as pd
import plotly.express as px

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
# MAIN SCREEN
# =====================================================

def show_progress_report():

    st.subheader(
        "Progress Report"
    )

    df = load_work_progress()

    if df.empty:

        st.warning(
            "No progress data available."
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
    # OVERALL KPI
    # ==========================================

    total_target = int(
        df["target_qty"].sum()
    )

    total_installed = int(
        df["installed_qty"].sum()
    )

    total_dismantled = int(
        df["dismantled_qty"].sum()
    )

    total_balance = (
        total_target
        - total_installed
    )

    overall_progress = round(
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

    st.markdown(
        "### Overall Progress"
    )

    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        st.metric(
            "Target",
            total_target
        )

    with c2:
        st.metric(
            "Installed",
            total_installed
        )

    with c3:
        st.metric(
            "Dismantled",
            total_dismantled
        )

    with c4:
        st.metric(
            "Balance",
            total_balance
        )

    with c5:
        st.metric(
            "Progress %",
            overall_progress
        )

    st.divider()

    # ==========================================
    # PROJECT PROGRESS
    # ==========================================

    project_df = (
        df
        .groupby(
            "project",
            as_index=False
        )
        .agg(
            {
                "target_qty": "sum",
                "installed_qty": "sum"
            }
        )
    )

    project_df["progress_pct"] = round(
        (
            project_df["installed_qty"]
            /
            project_df["target_qty"]
        ) * 100,
        2
    )

    st.markdown(
        "### Project Progress"
    )

    fig_project = px.bar(
        project_df,
        x="project",
        y="progress_pct",
        text="progress_pct"
    )

    st.plotly_chart(
        fig_project,
        use_container_width=True
    )

    # ==========================================
    # TEAM PROGRESS
    # ==========================================

    team_df = (
        df
        .groupby(
            "team",
            as_index=False
        )
        .agg(
            {
                "target_qty": "sum",
                "installed_qty": "sum"
            }
        )
    )

    team_df["progress_pct"] = round(
        (
            team_df["installed_qty"]
            /
            team_df["target_qty"]
        ) * 100,
        2
    )

    st.markdown(
        "### Team Progress"
    )

    fig_team = px.bar(
        team_df,
        x="team",
        y="progress_pct",
        text="progress_pct"
    )

    st.plotly_chart(
        fig_team,
        use_container_width=True
    )

    # ==========================================
    # STATUS DISTRIBUTION
    # ==========================================

    status_df = (
        df["status"]
        .value_counts()
        .reset_index()
    )

    status_df.columns = [
        "status",
        "count"
    ]

    st.markdown(
        "### Status Distribution"
    )

    fig_status = px.pie(
        status_df,
        names="status",
        values="count"
    )

    st.plotly_chart(
        fig_status,
        use_container_width=True
    )

    st.divider()

    # ==========================================
    # PROJECT RANKING
    # ==========================================

    ranking_project = (
        project_df
        .sort_values(
            by="progress_pct",
            ascending=False
        )
        .reset_index(drop=True)
    )

    ranking_project.index += 1

    st.markdown(
        "### Project Ranking"
    )

    st.dataframe(
        ranking_project,
        use_container_width=True
    )

    # ==========================================
    # TEAM RANKING
    # ==========================================

    ranking_team = (
        team_df
        .sort_values(
            by="progress_pct",
            ascending=False
        )
        .reset_index(drop=True)
    )

    ranking_team.index += 1

    st.markdown(
        "### Team Ranking"
    )

    st.dataframe(
        ranking_team,
        use_container_width=True
    )

    st.divider()

    # ==========================================
    # TOP PENDING PACKAGES
    # ==========================================

    st.markdown(
        "### Top Pending Packages"
    )

    pending_df = (
        df
        .sort_values(
            by="pending_installation",
            ascending=False
        )
        .head(20)
    )

    st.dataframe(
        pending_df[
            [
                "project",
                "team",
                "day_range",
                "chainage",
                "target_qty",
                "pending_dismantle",
                "pending_installation",
                "status"
            ]
        ],
        use_container_width=True
    )

    st.divider()

    # ==========================================
    # MANAGEMENT SUMMARY
    # ==========================================

    best_project = (
        ranking_project
        .iloc[0]["project"]
    )

    best_team = (
        ranking_team
        .iloc[0]["team"]
    )

    st.markdown(
        "### Management Summary"
    )

    st.success(
        f"""
Total Target : {total_target}

Installed : {total_installed}

Balance : {total_balance}

Overall Progress : {overall_progress}%

Best Project : {best_project}

Best Team : {best_team}
"""
    )

    # ==========================================
    # EXPORT
    # ==========================================

    csv_data = (
        df
        .to_csv(index=False)
    )

    st.download_button(
        label="Download Progress Report CSV",
        data=csv_data,
        file_name="progress_report.csv",
        mime="text/csv"
    )