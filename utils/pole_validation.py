"""
==============================================================
Pole Validation Engine
Version : V1.0
Project : LED Retrofit V2

Responsibilities
----------------
✓ Mandatory Validation
✓ Fixture Mapping Validation
✓ Pole Type Validation
✓ Mismatch Detection
✓ Pre-submit Validation

Database remains final authority.
This module only performs UI pre-validation.
==============================================================
"""

from __future__ import annotations

from typing import Dict, List, Tuple

import pandas as pd

# ==========================================================
# APPROVED RETROFIT MAPPING
# ==========================================================

RETROFIT_MAP = {

    350: 210,

    300: 180,

    250: 180,

    180: 110,

    80: 50

}

# ==========================================================
# VALID CONDITION
# ==========================================================

VALID_CONDITIONS = [

    "Good",

    "Damaged",

    "Missing",

    "Broken Arm",

    "Glass Broken",

    "Bracket Damaged",

    "Other"

]

# ==========================================================
# VALID MAKE
# ==========================================================

VALID_MAKES = [

    "Bajaj",

    "Philips",

    "Havells",

    "Crompton",

    "Wipro",

    "Others"

]

# ==========================================================
# VALIDATE REQUIRED FIELD
# ==========================================================

def validate_required(
    value,
    field_name: str
) -> Tuple[bool, str]:

    if value is None:

        return False, f"{field_name} is required."

    if str(value).strip() == "":

        return False, f"{field_name} is required."

    return True, ""

# ==========================================================
# VALIDATE POLE TYPE
# ==========================================================

def validate_pole_type(
    row: pd.Series
) -> List[str]:

    errors = []

    pole_type = row["Pole Type"]

    if pole_type == "SA":

        if pd.notna(row["Dismantle B"]):

            errors.append(

                f'{row["Pole No"]}: '
                'SA Pole cannot have Arm-B.'

            )

    elif pole_type == "DA":

        if pd.isna(row["Dismantle A"]):

            errors.append(

                f'{row["Pole No"]}: '
                'Arm-A required.'

            )

        if pd.isna(row["Dismantle B"]):

            errors.append(

                f'{row["Pole No"]}: '
                'Arm-B required.'

            )

    else:

        errors.append(

            f'{row["Pole No"]}: '
            'Invalid Pole Type.'

        )

    return errors

# ==========================================================
# VALIDATE CONDITION
# ==========================================================

def validate_condition(
    row: pd.Series
) -> List[str]:

    errors = []

    if row["Condition"] not in VALID_CONDITIONS:

        errors.append(

            f'{row["Pole No"]}: '
            'Invalid Condition.'

        )

    return errors

# ==========================================================
# VALIDATE MAKE
# ==========================================================

def validate_make(
    row: pd.Series
) -> List[str]:

    errors = []

    if row["Make"] not in VALID_MAKES:

        errors.append(

            f'{row["Pole No"]}: '
            'Invalid Make.'

        )

    return errors
# ==========================================================
# VALIDATE FIXTURE MAPPING
# ==========================================================

def validate_fixture_mapping(
    row: pd.Series
) -> List[str]:

    errors = []

    pole = row["Pole No"]

    # ----------------------------
    # ARM-A
    # ----------------------------

    system_a = row["System A"]
    install_a = row["Install A"]

    if pd.notna(system_a):

        expected = RETROFIT_MAP.get(
            int(system_a),
            None
        )

        if install_a != expected:

            errors.append(
                f"{pole}: Invalid Arm-A Mapping "
                f"({system_a} → {install_a})"
            )

    # ----------------------------
    # ARM-B
    # ----------------------------

    system_b = row["System B"]
    install_b = row["Install B"]

    if pd.notna(system_b):

        expected = RETROFIT_MAP.get(
            int(system_b),
            None
        )

        if install_b != expected:

            errors.append(
                f"{pole}: Invalid Arm-B Mapping "
                f"({system_b} → {install_b})"
            )

    return errors


# ==========================================================
# DETECT MISMATCH
# ==========================================================

def detect_mismatch(
    row: pd.Series
) -> bool:

    system_a = row["System A"]
    system_b = row["System B"]

    field_a = row["Dismantle A"]
    field_b = row["Dismantle B"]

    if system_a != field_a:
        return True

    if system_b != field_b:
        return True

    return False


# ==========================================================
# VALIDATE ONE ROW
# ==========================================================

def validate_row(
    row: pd.Series
) -> List[str]:

    errors = []

    errors.extend(
        validate_pole_type(row)
    )

    errors.extend(
        validate_condition(row)
    )

    errors.extend(
        validate_make(row)
    )

    errors.extend(
        validate_fixture_mapping(row)
    )

    return errors


# ==========================================================
# VALIDATE GRID
# ==========================================================

def validate_grid(
    transaction_df: pd.DataFrame
) -> Dict:

    result = {

        "valid": True,

        "errors": [],

        "mismatch_count": 0

    }

    if transaction_df.empty:

        result["valid"] = False

        result["errors"].append(
            "Transaction Grid Empty."
        )

        return result

    mismatch = 0

    for _, row in transaction_df.iterrows():

        row_errors = validate_row(row)

        if row_errors:

            result["valid"] = False

            result["errors"].extend(
                row_errors
            )

        if detect_mismatch(row):

            mismatch += 1

    result["mismatch_count"] = mismatch

    return result
# ==========================================================
# PRE-SUBMIT VALIDATION
# ==========================================================

def validate_before_submit(
    transaction_df: pd.DataFrame
) -> Dict:
    """
    Final UI validation before saving.

    NOTE:
    PostgreSQL remains the final authority.
    """

    result = validate_grid(transaction_df)

    if not result["valid"]:
        return result

    if len(transaction_df) == 0:

        result["valid"] = False

        result["errors"].append(
            "No poles selected."
        )

    return result


# ==========================================================
# VALIDATION SUMMARY
# ==========================================================

def validation_summary(
    validation_result: Dict
) -> str:
    """
    Convert validation result into
    user-friendly text.
    """

    if validation_result["valid"]:

        return (
            "Validation Successful."
        )

    return "\n".join(
        validation_result["errors"]
    )


# ==========================================================
# MARK GRID MISMATCH
# ==========================================================

def apply_mismatch_flag(
    transaction_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Update mismatch column.
    """

    if transaction_df.empty:

        return transaction_df

    df = transaction_df.copy()

    mismatch = []

    for _, row in df.iterrows():

        mismatch.append(
            detect_mismatch(row)
        )

    df["Mismatch"] = mismatch

    return df


# ==========================================================
# EXPORT VALIDATION REPORT
# ==========================================================

def validation_report(
    transaction_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Generate validation report.
    """

    rows = []

    if transaction_df.empty:

        return pd.DataFrame()

    for _, row in transaction_df.iterrows():

        errors = validate_row(row)

        rows.append({

            "Pole No": row["Pole No"],

            "Status":
                "PASS"
                if len(errors) == 0
                else "FAIL",

            "Mismatch":
                detect_mismatch(row),

            "Errors":
                "; ".join(errors)

        })

    return pd.DataFrame(rows)


# ==========================================================
# HELPER
# ==========================================================

def has_errors(
    validation_result: Dict
) -> bool:

    return not validation_result["valid"]


# ==========================================================
# MODULE EXPORTS
# ==========================================================

__all__ = [

    "RETROFIT_MAP",

    "VALID_CONDITIONS",

    "VALID_MAKES",

    "validate_required",

    "validate_pole_type",

    "validate_condition",

    "validate_make",

    "validate_fixture_mapping",

    "detect_mismatch",

    "validate_row",

    "validate_grid",

    "validate_before_submit",

    "validation_summary",

    "apply_mismatch_flag",

    "validation_report",

    "has_errors"

]