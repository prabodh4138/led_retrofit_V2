import streamlit as st
import pandas as pd

from utils.db import supabase


# =====================================================
# RETROFIT MAPPING
# =====================================================

RETROFIT_MAP = {
    350: 210,
    300: 180,
    250: 180,
    180: 110,
    80: 50
}


# =====================================================
# LOAD ORDERED POLES
# =====================================================

def load_ordered_poles():

    response = (
        supabase
        .table("vw_pole_search_ordered")
        .select("*")
        .execute()
    )

    return pd.DataFrame(response.data)


# =====================================================
# BUILD TRANSACTION GRID
# =====================================================

def build_transaction_grid(selected_df):

    rows = []

    for _, row in selected_df.iterrows():

        dismantle_a = row["design_arm1_fixture"]
        dismantle_b = row["design_arm2_fixture"]

        install_a = RETROFIT_MAP.get(
            dismantle_a,
            None
        )

        install_b = RETROFIT_MAP.get(
            dismantle_b,
            None
        )

        rows.append(
            {
                "Edit": False,
                "Pole No": row["pole_no"],
                "Chainage": row["chainage"],
                "Pole Type": row["pole_type"],
                "Dismantle A": dismantle_a,
                "Dismantle B": dismantle_b,
                "Install A": install_a,
                "Install B": install_b,
                "Condition": "Good",
                "Make": "Bajaj",
                "Remarks": ""
            }
        )

    return pd.DataFrame(rows)


# =====================================================
# MAIN PAGE
# =====================================================

def show_pole_transactions():

    st.subheader("Pole Transactions")

    st.markdown("---")

    # =================================================
    # SEARCH SECTION
    # =================================================

    col1, col2, col3 = st.columns(3)

    with col1:

        search_pole = st.text_input(
            "Search Pole Number",
            placeholder="P005"
        )

    with col2:

        search_mode = st.radio(
            "Search Mode",
            [
                "Pole Range",
                "Same Chainage"
            ]
        )

    with col3:

        pole_range = st.number_input(
            "Range",
            min_value=1,
            max_value=20,
            value=10
        )

    fetch_btn = st.button(
        "Fetch Poles",
        use_container_width=True
    )

    # =================================================
    # FETCH POLES
    # =================================================

    if fetch_btn:

        try:

            df = load_ordered_poles()

            if df.empty:

                st.warning(
                    "No poles found."
                )

                st.stop()

            if not search_pole:

                st.warning(
                    "Enter Pole Number."
                )

                st.stop()

            search_pole = (
                search_pole
                .strip()
                .upper()
            )

            selected_row = df[
                df["pole_no"] == search_pole
            ]

            if selected_row.empty:

                st.error(
                    f"{search_pole} not found."
                )

                st.stop()

            # -----------------------------------------
            # POLE RANGE MODE
            # -----------------------------------------

            if search_mode == "Pole Range":

                pole_seq = int(
                    selected_row.iloc[0][
                        "pole_sequence"
                    ]
                )

                filtered_df = df[
                    (
                        df["pole_sequence"]
                        >= pole_seq - pole_range
                    )
                    &
                    (
                        df["pole_sequence"]
                        <= pole_seq + pole_range
                    )
                ]

            # -----------------------------------------
            # SAME CHAINAGE MODE
            # -----------------------------------------

            else:

                chainage = (
                    selected_row.iloc[0][
                        "chainage"
                    ]
                )

                filtered_df = df[
                    df["chainage"]
                    == chainage
                ]

            filtered_df = (
                filtered_df
                .sort_values(
                    by="pole_sequence"
                )
                .reset_index(drop=True)
            )

            st.session_state[
                "pole_bucket"
            ] = filtered_df

        except Exception as e:

            st.error(str(e))

            st.stop()

    # =================================================
    # POLE BUCKET
    # =================================================

    if "pole_bucket" in st.session_state:

        bucket_df = (
            st.session_state[
                "pole_bucket"
            ]
            .copy()
        )

        bucket_df["Select"] = False

        st.markdown("### Pole Bucket")

        edited_bucket = st.data_editor(
            bucket_df[
                [
                    "Select",
                    "pole_no",
                    "chainage",
                    "pole_type",
                    "design_arm1_fixture",
                    "design_arm2_fixture"
                ]
            ],
            hide_index=True,
            use_container_width=True,
            key="pole_bucket_grid"
        )

        selected_df = edited_bucket[
            edited_bucket["Select"] == True
        ]

        # =============================================
        # TRANSACTION GRID
        # =============================================

        if not selected_df.empty:

            st.markdown("---")

            st.markdown(
                "### Transaction Grid"
            )

            transaction_df = (
                build_transaction_grid(
                    selected_df
                )
            )

            st.data_editor(
                transaction_df,
                hide_index=True,
                use_container_width=True,
                key="transaction_grid"
            )

            st.success(
                f"{len(selected_df)} pole(s) selected."
            )