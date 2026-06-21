import streamlit as st
import pandas as pd
from datetime import date

from utils.db import supabase


# =====================================================
# LOAD ACTIVE PACKAGES
# =====================================================

def load_active_packages():

    result = (
        supabase
        .table("vw_active_work_packages")
        .select("*")
        .execute()
    )

    df = pd.DataFrame(result.data)

    if df.empty:
        return pd.DataFrame()

    df["chainage"] = (
        df["chainage"]
        .astype(str)
        .str.strip()
    )

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
# SAVE ENTRY
# =====================================================

def save_entry(payload):

    return (
        supabase
        .table("entries")
        .insert(payload)
        .execute()
    )


# =====================================================
# ENTRY FORM
# =====================================================

def show_entry_form():

    st.subheader(
        "LED Retrofit Entry Form"
    )

    df = load_active_packages()

    if df.empty:

        st.warning(
            "No active work packages found"
        )

        return

    # ==========================================
    # PROJECT FILTER
    # ==========================================

    role = st.session_state.role
    project = st.session_state.project

    if (
        role == "vendor"
        and project != "ALL"
    ):

        df = df[
            df["project"]
            == project
        ]

    if df.empty:

        st.warning(
            "No work packages available"
        )

        return

    # ==========================================
    # ENTRY DATE
    # ==========================================

    entry_date = st.date_input(
        "Entry Date",
        value=date.today(),
        max_value=date.today()
    )

    # ==========================================
    # WORK TYPE
    # ==========================================

    work_type = st.selectbox(
        "Work Type",
        [
            "Dismantle",
            "Installation"
        ]
    )

    # ==========================================
    # CHAINAGE
    # ==========================================

    chainage_master = (
        df[
            [
                "chainage",
                "chainage_from"
            ]
        ]
        .drop_duplicates()
        .sort_values(
            by="chainage_from"
        )
    )

    chainages = (
        chainage_master["chainage"]
        .tolist()
    )

    selected_chainage = st.selectbox(
        "Chainage",
        chainages
    )

    # ==========================================
    # WORK PACKAGE
    # ==========================================

    chainage_df = (
        df[
            df["chainage"]
            == selected_chainage
        ]
        .copy()
        .sort_values(
            by=[
                "fixture_old",
                "fixture_new",
                "mapping_id"
            ]
        )
        .reset_index(drop=True)
    )

    package_options = []

    for _, row in chainage_df.iterrows():

        package_options.append(
            f"{row['fixture_mapping']} | "
            f"Target:{row['target_qty']} | "
            f"D:{row['dismantled_qty']} | "
            f"I:{row['installed_qty']} | "
            f"{row['day_range']} | "
            f"{row['mapping_id']}"
        )

    selected_package = st.selectbox(
        "Work Package",
        package_options
    )

    selected_index = (
        package_options.index(
            selected_package
        )
    )

    package = (
        chainage_df
        .iloc[selected_index]
    )

    # ==========================================
    # WORK SUMMARY
    # ==========================================

    available_install = max(
        0,
        int(package["dismantled_qty"])
        -
        int(package["installed_qty"])
    )

    st.markdown("### Work Summary")

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Target Qty",
            int(package["target_qty"])
        )

        st.metric(
            "Dismantled",
            int(package["dismantled_qty"])
        )

    with col2:

        st.metric(
            "Installed",
            int(package["installed_qty"])
        )

        st.metric(
            "Pending Dismantle",
            int(package["pending_dismantle"])
        )

    with col3:

        st.metric(
            "Available Install",
            available_install
        )

        st.metric(
            "Pending Install",
            int(package["pending_installation"])
        )

    st.divider()

    # ==========================================
    # ALLOWED QTY
    # ==========================================

    if work_type == "Dismantle":

        allowed_qty = int(
            package["pending_dismantle"]
        )

        fixture = int(
            package["fixture_old"]
        )

    else:

        allowed_qty = available_install

        fixture = int(
            package["fixture_new"]
        )

    st.info(
        f"Maximum Allowed Quantity : {allowed_qty}"
    )

    # ==========================================
    # QUANTITY
    # ==========================================

    quantity = st.number_input(
        "Quantity",
        min_value=1,
        step=1
    )

    # ==========================================
    # REASON
    # ==========================================

    reason = st.selectbox(
        "Reason",
        [
            "Normal Progress",
            "Rain",
            "Manpower Shortage",
            "Traffic Block",
            "Material Delay",
            "Hydra Breakdown",
            "Client Instruction",
            "Other"
        ]
    )

    # ==========================================
    # REMARKS
    # ==========================================

    remarks = st.text_area(
        "Remarks"
    )

    # ==========================================
    # SUBMIT
    # ==========================================

    if st.button(
        "Submit Entry",
        use_container_width=True
    ):

        try:

            if quantity > allowed_qty:

                st.error(
                    f"""
Entered Quantity : {quantity}

Maximum Allowed Quantity : {allowed_qty}

Please reduce the quantity.
"""
                )

                return

            payload = {

                "entry_date":
                str(entry_date),

                "project":
                package["project"],

                "team":
                package["team"],

                "day_range":
                package["day_range"],

                "chainage":
                package["chainage"],

                "work_type":
                work_type,

                "fixture":
                fixture,

                "quantity":
                int(quantity),

                "status":
                "Submitted",

                "reason":
                reason,

                "remarks":
                remarks,

                "mapping_id":
                package["mapping_id"],

                "created_by":
                st.session_state.user_id,

                "created_username":
                st.session_state.username

            }

            save_entry(payload)

            st.success(
                "Entry Saved Successfully"
            )

            st.rerun()

        except Exception as e:

            error_text = str(e)

            if "completed" in error_text.lower():

                st.error(
                    "This work package is already completed."
                )

            elif "future date" in error_text.lower():

                st.error(
                    "Future dates are not allowed."
                )

            else:

                st.error(
                    "Unable to save entry. Please contact administrator."
                )