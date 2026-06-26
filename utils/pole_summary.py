"""
==========================================================
Pole Summary Engine
Version : V1.0
Project : LED Retrofit V2

Responsibilities
----------------
✓ Selected Pole Count
✓ SA Pole Count
✓ DA Pole Count
✓ Fixture Count
✓ Condition Count
✓ Make Count
✓ Mismatch Count
✓ Summary Card Preparation

Author : ChatGPT
==========================================================
"""

from __future__ import annotations

import pandas as pd

# ==========================================================
# EMPTY SUMMARY
# ==========================================================

def empty_summary() -> dict:

    return {

        "selected_poles": 0,

        "sa_poles": 0,

        "da_poles": 0,

        "dismantled_fixtures": 0,

        "installed_fixtures": 0,

        "good": 0,

        "damaged": 0,

        "missing": 0,

        "broken_arm": 0,

        "glass_broken": 0,

        "bracket_damaged": 0,

        "other_condition": 0,

        "bajaj": 0,

        "philips": 0,

        "havells": 0,

        "crompton": 0,

        "wipro": 0,

        "others_make": 0,

        "mismatch": 0

    }

# ==========================================================
# FIXTURE COUNT
# ==========================================================

def fixture_count(
    transaction_df: pd.DataFrame
):

    dismantled = 0
    installed = 0

    if transaction_df.empty:

        return dismantled, installed

    for _, row in transaction_df.iterrows():

        if pd.notna(row["Dismantle A"]):
            dismantled += 1

        if pd.notna(row["Dismantle B"]):
            dismantled += 1

        if pd.notna(row["Install A"]):
            installed += 1

        if pd.notna(row["Install B"]):
            installed += 1

    return dismantled, installed


def row_fixture_count(
    row: pd.Series
) -> int:

    count = 0

    if pd.notna(row["Dismantle A"]):
        count += 1

    if pd.notna(row["Dismantle B"]):
        count += 1

    return count

# ==========================================================
# CONDITION SUMMARY
# ==========================================================

def condition_summary(
    transaction_df: pd.DataFrame
):

    summary = {

        "Good": 0,

        "Damaged": 0,

        "Missing": 0,

        "Broken Arm": 0,

        "Glass Broken": 0,

        "Bracket Damaged": 0,

        "Other": 0

    }

    if transaction_df.empty:

        return summary

    for _, row in transaction_df.iterrows():

        value = row["Condition"]

        if value in summary:

            summary[value] += row_fixture_count(row)

    return summary

# ==========================================================
# MAKE SUMMARY
# ==========================================================

def make_summary(
    transaction_df: pd.DataFrame
):

    summary = {

        "Bajaj": 0,

        "Philips": 0,

        "Havells": 0,

        "Crompton": 0,

        "Wipro": 0,

        "Others": 0

    }

    if transaction_df.empty:

        return summary

    for _, row in transaction_df.iterrows():

        value = row["Make"]

        if value in summary:

            summary[value] += row_fixture_count(row)

    return summary
# ==========================================================
# COMPLETE SUMMARY
# ==========================================================

def calculate_summary(
    transaction_df: pd.DataFrame
) -> dict:
    """
    Calculate complete transaction summary.
    """

    summary = empty_summary()

    if transaction_df.empty:
        return summary

    # ------------------------------------------------------
    # Pole Count
    # ------------------------------------------------------

    summary["selected_poles"] = len(transaction_df)

    summary["sa_poles"] = int(
        (
            transaction_df["Pole Type"] == "SA"
        ).sum()
    )

    summary["da_poles"] = int(
        (
            transaction_df["Pole Type"] == "DA"
        ).sum()
    )

    # ------------------------------------------------------
    # Fixture Count
    # ------------------------------------------------------

    dismantled, installed = fixture_count(
        transaction_df
    )

    summary["dismantled_fixtures"] = dismantled
    summary["installed_fixtures"] = installed

    # ------------------------------------------------------
    # Condition
    # ------------------------------------------------------

    cond = condition_summary(
        transaction_df
    )

    summary["good"] = cond["Good"]
    summary["damaged"] = cond["Damaged"]
    summary["missing"] = cond["Missing"]
    summary["broken_arm"] = cond["Broken Arm"]
    summary["glass_broken"] = cond["Glass Broken"]
    summary["bracket_damaged"] = cond["Bracket Damaged"]
    summary["other_condition"] = cond["Other"]

    # ------------------------------------------------------
    # Make
    # ------------------------------------------------------

    make = make_summary(
        transaction_df
    )

    summary["bajaj"] = make["Bajaj"]
    summary["philips"] = make["Philips"]
    summary["havells"] = make["Havells"]
    summary["crompton"] = make["Crompton"]
    summary["wipro"] = make["Wipro"]
    summary["others_make"] = make["Others"]

    # ------------------------------------------------------
    # Mismatch
    # ------------------------------------------------------

    if "Mismatch" in transaction_df.columns:

        summary["mismatch"] = int(
            transaction_df["Mismatch"].sum()
        )

    return summary


# ==========================================================
# KPI DATA
# ==========================================================

def summary_cards(
    summary: dict
):
    """
    Returns KPI cards in display order.
    """

    return [

        ("Selected Poles", summary["selected_poles"]),

        ("SA Poles", summary["sa_poles"]),

        ("DA Poles", summary["da_poles"]),

        ("Dismantled Fixtures",
         summary["dismantled_fixtures"]),

        ("Installed Fixtures",
         summary["installed_fixtures"]),

        ("Good",
         summary["good"]),

        ("Damaged",
         summary["damaged"]),

        ("Bajaj",
         summary["bajaj"]),

        ("Others",
         summary["others_make"]),

        ("Mismatch",
         summary["mismatch"])

    ]


# ==========================================================
# MODULE EXPORT
# ==========================================================

__all__ = [

    "empty_summary",

    "fixture_count",

    "row_fixture_count",

    "condition_summary",

    "make_summary",

    "calculate_summary",

    "summary_cards"

]
