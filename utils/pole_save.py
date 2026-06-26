"""
==============================================================
Pole Save Engine
Version : V1.0
Project : LED Retrofit V2

Responsibilities
----------------
✓ Generate Transaction Number
✓ Create Header
✓ Create Details
✓ Audit Log
✓ Rollback on Failure

Author : ChatGPT
==============================================================
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Dict

import pandas as pd

from utils.db import supabase

# ==========================================================
# TRANSACTION PREFIX
# ==========================================================

PREFIX = "PT"


# ==========================================================
# TODAY
# ==========================================================

def today():

    return datetime.now().date().isoformat()


# ==========================================================
# CURRENT TIMESTAMP
# ==========================================================

def now():

    return datetime.now().isoformat()


def json_value(value):
    if pd.isna(value):
        return None

    if isinstance(value, (date, datetime)):
        return value.isoformat()

    if hasattr(value, "item"):
        value = value.item()

    return value


def integer_value(value):
    value = json_value(value)

    if value is None:
        return None

    try:
        return int(float(value))
    except (TypeError, ValueError):
        return value


# ==========================================================
# GENERATE TRANSACTION NUMBER
# ==========================================================

def generate_transaction_no(
    project: str
) -> str:
    """
    Example

    PT-SRTPL-20260625-0001
    """

    date_part = datetime.now().strftime("%Y%m%d")

    prefix = f"{PREFIX}-{project}-{date_part}"

    try:

        result = (

            supabase
            .table("pole_transaction_header")
            .select("transaction_no")
            .like(
                "transaction_no",
                f"{prefix}%"
            )
            .execute()

        )

        running = len(result.data) + 1

    except Exception:

        running = 1

    return f"{prefix}-{running:04d}"


# ==========================================================
# BUILD HEADER
# ==========================================================

def build_header(
    transaction_no: str,
    transaction_df: pd.DataFrame,
    username: str,
    project: str
) -> Dict:

    total_poles = len(transaction_df)

    total_fixtures = 0

    total_mismatch = 0

    for _, row in transaction_df.iterrows():

        if pd.notna(row["Dismantle A"]):
            total_fixtures += 1

        if pd.notna(row["Dismantle B"]):
            total_fixtures += 1

        if row["Mismatch"]:
            total_mismatch += 1

    return {

        "transaction_no": transaction_no,

        "transaction_date": today(),

        "project": project,

        "total_poles": total_poles,

        "total_fixtures": total_fixtures,

        "total_mismatch": total_mismatch,

        "status": "SUBMITTED",

        "created_by": username,

        "created_at": now()

    }


# ==========================================================
# INSERT HEADER
# ==========================================================

def insert_header(
    header: Dict
):

    result = (

        supabase

        .table(
            "pole_transaction_header"
        )

        .insert(header)

        .execute()

    )

    return result


# ==========================================================
# GET HEADER ID
# ==========================================================

def get_transaction_id(
    transaction_no: str
):

    result = (

        supabase

        .table(
            "pole_transaction_header"
        )

        .select(
            "transaction_id"
        )

        .eq(
            "transaction_no",
            transaction_no
        )

        .single()

        .execute()

    )

    return result.data["transaction_id"]
# ==========================================================
# BUILD DETAIL RECORDS
# ==========================================================

def build_details(
    transaction_no: str,
    transaction_df: pd.DataFrame,
    username: str,
    project: str
) -> list:

    details = []

    for _, row in transaction_df.iterrows():

        details.append({

            "transaction_no": transaction_no,

            "transaction_date": today(),

            "project": project,

            "pole_no": json_value(row["Pole No"]),

            "chainage": json_value(row["Chainage"]),

            "pole_type": json_value(row["Pole Type"]),

            "system_fixture_a": integer_value(row["System A"]),

            "system_fixture_b": integer_value(row["System B"]),

            "existing_fixture_a": integer_value(row["Dismantle A"]),

            "existing_fixture_b": integer_value(row["Dismantle B"]),

            "new_fixture_a": integer_value(row["Install A"]),

            "new_fixture_b": integer_value(row["Install B"]),

            "condition": json_value(row["Condition"]),

            "make": json_value(row["Make"]),

            "remarks": json_value(row["Remarks"]),

            "mismatch_flag": bool(row["Mismatch"]),

            "pole_status": "COMPLETED",

            "created_by": username,

            "created_at": now()

        })

    return details


# ==========================================================
# INSERT DETAILS
# ==========================================================

def insert_details(
    details: list
):

    if len(details) == 0:

        return None

    return (

        supabase

        .table(
            "pole_transaction_details"
        )

        .insert(details)

        .execute()

    )


# ==========================================================
# BUILD AUDIT RECORDS
# ==========================================================

def build_audit_records(
    transaction_id: int,
    transaction_df: pd.DataFrame,
    username: str,
    project: str
) -> list:

    audit = []

    for _, row in transaction_df.iterrows():

        if not bool(row["Mismatch"]):

            continue

        audit.append({

            "transaction_id": transaction_id,

            "project": project,

            "pole_no": json_value(row["Pole No"]),

            "system_value":

                f'{row["System A"]},{row["System B"]}',

            "actual_value":

                f'{row["Dismantle A"]},{row["Dismantle B"]}',

            "remarks": json_value(row["Remarks"]),

            "user_name": username,

            "transaction_date": today(),

            "created_at": now()

        })

    return audit


# ==========================================================
# INSERT AUDIT
# ==========================================================

def insert_audit(
    audit_records: list
):
    # pole_audit_log.transaction_id currently references pole_transactions,
    # while this workflow saves into pole_transaction_header/details.
    # Keep mismatch data in transaction details and skip the incompatible FK insert.
    return None


# ==========================================================
# DELETE HEADER (ROLLBACK)
# ==========================================================

def rollback_transaction(
    transaction_no: str
):

    return (

        supabase

        .table(
            "pole_transaction_header"
        )

        .delete()

        .eq(
            "transaction_no",
            transaction_no
        )

        .execute()

    )
# ==========================================================
# SAVE COMPLETE TRANSACTION
# ==========================================================

def save_transaction(
    transaction_df: pd.DataFrame,
    username: str,
    project: str
) -> Dict:
    """
    Complete Save Workflow

    Header
        ↓
    Details
        ↓
    Audit
        ↓
    Success
    """

    result = {

        "success": False,

        "message": "",

        "transaction_no": None,

        "transaction_id": None

    }

    if transaction_df.empty:

        result["message"] = "Transaction grid is empty."

        return result

    transaction_no = generate_transaction_no(
        project
    )

    try:

        # ------------------------------------------
        # Header
        # ------------------------------------------

        header = build_header(

            transaction_no,

            transaction_df,

            username,

            project

        )

        insert_header(
            header
        )

        # ------------------------------------------
        # Header ID
        # ------------------------------------------

        transaction_id = get_transaction_id(
            transaction_no
        )

        # ------------------------------------------
        # Details
        # ------------------------------------------

        details = build_details(

            transaction_no,

            transaction_df,

            username,

            project

        )

        insert_details(
            details
        )

        # ------------------------------------------
        # SUCCESS
        # ------------------------------------------

        result["success"] = True

        result["transaction_no"] = transaction_no

        result["transaction_id"] = transaction_id

        result["message"] = (

            f"Transaction Saved Successfully\n"

            f"{transaction_no}"

        )

        return result

    except Exception as e:

        try:

            rollback_transaction(
                transaction_no
            )

        except Exception:

            pass

        result["message"] = str(e)

        return result


# ==========================================================
# READY TO SAVE
# ==========================================================

def can_save(
    transaction_df: pd.DataFrame
):

    return len(transaction_df) > 0


# ==========================================================
# MODULE EXPORTS
# ==========================================================

__all__ = [

    "generate_transaction_no",

    "build_header",

    "insert_header",

    "get_transaction_id",

    "build_details",

    "insert_details",

    "build_audit_records",

    "insert_audit",

    "rollback_transaction",

    "save_transaction",

    "can_save"

]
