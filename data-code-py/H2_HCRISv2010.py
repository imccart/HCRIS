"""HCRIS v2010 extraction — 2010-2025.

CMS HCRIS using Form 2552-10. Raw CSV files in long format, extracted by
worksheet/line/column codes. Handles folder/file naming changes at 2021 and
ZIP archive fallback for recent years.
"""

from pathlib import Path
from zipfile import ZipFile
import io
import numpy as np
import pandas as pd


# Variable locations -------------------------------------------------------

HCRIS_VARS = [
    # (name, wksht_cd, line_num, clmn_num, source)
    ("beds",                       "S300001", "01400", "00200", "numeric"),
    ("tot_charges",                "G300000", "00100", "00100", "numeric"),
    ("tot_discounts",              "G300000", "00200", "00100", "numeric"),
    ("net_pat_rev",                "G300000", "00300", "00100", "numeric"),
    ("tot_operating_exp",          "G300000", "00400", "00100", "numeric"),
    ("ip_charges",                 "G200000", "00100", "00100", "numeric"),
    ("icu_charges",                "G200000", "01600", "00100", "numeric"),
    ("ancillary_charges",          "G200000", "01800", "00100", "numeric"),
    ("tot_discharges",             "S300001", "00100", "01500", "numeric"),
    ("mcare_discharges",           "S300001", "00100", "01300", "numeric"),
    ("mcaid_discharges",           "S300001", "00100", "01400", "numeric"),
    ("tot_mcare_payment",          "E00A18A", "05900", "00100", "numeric"),
    ("secondary_mcare_payment",    "E00A18A", "06000", "00100", "numeric"),
    ("street",                     "S200001", "00100", "00100", "alpha"),
    ("city",                       "S200001", "00200", "00100", "alpha"),
    ("state",                      "S200001", "00200", "00200", "alpha"),
    ("zip",                        "S200001", "00200", "00300", "alpha"),
    ("county",                     "S200001", "00200", "00400", "alpha"),
    ("name",                       "S200001", "00300", "00100", "alpha"),
    ("hvbp_payment",               "E00A18A", "07093", "00100", "numeric"),
    ("hrrp_payment",               "E00A18A", "07094", "00100", "numeric"),
    ("tot_uncomp_care_charges",    "S100000", "02000", "00300", "numeric"),
    ("tot_uncomp_care_partial_pmts","S100000", "02200", "00300", "numeric"),
    ("bad_debt",                   "S100000", "02800", "00100", "numeric"),
    ("cost_to_charge",             "S100000", "00100", "00100", "numeric"),
    ("new_cap_ass",                "A700001", "01000", "00200", "numeric"),
    ("cash",                       "G000000", "00100", "00100", "numeric"),
    ("fixed_assets",               "G000000", "03000", "00100", "numeric"),
    ("depr_land",                  "G000000", "01400", "00100", "numeric"),
    ("depr_bldg",                  "G000000", "01600", "00100", "numeric"),
    ("depr_lease",                 "G000000", "01800", "00100", "numeric"),
    ("depr_fixed_equip",           "G000000", "02000", "00100", "numeric"),
    ("depr_auto",                  "G000000", "02200", "00100", "numeric"),
    ("depr_major_equip",           "G000000", "02400", "00100", "numeric"),
    ("depr_minor_equip",           "G000000", "02600", "00100", "numeric"),
    ("depr_HIT",                   "G000000", "02800", "00100", "numeric"),
    ("current_assets",             "G000000", "01100", "00100", "numeric"),
    ("current_liabilities",        "G000000", "04500", "00100", "numeric"),
]

RPT_COLS = [
    "RPT_REC_NUM", "PRVDR_CTRL_TYPE_CD", "PRVDR_NUM", "NPI",
    "RPT_STUS_CD", "FY_BGN_DT", "FY_END_DT", "PROC_DT",
    "INITL_RPT_SW", "LAST_RPT_SW", "TRNSMTL_NUM", "FI_NUM",
    "ADR_VNDR_CD", "FI_CREAT_DT", "UTIL_CD", "NPR_DT",
    "SPEC_IND", "FI_RCPT_DT",
]

LONG_COLS = ["RPT_REC_NUM", "WKSHT_CD", "LINE_NUM", "CLMN_NUM", "ITM_VAL_NUM"]


# File path resolver -------------------------------------------------------

def _resolve_path(year, suffix):
    """Find the CSV file for a given year and suffix (alpha/nmrc/rpt).

    Tries unzipped folders first (two naming conventions), then ZIP archives.
    Returns (path_or_buffer, label) where label is for logging.
    """
    base = Path("data/input/HCRIS_v2010")

    folders = [f"HospitalFY{year}", f"HOSP10FY{year}"]
    files = [
        f"hosp10_{year}_{suffix.upper()}.CSV",
        f"HOSP10_{year}_{suffix.lower()}.csv",
    ]
    for folder in folders:
        for fname in files:
            path = base / folder / fname
            if path.exists():
                return path, str(path)

    # ZIP fallback
    zips = [
        f"HOSP10FY{year}.ZIP", f"HOSP10FY{year}.zip",
        f"HospitalFY{year}.ZIP", f"HospitalFY{year}.zip",
    ]
    entries = [
        f"HOSP10_{year}_{suffix.lower()}.csv",
        f"hosp10_{year}_{suffix.upper()}.CSV",
    ]
    for zf in zips:
        zip_path = base / zf
        if zip_path.exists():
            with ZipFile(zip_path) as zfile:
                names = zfile.namelist()
                for entry in entries:
                    if entry in names:
                        buf = io.BytesIO(zfile.read(entry))
                        return buf, f"{zip_path}:{entry}"

    raise FileNotFoundError(f"Cannot find HCRIS v2010 data for year {year}, suffix {suffix}")


def _read_csv(year, suffix, col_names):
    source, label = _resolve_path(year, suffix)
    return pd.read_csv(source, header=None, names=col_names, dtype=str)


# Extraction ---------------------------------------------------------------

def extract_v2010():
    print("Extracting HCRIS v2010 (2010-2025)...")
    frames = []
    for yr in range(2010, 2026):
        alpha = _read_csv(yr, "alpha", LONG_COLS)
        nmrc = _read_csv(yr, "nmrc", LONG_COLS)
        rpt = _read_csv(yr, "rpt", RPT_COLS)

        final = rpt[["RPT_REC_NUM", "PRVDR_NUM", "NPI", "FY_BGN_DT", "FY_END_DT",
                      "PROC_DT", "FI_CREAT_DT", "RPT_STUS_CD"]].copy()
        final.columns = ["report", "provider_number", "npi", "fy_start", "fy_end",
                         "date_processed", "date_created", "status"]
        final["year"] = yr
        final["data_source"] = "v2010"

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
        print(f"  v2010 {yr}: {len(final):,} reports")

    combined = pd.concat(frames, ignore_index=True)
    combined.to_csv("data/output/HCRIS_Data_v2010.txt", sep="\t", index=False)
    print(f"  v2010 total: {len(combined):,} rows written")
    return combined


if __name__ == "__main__":
    extract_v2010()
