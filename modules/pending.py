import streamlit as st
import pandas as pd

from utils.db import supabase


# =====================================================
# LOAD DATA
# =====================================================

def load_pending_data():

    result = (
        supabase
        .table("vw_work_progress")
        .select("*")
        .neq("status", "COMPLETED")
        .execute()
    )

    df = pd.DataFrame(result.data)

    if df.empty:
        return pd.DataFrame()

    df["chainage_from"] = pd.to_numeric(
        df["chainage_from"],
        errors="coerce"
    )

    df["chainage_to"] = pd.to_numeric(
        df["chainage_to"],
        errors="coerce"
    )

    return df


# =====================================================
# MAIN SCREEN
# =====================================================

def show_pending_matrix():

    st.subheader(
        "Pending Work Matrix"
    )

    df = load_pending_data()

    if df.empty:

        st.success(
            "No pending work packages found."
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
                .dropna()
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
                .dropna()
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
                .dropna()
                .unique()
                .tolist()
            )
        )

    search_chainage = st.text_input(
        "Search Chainage"
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

    if search_chainage:

        filtered_df = filtered_df[
            filtered_df["chainage"]
            .astype(str)
            .str.contains(
                search_chainage,
                case=False,
                na=False
            )
        ]

    # ==========================================
    # SORTING
    # ==========================================

    filtered_df = (
        filtered_df
        .sort_values(
            by=[
                "project",
                "team",
                "chainage_from",
                "chainage_to"
            ]
        )
        .reset_index(drop=True)
    )

    # ==========================================
    # KPI SUMMARY
    # ==========================================

    st.markdown(
        "### Pending Summary"
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        st.metric(
            "Pending Packages",
            len(filtered_df)
        )

    with c2:

        st.metric(
            "Pending Dismantle",
            int(
                filtered_df[
                    "pending_dismantle"
                ].sum()
            )
        )

    with c3:

        st.metric(
            "Pending Installation",
            int(
                filtered_df[
                    "pending_installation"
                ].sum()
            )
        )

    st.divider()

    # ==========================================
    # MATRIX
    # ==========================================

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
        filtered_df[
            display_cols
        ],
        use_container_width=True,
        hide_index=True
    )

    # ==========================================
    # TOP PENDING
    # ==========================================

    st.markdown(
        "### Top Pending Packages"
    )

    top_pending = (
        filtered_df
        .sort_values(
            by=[
                "pending_installation",
                "pending_dismantle"
            ],
            ascending=False
        )
        .head(20)
    )

    st.dataframe(
        top_pending[
            display_cols
        ],
        use_container_width=True,
        hide_index=True
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
        label="Download Pending Matrix CSV",
        data=csv_data,
        file_name="pending_matrix.csv",
        mime="text/csv"
    )