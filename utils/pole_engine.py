"""
==============================================================
Pole Engine
Version : V1.0
Project : LED Retrofit V2

Responsibilities
----------------
✓ Load Project Poles
✓ Search Pole Bucket
✓ Build Transaction Grid
✓ Refresh Grid
✓ Call Validation
✓ Call Summary
✓ Return Standard Result Object

No Streamlit UI
No Database Save
No SQL Insert

==============================================================
"""

from __future__ import annotations

from typing import Dict, Optional

import pandas as pd

from utils.pole_search import (
    load_poles,
    search_bucket,
    build_pole_bucket,
    selected_poles,
    build_transaction_grid,
    refresh_transaction_grid,
)

from utils.pole_validation import (
    validate_before_submit,
)

from utils.pole_summary import (
    calculate_summary,
)

# ==========================================================
# STANDARD RESPONSE
# ==========================================================

def result_template() -> Dict:

    return {

        "success": True,

        "message": "",

        "bucket_df": pd.DataFrame(),

        "selected_df": pd.DataFrame(),

        "transaction_df": pd.DataFrame(),

        "summary": {},

        "validation": {}

    }


# ==========================================================
# LOAD PROJECT
# ==========================================================

def load_project(
    project: str
) -> pd.DataFrame:
    """
    Load project poles from vw_pole_search.
    """

    return load_poles(project)


# ==========================================================
# SEARCH POLES
# ==========================================================

def search_poles(
    project: str,
    pole_no: str,
    mode: str,
    before: int = 10,
    after: int = 10
) -> Dict:

    result = result_template()

    df = load_project(project)

    if df.empty:

        result["success"] = False

        result["message"] = "No poles found."

        return result

    bucket = search_bucket(

        df=df,

        pole_no=pole_no,

        mode=mode,

        before=before,

        after=after

    )

    if bucket.empty:

        result["success"] = False

        result["message"] = "Pole not found."

        return result

    result["bucket_df"] = build_pole_bucket(bucket)

    return result


# ==========================================================
# BUILD TRANSACTION
# ==========================================================

def build_transaction(
    bucket_editor_df: pd.DataFrame
) -> Dict:

    result = result_template()

    selected_df = selected_poles(
        bucket_editor_df
    )

    if selected_df.empty:

        result["success"] = False

        result["message"] = "Select at least one pole."

        return result

    transaction_df = build_transaction_grid(
        selected_df
    )

    transaction_df = refresh_transaction_grid(
        transaction_df
    )

    summary = calculate_summary(
        transaction_df
    )

    result["selected_df"] = selected_df

    result["transaction_df"] = transaction_df

    result["summary"] = summary

    return result
# ==========================================================
# REFRESH TRANSACTION
# ==========================================================

def refresh_transaction(
    transaction_df: pd.DataFrame
) -> Dict:
    """
    Refresh transaction grid after user editing.
    """

    result = result_template()

    if transaction_df.empty:

        result["success"] = False
        result["message"] = "Transaction grid is empty."

        return result

    refreshed = refresh_transaction_grid(
        transaction_df
    )

    summary = calculate_summary(
        refreshed
    )

    result["transaction_df"] = refreshed
    result["summary"] = summary

    return result


# ==========================================================
# VALIDATE TRANSACTION
# ==========================================================

def validate_transaction(
    transaction_df: pd.DataFrame
) -> Dict:
    """
    Perform UI validation before save.
    """

    result = result_template()

    if transaction_df.empty:

        result["success"] = False
        result["message"] = "Transaction grid is empty."

        return result

    refreshed = refresh_transaction_grid(
        transaction_df
    )

    validation = validate_before_submit(
        refreshed
    )

    summary = calculate_summary(
        refreshed
    )

    result["transaction_df"] = refreshed
    result["summary"] = summary
    result["validation"] = validation

    if not validation["valid"]:

        result["success"] = False
        result["message"] = "\n".join(
            validation["errors"]
        )

    return result


# ==========================================================
# BUILD FROM SELECTION
# ==========================================================

def build_from_selection(
    bucket_editor_df: pd.DataFrame
) -> Dict:
    """
    Alias for transaction creation.
    """

    return build_transaction(
        bucket_editor_df
    )


# ==========================================================
# GET SUMMARY ONLY
# ==========================================================

def get_summary(
    transaction_df: pd.DataFrame
) -> dict:
    """
    Return only summary object.
    """

    if transaction_df.empty:

        return {}

    refreshed = refresh_transaction_grid(
        transaction_df
    )

    return calculate_summary(
        refreshed
    )


# ==========================================================
# HAS VALIDATION ERRORS
# ==========================================================

def has_errors(
    validation: dict
) -> bool:

    if not validation:

        return False

    return not validation.get(
        "valid",
        True
    )
# ==========================================================
# SEARCH + BUILD
# ==========================================================

def search_and_build(
    project: str,
    pole_no: str,
    mode: str,
    before: int = 10,
    after: int = 10,
    bucket_editor_df: Optional[pd.DataFrame] = None
) -> Dict:
    """
    Complete search and build workflow.
    """

    result = result_template()

    # ------------------------------------------------------
    # SEARCH
    # ------------------------------------------------------

    search_result = search_poles(
        project=project,
        pole_no=pole_no,
        mode=mode,
        before=before,
        after=after
    )

    if not search_result["success"]:
        return search_result

    result["bucket_df"] = search_result["bucket_df"]

    # ------------------------------------------------------
    # BUILD
    # ------------------------------------------------------

    if bucket_editor_df is not None:

        build_result = build_transaction(
            bucket_editor_df
        )

        result.update(build_result)

    return result


# ==========================================================
# PROCESS TRANSACTION
# ==========================================================

def process_transaction(
    transaction_df: pd.DataFrame
) -> Dict:
    """
    Refresh
    ->
    Validate
    ->
    Summary
    """

    result = result_template()

    if transaction_df.empty:

        result["success"] = False

        result["message"] = "No transaction available."

        return result

    # ---------------------------------------------
    # Refresh
    # ---------------------------------------------

    refreshed = refresh_transaction_grid(
        transaction_df
    )

    # ---------------------------------------------
    # Validation
    # ---------------------------------------------

    validation = validate_before_submit(
        refreshed
    )

    # ---------------------------------------------
    # Summary
    # ---------------------------------------------

    summary = calculate_summary(
        refreshed
    )

    result["transaction_df"] = refreshed
    result["summary"] = summary
    result["validation"] = validation

    if validation["valid"]:

        result["success"] = True
        result["message"] = "Validation Successful."

    else:

        result["success"] = False
        result["message"] = "\n".join(
            validation["errors"]
        )

    return result


# ==========================================================
# GET KPI
# ==========================================================

def get_kpi(
    transaction_df: pd.DataFrame
) -> dict:

    if transaction_df.empty:

        return {}

    return calculate_summary(
        refresh_transaction_grid(
            transaction_df
        )
    )


# ==========================================================
# READY TO SAVE ?
# ==========================================================

def ready_to_save(
    transaction_df: pd.DataFrame
) -> bool:

    result = process_transaction(
        transaction_df
    )

    return result["success"]


# ==========================================================
# MODULE EXPORTS
# ==========================================================

__all__ = [

    "load_project",

    "search_poles",

    "build_transaction",

    "build_from_selection",

    "refresh_transaction",

    "validate_transaction",

    "search_and_build",

    "process_transaction",

    "get_summary",

    "get_kpi",

    "ready_to_save"

]