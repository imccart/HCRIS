"""HCRIS pipeline orchestrator.

Sources H3 (PPS 1985-1999), H1 (v1996 1998-2011), H2 (v2010 2010-2025),
adds missing variables, deduplicates overlapping reports, and writes the
final combined dataset.
"""

import numpy as np
import pandas as pd

from H3_HCRIS_PPS import extract_pps
from H1_HCRISv1996 import extract_v1996
from H2_HCRISv2010 import extract_v2010


# NA-safe aggregation helpers ----------------------------------------------

def na_sum(x):
    return np.nan if x.isna().all() else x.sum(skipna=True)

def na_max(x):
    return x.iloc[0] if x.isna().all() else x.max(skipna=True)

def na_min(x):
    return x.iloc[0] if x.isna().all() else x.min(skipna=True)


# Depreciation columns ----------------------------------------------------

DEPR_COLS = [
    "depr_land", "depr_bldg", "depr_lease", "depr_fixed_equip",
    "depr_auto", "depr_major_equip", "depr_minor_equip",
]

# depr_HIT only exists in v2010
DEPR_COLS_V2010 = DEPR_COLS + ["depr_HIT"]


def compute_accum_dep(df, depr_cols):
    """Sum absolute values of depreciation columns; all-NA → NA."""
    dep_vals = df[depr_cols].apply(pd.to_numeric, errors="coerce").abs()
    all_na = dep_vals.isna().all(axis=1)
    return dep_vals.sum(axis=1, skipna=True).where(~all_na, other=np.nan)


# Numeric flow/stock columns for aggregation -------------------------------

SUM_COLS = [
    "tot_charges", "tot_discounts", "tot_operating_exp", "ip_charges",
    "icu_charges", "ancillary_charges", "tot_discharges", "mcare_discharges",
    "mcaid_discharges", "tot_mcare_payment", "secondary_mcare_payment",
    "hvbp_payment", "hrrp_payment", "uncomp_care", "tot_uncomp_care_charges",
    "tot_uncomp_care_partial_pmts", "bad_debt", "new_cap_ass",
    "cash", "net_pat_rev", "fixed_assets", "accum_dep",
    "current_assets", "current_liabilities",
    "pps_ip_charges", "pps_op_charges", "pps_mcare_cost", "pps_pgm_cost",
]


def _agg_reports(grp):
    """Aggregate a group of duplicate reports into a single row."""
    row = {
        "beds": na_max(grp["beds"]),
        "fy_start": na_min(grp["fy_start"]),
        "fy_end": na_max(grp["fy_end"]),
        "date_processed": na_max(grp["date_processed"]),
        "date_created": na_min(grp["date_created"]),
        "street": grp["street"].iloc[0],
        "city": grp["city"].iloc[0],
        "state": grp["state"].iloc[0],
        "zip": grp["zip"].iloc[0],
        "county": grp["county"].iloc[0],
        "name": grp["name"].iloc[0],
        "cost_to_charge": grp["cost_to_charge"].iloc[0],
    }
    for c in SUM_COLS:
        row[c] = na_sum(grp[c])
    return pd.Series(row)


# Main pipeline ------------------------------------------------------------

def main():
    # Step 1: Extract from all three sources
    pps = extract_pps()
    v1996 = extract_v1996()
    v2010 = extract_v2010()

    # Step 2: Harmonize columns across sources

    ## PPS: add v2010-only columns, compute accum_dep, drop depr_ columns
    for col in ["hvbp_payment", "hrrp_payment", "tot_uncomp_care_charges",
                "tot_uncomp_care_partial_pmts", "bad_debt"]:
        pps[col] = np.nan
    pps["accum_dep"] = compute_accum_dep(pps, DEPR_COLS)
    pps.drop(columns=DEPR_COLS, inplace=True)

    ## v1996: same treatment
    for col in ["hvbp_payment", "hrrp_payment", "tot_uncomp_care_charges",
                "tot_uncomp_care_partial_pmts", "bad_debt"]:
        v1996[col] = np.nan
    v1996["accum_dep"] = compute_accum_dep(v1996, DEPR_COLS)
    v1996.drop(columns=DEPR_COLS, inplace=True)

    ## v2010: add v1996-only columns, compute uncomp_care and accum_dep
    for col in ["pps_ip_charges", "pps_op_charges", "pps_mcare_cost", "pps_pgm_cost"]:
        v2010[col] = np.nan
    v2010["uncomp_care"] = (
        pd.to_numeric(v2010["tot_uncomp_care_charges"], errors="coerce")
        - pd.to_numeric(v2010["tot_uncomp_care_partial_pmts"], errors="coerce")
        + pd.to_numeric(v2010["bad_debt"], errors="coerce")
    )
    v2010["accum_dep"] = compute_accum_dep(v2010, DEPR_COLS_V2010)
    v2010.drop(columns=DEPR_COLS_V2010, inplace=True, errors="ignore")

    # Step 3: Combine and parse dates
    print("Combining sources and deduplicating...")
    combined = pd.concat([pps, v1996, v2010], ignore_index=True)

    for col in ["fy_start", "fy_end", "date_processed", "date_created"]:
        combined[col] = pd.to_datetime(combined[col], format="mixed", errors="coerce")

    combined["tot_discounts"] = combined["tot_discounts"].abs()
    combined["hrrp_payment"] = combined["hrrp_payment"].abs()

    # Ensure numeric types for aggregation columns
    for c in SUM_COLS + ["beds", "cost_to_charge"]:
        if c in combined.columns:
            combined[c] = pd.to_numeric(combined[c], errors="coerce")

    # Step 4: Source-priority deduplication (v2010 > v1996 > pps)
    priority_map = {"v2010": 3, "v1996": 2, "pps": 1}
    combined["source_priority"] = combined["data_source"].map(priority_map).fillna(0).astype(int)
    combined = (
        combined
        .sort_values(["provider_number", "fy_start", "fy_end",
                       "source_priority", "date_created"],
                      ascending=[True, True, True, False, False])
        .groupby(["provider_number", "fy_start", "fy_end"], dropna=False)
        .first()
        .reset_index()
    )
    combined.drop(columns=["source_priority"], inplace=True)

    # Derive fiscal year from fy_end
    combined["fyear"] = combined["fy_end"].dt.year
    combined.drop(columns=["year"], inplace=True, errors="ignore")
    combined = combined.sort_values(["provider_number", "fyear"]).reset_index(drop=True)

    # Step 5: Count reports per provider/fyear
    combined["total_reports"] = combined.groupby(["provider_number", "fyear"])["provider_number"].transform("count")
    combined["report_number"] = combined.groupby(["provider_number", "fyear"]).cumcount() + 1

    # Step 6: Unique reports (one per provider/fyear)
    unique1 = (
        combined
        .loc[combined["total_reports"] == 1]
        .drop(columns=["report", "total_reports", "report_number", "npi", "status"])
        .assign(source="unique reports")
    )

    # Step 7: Duplicate reports
    dupes = combined.loc[combined["total_reports"] > 1].copy()
    dupes["time_diff"] = (dupes["fy_end"] - dupes["fy_start"]).dt.days

    grp_days = dupes.groupby(["provider_number", "fyear"])["time_diff"].transform("sum")
    dupes["total_days"] = grp_days

    ## 7a: Sum if total days < 370
    short_dupes = dupes.loc[dupes["total_days"] < 370].copy()
    short_dupes["hrrp_payment"] = short_dupes["hrrp_payment"].fillna(0)
    short_dupes["hvbp_payment"] = short_dupes["hvbp_payment"].fillna(0)

    if len(short_dupes) > 0:
        unique2 = (
            short_dupes
            .groupby(["provider_number", "fyear"])
            .apply(_agg_reports, include_groups=False)
            .reset_index()
            .assign(source="total for year")
        )
    else:
        unique2 = pd.DataFrame()

    ## 7b: Pick primary report if one covers full year
    long_dupes = dupes.loc[dupes["total_days"] >= 370].copy()
    long_dupes["max_days"] = long_dupes.groupby(["provider_number", "fyear"])["time_diff"].transform("max")
    long_dupes["max_date"] = long_dupes.groupby(["provider_number", "fyear"])["fy_end"].transform("max")

    primary_mask = (
        (long_dupes["max_days"] == long_dupes["time_diff"]) &
        (long_dupes["time_diff"] > 360) &
        (long_dupes["max_date"] == long_dupes["fy_end"])
    )
    unique3 = (
        long_dupes
        .loc[primary_mask]
        .drop(columns=["report", "total_reports", "report_number", "npi", "status",
                        "max_days", "time_diff", "total_days", "max_date"])
        .assign(source="primary report")
    )

    ## 7c: Weighted average for remainder
    used_keys = set()
    if len(unique3) > 0:
        used_keys = set(zip(unique3["provider_number"], unique3["fyear"]))

    remainder = long_dupes.loc[
        ~long_dupes.apply(lambda r: (r["provider_number"], r["fyear"]) in used_keys, axis=1)
    ].copy()

    if len(remainder) > 0:
        for c in SUM_COLS:
            remainder[c] = remainder[c] * (remainder["time_diff"] / remainder["total_days"])

        remainder["hrrp_payment"] = remainder["hrrp_payment"].fillna(0)
        remainder["hvbp_payment"] = remainder["hvbp_payment"].fillna(0)

        unique4 = (
            remainder
            .groupby(["provider_number", "fyear"])
            .apply(_agg_reports, include_groups=False)
            .reset_index()
            .assign(source="weighted_average")
        )
    else:
        unique4 = pd.DataFrame()

    # Step 8: Combine all tiers
    final = pd.concat([unique1, unique2, unique3, unique4], ignore_index=True)
    final = final.rename(columns={"fyear": "year"}).sort_values(["provider_number", "year"]).reset_index(drop=True)

    # Write output
    final.to_csv("data/output/HCRIS_Data.txt", sep="\t", index=False)
    print(f"Final dataset: {len(final):,} rows, {len(final.columns)} columns")
    print(f"Years: {int(final['year'].min())}-{int(final['year'].max())}")
    return final


if __name__ == "__main__":
    main()
