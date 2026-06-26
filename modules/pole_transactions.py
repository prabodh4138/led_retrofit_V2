"""
=========================================================
Pole Transactions
Version : V1.0

Search Screen
Pole Bucket
Transaction Grid
=========================================================
"""

import pandas as pd
import streamlit as st

from utils.pole_engine import (
    build_transaction,
    refresh_transaction,
    search_poles,
    validate_transaction,
)
from utils.pole_save import save_transaction


CONDITION_OPTIONS = [
    "Good",
    "Damaged",
    "Missing",
    "Broken Arm",
    "Glass Broken",
    "Bracket Damaged",
    "Other",
]

MAKE_OPTIONS = [
    "Bajaj",
    "Philips",
    "Havells",
    "Crompton",
    "Wipro",
    "Others",
]

FIELD_EDIT_COLUMNS = [
    "Dismantle A",
    "Dismantle B",
    "Condition",
    "Make",
    "Remarks",
]

READ_ONLY_TRANSACTION_COLUMNS = [
    "Pole No",
    "Chainage",
    "Pole Type",
    "System A",
    "System B",
    "Install A",
    "Install B",
    "Mismatch",
]

PROJECT_OPTIONS = [
    "SRTPL",
    "DTPL",
    "TEL",
]


# =====================================================
# SESSION
# =====================================================

def _initialize_pole_session() -> None:
    if "bucket_df" not in st.session_state:
        st.session_state["bucket_df"] = pd.DataFrame()

    if "transaction_df" not in st.session_state:
        st.session_state["transaction_df"] = pd.DataFrame()

    if "summary" not in st.session_state:
        st.session_state["summary"] = {}

    if "validation" not in st.session_state:
        st.session_state["validation"] = {}

    if "search_result" not in st.session_state:
        st.session_state["search_result"] = {}

    if "bucket_editor_version" not in st.session_state:
        st.session_state["bucket_editor_version"] = 0

    if "transaction_editor_version" not in st.session_state:
        st.session_state["transaction_editor_version"] = 0

    if "active_pole_project" not in st.session_state:
        st.session_state["active_pole_project"] = ""


def _state(key: str, default):
    if key not in st.session_state:
        st.session_state[key] = default

    return st.session_state[key]


def _bump_counter(key: str) -> None:
    current_value = _state(key, 0)
    st.session_state[key] = int(current_value or 0) + 1


def _empty_pole_state(clear_bucket: bool = True) -> None:
    _initialize_pole_session()

    if clear_bucket:
        st.session_state["bucket_df"] = pd.DataFrame()
        st.session_state["search_result"] = {}
        _bump_counter("bucket_editor_version")

    st.session_state["transaction_df"] = pd.DataFrame()
    st.session_state["summary"] = {}
    st.session_state["validation"] = {}
    _bump_counter("transaction_editor_version")


# =====================================================
# HELPERS
# =====================================================

def _is_empty_df(value) -> bool:
    return not isinstance(value, pd.DataFrame) or value.empty


def _show_summary(summary: dict) -> None:
    if not summary:
        return

    st.divider()
    st.subheader("Transaction Summary")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Selected Poles", summary.get("selected_poles", 0))
        st.metric("SA Poles", summary.get("sa_poles", 0))

    with col2:
        st.metric("DA Poles", summary.get("da_poles", 0))
        st.metric("Mismatch", summary.get("mismatch", 0))

    with col3:
        st.metric("Dismantled", summary.get("dismantled_fixtures", 0))
        st.metric("Installed", summary.get("installed_fixtures", 0))

    with col4:
        st.metric("Good", summary.get("good", 0))
        st.metric("Damaged", summary.get("damaged", 0))

    with col5:
        st.metric("Bajaj", summary.get("bajaj", 0))
        st.metric("Others", summary.get("others_make", 0))


def _apply_edit_flags(
    edited_df: pd.DataFrame,
    previous_df: pd.DataFrame,
) -> pd.DataFrame:
    if edited_df.empty or previous_df.empty:
        return edited_df

    if "Edit" not in edited_df.columns:
        return edited_df

    if "Pole No" not in edited_df.columns:
        return edited_df

    previous_by_pole = previous_df.set_index("Pole No")
    updated_df = edited_df.copy()

    for index, row in updated_df.iterrows():
        if bool(row.get("Edit", False)):
            continue

        pole_no = row.get("Pole No")

        if pole_no not in previous_by_pole.index:
            continue

        for column in FIELD_EDIT_COLUMNS:
            if column in updated_df.columns and column in previous_by_pole.columns:
                updated_df.at[index, column] = previous_by_pole.at[pole_no, column]

    return updated_df


def _bucket_editor_key() -> str:
    version = _state("bucket_editor_version", 0)
    return f"bucket_editor_{version}"


def _transaction_editor_key() -> str:
    version = _state("transaction_editor_version", 0)
    return f"transaction_editor_{version}"


# =====================================================
# MAIN
# =====================================================

def show_pole_transactions():
    _initialize_pole_session()

    st.subheader("Pole Transactions")
    st.divider()

    user_project = str(st.session_state.get("project", "") or "").strip()
    username = st.session_state.get("username", "")

    if not user_project:
        st.warning("Project not found in session.")
        return

    project = user_project.upper()

    if project == "ALL":
        project = st.selectbox(
            "Project",
            PROJECT_OPTIONS,
            key="pole_transaction_project",
        )
    else:
        st.caption(f"Project : {project}")

    if st.session_state["active_pole_project"] != project:
        st.session_state["active_pole_project"] = project
        _empty_pole_state(clear_bucket=True)

    # ---------------------------------------------
    # SEARCH
    # ---------------------------------------------

    c1, c2, c3, c4 = st.columns([2, 2, 1, 1])

    with c1:
        pole_no = st.text_input(
            "Pole Number",
            placeholder="Example : P003",
        ).strip().upper()

    with c2:
        mode = st.selectbox(
            "Search Mode",
            [
                "Pole Range",
                "Same Chainage",
            ],
        )

    with c3:
        before = st.number_input(
            "- Pole",
            min_value=0,
            max_value=50,
            value=10,
            step=1,
        )

    with c4:
        after = st.number_input(
            "+ Pole",
            min_value=0,
            max_value=50,
            value=10,
            step=1,
        )

    if st.button("Search", use_container_width=True):
        if not pole_no:
            _empty_pole_state(clear_bucket=True)
            st.error("Pole Number is required.")
        else:
            result = search_poles(
                project=project,
                pole_no=pole_no,
                mode=mode,
                before=int(before),
                after=int(after),
            )

            if result.get("success", False):
                bucket_df = result.get("bucket_df", pd.DataFrame())

                st.session_state["search_result"] = result
                st.session_state["bucket_df"] = bucket_df
                st.session_state["transaction_df"] = pd.DataFrame()
                st.session_state["summary"] = {}
                st.session_state["validation"] = {}
                st.session_state["bucket_editor_version"] += 1
                st.session_state["transaction_editor_version"] += 1
            else:
                _empty_pole_state(clear_bucket=True)
                st.error(result.get("message", "Search Failed."))

    # ==================================================
    # POLE BUCKET
    # ==================================================

    if not _is_empty_df(st.session_state["bucket_df"]):
        st.markdown("### Pole Bucket")

        bucket_df = st.data_editor(
            st.session_state["bucket_df"],
            hide_index=True,
            use_container_width=True,
            key=_bucket_editor_key(),
            column_config={
                "Select": st.column_config.CheckboxColumn("Select"),
            },
        )

        st.session_state["bucket_df"] = bucket_df

        st.divider()

        if st.button(
            "Build Transaction Grid",
            type="primary",
            use_container_width=True,
        ):
            build_result = build_transaction(bucket_df)

            if build_result.get("success", False):
                transaction_df = build_result.get(
                    "transaction_df",
                    pd.DataFrame(),
                )

                st.session_state["transaction_df"] = transaction_df
                st.session_state["summary"] = build_result.get("summary", {})
                st.session_state["validation"] = {}
                st.session_state["transaction_editor_version"] += 1
            else:
                _empty_pole_state(clear_bucket=False)
                st.error(
                    build_result.get(
                        "message",
                        "Unable to build transaction.",
                    )
                )

    # ==================================================
    # TRANSACTION GRID
    # ==================================================

    if _is_empty_df(st.session_state["transaction_df"]):
        return

    st.markdown("### Transaction Grid")

    previous_transaction_df = st.session_state["transaction_df"].copy()

    edited_transaction_df = st.data_editor(
        previous_transaction_df,
        hide_index=True,
        use_container_width=True,
        key=_transaction_editor_key(),
        disabled=READ_ONLY_TRANSACTION_COLUMNS,
        column_config={
            "Edit": st.column_config.CheckboxColumn("Edit"),
            "Dismantle A": st.column_config.NumberColumn("Dismantle A"),
            "Dismantle B": st.column_config.NumberColumn("Dismantle B"),
            "Condition": st.column_config.SelectboxColumn(
                "Condition",
                options=CONDITION_OPTIONS,
            ),
            "Make": st.column_config.SelectboxColumn(
                "Make",
                options=MAKE_OPTIONS,
            ),
            "Remarks": st.column_config.TextColumn("Remarks"),
        },
    )

    edited_transaction_df = _apply_edit_flags(
        edited_transaction_df,
        previous_transaction_df,
    )

    refresh_result = refresh_transaction(edited_transaction_df)

    if refresh_result.get("success", False):
        refreshed_df = refresh_result.get(
            "transaction_df",
            edited_transaction_df,
        )

        st.session_state["transaction_df"] = refreshed_df
        st.session_state["summary"] = refresh_result.get("summary", {})
        st.session_state["validation"] = refresh_result.get("validation", {})
    else:
        st.session_state["transaction_df"] = edited_transaction_df
        st.warning(
            refresh_result.get(
                "message",
                "Unable to refresh transaction.",
            )
        )

    engine_result = validate_transaction(
        st.session_state["transaction_df"]
    )

    if engine_result.get("success", False):
        validated_df = engine_result.get(
            "transaction_df",
            st.session_state["transaction_df"],
        )

        st.session_state["transaction_df"] = validated_df
        st.session_state["summary"] = engine_result.get("summary", {})
        st.session_state["validation"] = engine_result.get("validation", {})
    else:
        st.session_state["summary"] = engine_result.get(
            "summary",
            st.session_state["summary"],
        )
        st.session_state["validation"] = engine_result.get("validation", {})

    _show_summary(st.session_state["summary"])

    # ==================================================
    # VALIDATION RESULT
    # ==================================================

    st.divider()

    if engine_result.get("success", False):
        st.success(
            engine_result.get(
                "message",
                "Validation Successful.",
            )
        )
    else:
        st.error(
            engine_result.get(
                "message",
                "Validation Failed.",
            )
        )

    # ==================================================
    # SAVE
    # ==================================================

    st.divider()

    save_disabled = not engine_result.get("success", False)

    if st.button(
        "Save Transaction",
        type="primary",
        disabled=save_disabled,
        use_container_width=True,
    ):
        with st.spinner("Saving..."):
            save_result = save_transaction(
                transaction_df=st.session_state["transaction_df"],
                username=username,
                project=project,
            )

        if save_result.get("success", False):
            st.success(
                f"""
Transaction Saved Successfully

Transaction No :
{save_result.get("transaction_no", "")}
"""
            )
            st.balloons()
            _empty_pole_state(clear_bucket=True)
        else:
            st.error(save_result.get("message", "Save failed."))


# ==========================================================
# MODULE COMPLETE
# ==========================================================

__all__ = [
    "show_pole_transactions",
]
