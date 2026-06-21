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
        .table("vw_target_summary")
        .select("*")
        .execute()
    )

    if result.data:
        return result.data[0]

    return None


# =====================================================
# LOAD TARGET MASTER
# =====================================================

def load_targets():

    result = (
        supabase
        .table("vw_target_master")
        .select("*")
        .execute()
    )

    return pd.DataFrame(result.data)


# =====================================================
# MAIN SCREEN
# =====================================================

def show_target_master():

    require_login()

    role = st.session_state.role

    if role not in ["admin", "super_admin"]:

        st.error(
            "Access Denied"
        )

        return

    st.subheader(
        "Target Master"
    )

    # ==========================================
    # KPI DASHBOARD
    # ==========================================

    summary = load_summary()

    if summary:

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:

            st.metric(
                "Packages",
                summary["total_packages"]
            )

        with col2:

            st.metric(
                "Target Qty",
                summary["total_target"]
            )

        with col3:

            st.metric(
                "Projects",
                summary["total_projects"]
            )

        with col4:

            st.metric(
                "Teams",
                summary["total_teams"]
            )

        with col5:

            st.metric(
                "Mappings",
                summary["total_mappings"]
            )

    st.divider()

    # ==========================================
    # LOAD DATA
    # ==========================================

    df = load_targets()

    if df.empty:

        st.warning(
            "No Target Data Found"
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

        fixture_filter = st.selectbox(
            "Fixture Mapping",
            ["All"]
            +
            sorted(
                df["fixture_mapping"]
                .dropna()
                .unique()
                .tolist()
            )
        )

    search_mapping = st.text_input(
        "Search Mapping ID"
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

    if fixture_filter != "All":

        filtered_df = filtered_df[
            filtered_df["fixture_mapping"]
            == fixture_filter
        ]

    if search_mapping:

        filtered_df = filtered_df[
            filtered_df["mapping_id"]
            .astype(str)
            .str.contains(
                search_mapping,
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
                "mapping_id"
            ]
        )
        .reset_index(drop=True)
    )

    # ==========================================
    # SUMMARY
    # ==========================================

    st.markdown(
        "### Filtered Summary"
    )

    s1, s2 = st.columns(2)

    with s1:

        st.metric(
            "Packages",
            len(filtered_df)
        )

    with s2:

        st.metric(
            "Target Qty",
            int(
                filtered_df[
                    "target_qty"
                ].sum()
            )
        )

    st.divider()

    # ==========================================
    # GRID
    # ==========================================

    st.markdown(
        "### Target Grid"
    )

    display_cols = [

        "project",

        "team",

        "day_range",

        "chainage",

        "fixture_mapping",

        "target_qty",

        "mapping_id"

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
    # CSV EXPORT
    # ==========================================

    csv_data = (
        filtered_df
        .to_csv(index=False)
    )

    st.download_button(
        label="Download Target Master CSV",
        data=csv_data,
        file_name="target_master.csv",
        mime="text/csv"
    )

    # ==========================================
    # PHASE STATUS
    # ==========================================

    if role == "super_admin":

        st.info(
            """
Phase-2 Features Coming Next

• Add Target
• Edit Target
• Delete Target
• Excel Upload
• Bulk Validation
"""
        )