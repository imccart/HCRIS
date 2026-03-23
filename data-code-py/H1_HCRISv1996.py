"""HCRIS v1996 extraction — 1998-2011.

CMS HCRIS using Form 2552-96. Raw CSV files in long format, extracted by
worksheet/line/column codes.
"""

from pathlib import Path
import numpy as np
import pandas as pd


# Variable locations -------------------------------------------------------

HCRIS_VARS = [
    # (name, wksht_cd, line_num, clmn_num, source)
    ("beds",                   "S300001", "01200", "0100", "numeric"),
    ("tot_charges",            "G300000", "00100", "0100", "numeric"),
    ("net_pat_rev",            "G300000", "00300", "0100", "numeric"),
    ("tot_discounts",          "G300000", "00200", "0100", "numeric"),
    ("tot_operating_exp",      "G300000", "00400", "0100", "numeric"),
    ("ip_charges",             "G200000", "00100", "0100", "numeric"),
    ("icu_charges",            "G200000", "01500", "0100", "numeric"),
    ("ancillary_charges",      "G200000", "01700", "0100", "numeric"),
    ("tot_discharges",         "S300001", "00100", "1500", "numeric"),
    ("mcare_discharges",       "S300001", "00100", "1300", "numeric"),
    ("mcaid_discharges",       "S300001", "00100", "1400", "numeric"),
    ("tot_mcare_payment",      "E00A18A", "01600", "0100", "numeric"),
    ("secondary_mcare_payment","E00A18A", "01700", "0100", "numeric"),
    ("street",                 "S200000", "00100", "0100", "alpha"),
    ("city",                   "S200000", "00101", "0100", "alpha"),
    ("state",                  "S200000", "00101", "0200", "alpha"),
    ("zip",                    "S200000", "00101", "0300", "alpha"),
    ("county",                 "S200000", "00101", "0400", "alpha"),
    ("name",                   "S200000", "00200", "0100", "alpha"),
    ("uncomp_care",            "S100000", "03000", "0100", "numeric"),
    ("cost_to_charge",         "S100000", "02400", "0100", "numeric"),
    ("new_cap_ass",            "A700002", "00900", "0200", "numeric"),
    ("cash",                   "G000000", "00100", "0100", "numeric"),
    ("fixed_assets",           "G000000", "02100", "0100", "numeric"),
    ("depr_land",              "G000000", "01301", "0100", "numeric"),
    ("depr_bldg",              "G000000", "01401", "0100", "numeric"),
    ("depr_lease",             "G000000", "01501", "0100", "numeric"),
    ("depr_fixed_equip",       "G000000", "01601", "0100", "numeric"),
    ("depr_auto",              "G000000", "01701", "0100", "numeric"),
    ("depr_major_equip",       "G000000", "01801", "0100", "numeric"),
    ("depr_minor_equip",       "G000000", "01901", "0100", "numeric"),
    ("current_assets",         "G000000", "01100", "0100", "numeric"),
    ("current_liabilities",    "G000000", "03600", "0100", "numeric"),
    ("pps_ip_charges",         "C000001", "10100", "0600", "numeric"),
    ("pps_op_charges",         "C000001", "10100", "0700", "numeric"),
    ("pps_mcare_cost",         "D10A181", "04900", "0100", "numeric"),
    ("pps_pgm_cost",           "D10A181", "05300", "0100", "numeric"),
]

RPT_COLS = [
    "RPT_REC_NUM", "PRVDR_CTRL_TYPE_CD", "PRVDR_NUM", "NPI",
    "RPT_STUS_CD", "FY_BGN_DT", "FY_END_DT", "PROC_DT",
    "INITL_RPT_SW", "LAST_RPT_SW", "TRNSMTL_NUM", "FI_NUM",
    "ADR_VNDR_CD", "FI_CREAT_DT", "UTIL_CD", "NPR_DT",
    "SPEC_IND", "FI_RCPT_DT",
]

LONG_COLS = ["RPT_REC_NUM", "WKSHT_CD", "LINE_NUM", "CLMN_NUM", "ITM_VAL_NUM"]


# Extraction ---------------------------------------------------------------

def extract_v1996():
    print("Extracting HCRIS v1996 (1998-2011)...")
    frames = []
    for yr in range(1998, 2012):
        base = Path(f"data/input/HCRIS_v1996/HospitalFY{yr}")
        alpha = pd.read_csv(base / f"hosp_{yr}_ALPHA.CSV", header=None, names=LONG_COLS, dtype=str)
        nmrc = pd.read_csv(base / f"hosp_{yr}_NMRC.CSV", header=None, names=LONG_COLS, dtype=str)
        rpt = pd.read_csv(base / f"hosp_{yr}_RPT.CSV", header=None, names=RPT_COLS, dtype=str)

        final = rpt[["RPT_REC_NUM", "PRVDR_NUM", "NPI", "FY_BGN_DT", "FY_END_DT",
                      "PROC_DT", "FI_CREAT_DT", "RPT_STUS_CD"]].copy()
        final.columns = ["report", "provider_number", "npi", "fy_start", "fy_end",
                         "date_processed", "date_created", "status"]
        final["year"] = yr
        final["data_source"] = "v1996"

        for var_name, wksht, line, col, source in HCRIS_VARS:
            data = alpha if source == "alpha" else nmrc
            vals = (
                data
                .loc[(data["WKSHT_CD"] == wksht) &
                     (data["LINE_NUM"] == line) &
                     (data["CLMN_NUM"] == col),
                     ["RPT_REC_NUM", "ITM_VAL_NUM"]]
                .rename(columns={"RPT_REC_NUM": "report", "ITM_VAL_NUM": var_name})
            )
            if source == "numeric":
                vals[var_name] = pd.to_numeric(vals[var_name], errors="coerce")
            final = final.merge(vals, on="report", how="left")

        frames.append(final)
        print(f"  v1996 {yr}: {len(final):,} reports")

    combined = pd.concat(frames, ignore_index=True)
    combined.to_csv("data/output/HCRIS_Data_v1996.txt", sep="\t", index=False)
    print(f"  v1996 total: {len(combined):,} rows written")
    return combined


if __name__ == "__main__":
    extract_v1996()
