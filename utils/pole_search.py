"""
===========================================================
Pole Search Engine
Version : V1.0
Project : LED Retrofit V2
Author  : ChatGPT

Responsibilities
----------------
✓ Load Pole Master
✓ Pole Search
✓ Pole Range Search
✓ Same Chainage Search
✓ Retrofit Mapping
✓ Build Pole Bucket
✓ Build Transaction Grid

NOTE
----
No Validation
No Save Logic
No Dashboard Logic
===========================================================
"""

from __future__ import annotations

import re
from typing import Optional

import pandas as pd
import streamlit as st

from utils.db import supabase

# ===========================================================
# RETROFIT MAPPING
# ===========================================================

RETROFIT_MAP = {
    350: 210,
    300: 180,
    250: 180,
    180: 110,
    80: 50
}


# ===========================================================
# LOAD POLE MASTER
# ===========================================================

@st.cache_data(ttl=30)

def load_poles(project: str) -> pd.DataFrame:
    """
    Load poles from vw_pole_search
    """

    try:

        response = (
            supabase
            .table("vw_pole_search")
            .select("*")
            .eq("project", project)
            .order("pole_sequence")
            .execute()
        )

        if not response.data:

            return pd.DataFrame()

        df = pd.DataFrame(response.data)

        if "pole_sequence" not in df.columns:

            df["pole_sequence"] = range(
                1,
                len(df) + 1
            )

        return df

    except Exception as e:

        st.error(e)

        return pd.DataFrame()


# ===========================================================
# EXTRACT POLE NUMBER
# Example
# P005 -> 5
# ===========================================================

def pole_number(pole_no: str) -> int:

    if not pole_no:

        return 0

    m = re.search(r"(\d+)", str(pole_no))

    if m:

        return int(
            m.group(1)
        )

    return 0


# ===========================================================
# RETROFIT MAPPING
# ===========================================================

def retrofit_fixture(
    fixture: Optional[int]
) -> Optional[int]:

    if fixture is None:

        return None

    if pd.isna(fixture):

        return None

    return RETROFIT_MAP.get(
        int(fixture),
        None
    )


# ===========================================================
# FIND POLE
# ===========================================================

def find_pole(
    df: pd.DataFrame,
    pole_no: str
):

    if df.empty:

        return None

    result = df[
        df["pole_no"] == pole_no
    ]

    if result.empty:

        return None

    return result.iloc[0]


# ===========================================================
# SAME CHAINAGE SEARCH
# ===========================================================

def same_chainage_bucket(
    df: pd.DataFrame,
    pole_no: str
) -> pd.DataFrame:

    pole = find_pole(
        df,
        pole_no
    )

    if pole is None:

        return pd.DataFrame()

    chainage = pole["chainage"]

    bucket = df[
        df["chainage"] == chainage
    ]

    return (
        bucket
        .sort_values(
            "pole_sequence"
        )
        .reset_index(drop=True)
    )
# ===========================================================
# POLE RANGE SEARCH
# ===========================================================

def pole_range_bucket(
    df: pd.DataFrame,
    pole_no: str,
    before: int = 10,
    after: int = 10
) -> pd.DataFrame:
    """
    Return +/- pole range from selected pole.
    """

    if df.empty:
        return pd.DataFrame()

    pole = find_pole(df, pole_no)

    if pole is None:
        return pd.DataFrame()

    seq = int(pole["pole_sequence"])

    bucket = df[
        (df["pole_sequence"] >= seq - before)
        &
        (df["pole_sequence"] <= seq + after)
    ]

    bucket = (
        bucket
        .sort_values("pole_sequence")
        .reset_index(drop=True)
    )

    return bucket


# ===========================================================
# SEARCH DISPATCHER
# ===========================================================

def search_bucket(
    df: pd.DataFrame,
    pole_no: str,
    mode: str = "Pole Range",
    before: int = 10,
    after: int = 10
) -> pd.DataFrame:
    """
    mode:
        Pole Range
        Same Chainage
    """

    if df.empty:
        return pd.DataFrame()

    if not pole_no:
        return pd.DataFrame()

    mode = mode.strip().lower()

    if mode == "same chainage":
        return same_chainage_bucket(
            df,
            pole_no
        )

    return pole_range_bucket(
        df,
        pole_no,
        before,
        after
    )


# ===========================================================
# BUILD POLE BUCKET
# ===========================================================

def build_pole_bucket(
    bucket_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Create selectable Pole Bucket for UI.
    """

    if bucket_df.empty:
        return pd.DataFrame()

    bucket = bucket_df.copy()

    bucket.insert(
        0,
        "Select",
        False
    )

    columns = [

        "Select",

        "pole_no",

        "chainage",

        "pole_type",

        "design_arm1_fixture",

        "design_arm2_fixture"

    ]

    bucket = bucket[columns]

    bucket.rename(
        columns={

            "pole_no": "Pole No",

            "chainage": "Chainage",

            "pole_type": "Pole Type",

            "design_arm1_fixture": "Arm-1",

            "design_arm2_fixture": "Arm-2"

        },
        inplace=True
    )

    return bucket.reset_index(drop=True)


# ===========================================================
# GET SELECTED POLES
# ===========================================================

def selected_poles(
    edited_bucket: pd.DataFrame
) -> pd.DataFrame:
    """
    Return only selected poles from bucket.
    """

    if edited_bucket.empty:
        return pd.DataFrame()

    if "Select" not in edited_bucket.columns:
        return pd.DataFrame()

    selected = edited_bucket[
        edited_bucket["Select"] == True
    ].copy()

    if selected.empty:
        return pd.DataFrame()

    selected.rename(
        columns={

            "Pole No": "pole_no",

            "Chainage": "chainage",

            "Pole Type": "pole_type",

            "Arm-1": "design_arm1_fixture",

            "Arm-2": "design_arm2_fixture"

        },
        inplace=True
    )

    return selected.reset_index(drop=True)
# ===========================================================
# BUILD TRANSACTION GRID
# ===========================================================

def build_transaction_grid(
    selected_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Convert selected poles into editable transaction grid.
    """

    if selected_df.empty:
        return pd.DataFrame()

    rows = []

    for _, row in selected_df.iterrows():

        system_a = row.get("design_arm1_fixture")
        system_b = row.get("design_arm2_fixture")

        new_a = retrofit_fixture(system_a)
        new_b = retrofit_fixture(system_b)

        rows.append({

            # ---------------------------------------
            # UI
            # ---------------------------------------

            "Edit": False,

            # ---------------------------------------
            # Pole Information
            # ---------------------------------------

            "Pole No": row["pole_no"],

            "Chainage": row["chainage"],

            "Pole Type": row["pole_type"],

            # ---------------------------------------
            # Hidden System Values
            # ---------------------------------------

            "System A": system_a,

            "System B": system_b,

            # ---------------------------------------
            # Field Values
            # ---------------------------------------

            "System A": system_a,
            "System B": system_b,

            "Dismantle A": False,
            "Install A": False,

            "Dismantle B": False,
            "Install B": False,

            # ---------------------------------------
            # Inspection
            # ---------------------------------------

            "Condition": "Good",

            "Make": "Bajaj",

            "Remarks": "",

            # ---------------------------------------
            # Status
            # ---------------------------------------

            "Mismatch": False

        })

    transaction_df = pd.DataFrame(rows)

    return transaction_df


# ===========================================================
# FIXTURE COUNT
# ===========================================================

def calculate_fixture_count(
    transaction_df: pd.DataFrame
) -> dict:
    """
    Calculate dismantled and installed fixtures.
    """

    if transaction_df.empty:

        return {

            "total_poles": 0,

            "sa_poles": 0,

            "da_poles": 0,

            "dismantled": 0,

            "installed": 0

        }

    total_poles = len(transaction_df)

    sa = (
        transaction_df["Pole Type"] == "SA"
    ).sum()

    da = (
        transaction_df["Pole Type"] == "DA"
    ).sum()

    dismantled = 0
    installed = 0

    for _, row in transaction_df.iterrows():

        if pd.notna(row["Dismantle A"]):
            dismantled += 1

        if pd.notna(row["Dismantle B"]):
            dismantled += 1

        if pd.notna(row["Install A"]):
            installed += 1

        if pd.notna(row["Install B"]):
            installed += 1

    return {

        "total_poles": total_poles,

        "sa_poles": int(sa),

        "da_poles": int(da),

        "dismantled": dismantled,

        "installed": installed

    }


# ===========================================================
# UPDATE MISMATCH FLAG
# ===========================================================

def update_mismatch(
    transaction_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Compare system fixtures with field dismantled fixtures.
    """

    if transaction_df.empty:
        return transaction_df

    updated = transaction_df.copy()

    mismatch = []

    for _, row in updated.iterrows():

        flag = (
            row["System A"] != row["Dismantle A"]
        ) or (
            row["System B"] != row["Dismantle B"]
        )

        mismatch.append(flag)

    updated["Mismatch"] = mismatch

    return updated
# ===========================================================
# REFRESH GRID
# ===========================================================

def refresh_transaction_grid(
    transaction_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Refresh calculated columns after editing.
    """

    if transaction_df.empty:
        return transaction_df

    df = transaction_df.copy()

    df = update_mismatch(df)

    return df


# ===========================================================
# NORMALIZE GRID
# ===========================================================

def normalize_transaction_grid(
    transaction_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Fill blank values and standardize grid.
    """

    if transaction_df.empty:
        return transaction_df

    df = transaction_df.copy()

    text_columns = [
        "Condition",
        "Make",
        "Remarks"
    ]

    for col in text_columns:

        if col in df.columns:
            df[col] = df[col].fillna("").astype(str)

    fixture_columns = [

        "System A",
        "System B",

        "Dismantle A",
        "Dismantle B",

        "Install A",
        "Install B"

    ]

    for col in fixture_columns:

        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            )

    return df


# ===========================================================
# EXPORT GRID
# ===========================================================

def export_transaction_grid(
    transaction_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Returns export-ready dataframe.
    """

    if transaction_df.empty:
        return pd.DataFrame()

    export_df = transaction_df.copy()

    export_df = export_df.rename(
        columns={
            "Pole No": "pole_no",
            "Chainage": "chainage",
            "Pole Type": "pole_type",
            "System A": "system_fixture_a",
            "System B": "system_fixture_b",
            "Dismantle A": "existing_fixture_a",
            "Dismantle B": "existing_fixture_b",
            "Install A": "new_fixture_a",
            "Install B": "new_fixture_b",
            "Condition": "condition",
            "Make": "make",
            "Remarks": "remarks",
            "Mismatch": "mismatch_flag"
        }
    )

    return export_df


# ===========================================================
# PROJECT FILTER
# ===========================================================

def filter_project(
    df: pd.DataFrame,
    project: str
) -> pd.DataFrame:
    """
    Filter dataframe by project.
    """

    if df.empty:
        return df

    return (
        df[df["project"] == project]
        .reset_index(drop=True)
    )


# ===========================================================
# EMPTY GRID
# ===========================================================

def empty_transaction_grid() -> pd.DataFrame:
    """
    Returns an empty transaction grid with
    all required columns.
    """

    columns = [

        "Edit",

        "Pole No",
        "Chainage",
        "Pole Type",

        "System A",
        "System B",

        "Dismantle A",
        "Dismantle B",

        "Install A",
        "Install B",

        "Condition",
        "Make",
        "Remarks",

        "Mismatch"

    ]

    return pd.DataFrame(columns=columns)


# ===========================================================
# MODULE COMPLETE
# ===========================================================

__all__ = [

    "RETROFIT_MAP",

    "load_poles",

    "pole_number",

    "retrofit_fixture",

    "find_pole",

    "same_chainage_bucket",

    "pole_range_bucket",

    "search_bucket",

    "build_pole_bucket",

    "selected_poles",

    "build_transaction_grid",

    "calculate_fixture_count",

    "update_mismatch",

    "refresh_transaction_grid",

    "normalize_transaction_grid",

    "export_transaction_grid",

    "filter_project",

    "empty_transaction_grid"

]
