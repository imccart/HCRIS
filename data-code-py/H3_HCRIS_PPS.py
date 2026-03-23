"""PPS (Prospective Payment System) extraction — 1985-1999.

Pre-extracted Stata flat files from NBER, using Form 2552-85/89/92/96.
- 1985-1995: limited variable set (no balance sheet, no revenue stmt)
- 1996-1999: full variable set, split into two parts per year
Date formats:
- Pre-1996: Julian YYDDD (e.g., "91274" = Oct 1, 1991)
- 1996-1999: CCYYMMDD (e.g., "19971001")
Output dates formatted as M/D/YYYY to match HCRIS H1/H2 output.
"""

from pathlib import Path
import numpy as np
import pandas as pd


# SSA state code mapping ---------------------------------------------------

SSA_STATE = pd.read_csv(
    Path("data-code/pps-xwalk/ssa_state_codes.csv"),
    dtype={"ssa_code": str, "state": str},
)
_STATE_MAP = dict(zip(SSA_STATE["ssa_code"], SSA_STATE["state"]))


# Helper functions ---------------------------------------------------------

def pad_provider(s):
    """Pad provider number to 6 digits with leading zeros."""
    s = pd.Series(s).astype(str).str.strip()
    return s.where(s != "", other=pd.NA).str.zfill(6)


def get_state_from_provider(provider_num):
    """Derive state abbreviation from first 2 digits of provider number."""
    return pd.Series(provider_num).astype(str).str[:2].map(_STATE_MAP)


def _strftime_mdy(dates):
    """Format datetime Series as M/D/YYYY (no leading zeros), cross-platform."""
    m = dates.dt.month.astype("Int64").astype(str)
    d = dates.dt.day.astype("Int64").astype(str)
    y = dates.dt.year.astype("Int64").astype(str)
    result = m + "/" + d + "/" + y
    return result.where(dates.notna(), other=pd.NA)


def parse_julian_date(date_str):
    """Parse Julian YYDDD strings to M/D/YYYY."""
    s = pd.Series(date_str).astype(str).str.strip()
    mask = s.notna() & (s.str.len() >= 5)
    yy = pd.to_numeric(s.str[:2], errors="coerce")
    ddd = pd.to_numeric(s.str[2:5], errors="coerce")
    year = np.where(yy >= 80, 1900 + yy, 2000 + yy)
    base = pd.to_datetime(
        pd.Series(year, dtype="Int64").astype(str) + "-01-01",
        errors="coerce",
    )
    dates = base + pd.to_timedelta(ddd - 1, unit="D")
    result = _strftime_mdy(dates)
    result = result.where(mask, other=pd.NA)
    return result


def parse_ccyymmdd(date_str):
    """Parse CCYYMMDD strings to M/D/YYYY."""
    s = pd.Series(date_str).astype(str).str.strip()
    mask = s.notna() & (s.str.len() == 8)
    dates = pd.to_datetime(s, format="%Y%m%d", errors="coerce")
    result = _strftime_mdy(dates)
    result = result.where(mask, other=pd.NA)
    return result


# Column template (consistent output order) --------------------------------

OUTPUT_COLS = [
    "report", "provider_number", "npi", "fy_start", "fy_end",
    "date_processed", "date_created", "status", "year", "data_source",
    "beds", "tot_charges", "net_pat_rev", "tot_discounts", "tot_operating_exp",
    "ip_charges", "icu_charges", "ancillary_charges",
    "tot_discharges", "mcare_discharges", "mcaid_discharges",
    "tot_mcare_payment", "secondary_mcare_payment",
    "street", "city", "state", "zip", "county", "name",
    "uncomp_care", "cost_to_charge",
    "new_cap_ass", "cash", "fixed_assets",
    "depr_land", "depr_bldg", "depr_lease", "depr_fixed_equip",
    "depr_auto", "depr_major_equip", "depr_minor_equip",
    "current_assets", "current_liabilities",
    "pps_ip_charges", "pps_op_charges", "pps_mcare_cost", "pps_pgm_cost",
]


# Import PPS 1996-1999 ----------------------------------------------------

def extract_pps_1996_1999():
    frames = []
    for yr in range(1996, 2000):
        yy = str(yr)[2:]
        base = Path("data/input/hcris_pps_nber")
        part1 = pd.read_stata(base / f"pps{yy}_f1_f1800.dta")
        part2 = pd.read_stata(base / f"pps{yy}_f1801_to_end.dta")
        part1["f1"] = pad_provider(part1["f1"]).values
        part2["f1"] = pad_provider(part2["f1"]).values
        pps = part1.merge(part2, on="f1", how="left")

        df = pd.DataFrame({
            "report": pd.NA,
            "provider_number": pps["f1"],
            "npi": pd.NA,
            "fy_start": parse_ccyymmdd(pps["f22"]).values,
            "fy_end": parse_ccyymmdd(pps["f23"]).values,
            "date_processed": pd.NA,
            "date_created": parse_ccyymmdd(pps["f69"]).values,
            "status": pps["f74"].astype(str),
            "year": yr,
            "data_source": "pps",
            "beds": pd.to_numeric(pps["f85"], errors="coerce"),
            "tot_charges": pd.to_numeric(pps["f2135"], errors="coerce"),
            "net_pat_rev": pd.to_numeric(pps["f2137"], errors="coerce"),
            "tot_discounts": pd.to_numeric(pps["f2136"], errors="coerce"),
            "tot_operating_exp": pd.to_numeric(pps["f2138"], errors="coerce"),
            "ip_charges": pd.to_numeric(pps["f2133"], errors="coerce"),
            "icu_charges": pd.to_numeric(pps["f2108"], errors="coerce"),
            "ancillary_charges": pd.to_numeric(pps["f2115"], errors="coerce"),
            "tot_discharges": pd.to_numeric(pps["f178"], errors="coerce"),
            "mcare_discharges": pd.to_numeric(pps["f172"], errors="coerce"),
            "mcaid_discharges": pd.to_numeric(pps["f175"], errors="coerce"),
            "tot_mcare_payment": pd.to_numeric(pps["f1833"], errors="coerce"),
            "secondary_mcare_payment": pd.to_numeric(pps["f1834"], errors="coerce"),
            "street": pd.NA,
            "city": pd.NA,
            "state": get_state_from_provider(pps["f1"]).values,
            "zip": pd.NA,
            "county": pd.NA,
            "name": pps["f18"].astype(str),
            "uncomp_care": np.nan,
            "cost_to_charge": np.nan,
            "new_cap_ass": pd.to_numeric(pps["f1473"], errors="coerce"),
            "cash": pd.to_numeric(pps["f2038"], errors="coerce"),
            "fixed_assets": pd.to_numeric(pps["f2066"], errors="coerce"),
            "depr_land": pd.to_numeric(pps["f2050"], errors="coerce"),
            "depr_bldg": pd.to_numeric(pps["f2054"], errors="coerce"),
            "depr_lease": pd.to_numeric(pps["f2056"], errors="coerce"),
            "depr_fixed_equip": pd.to_numeric(pps["f2058"], errors="coerce"),
            "depr_auto": pd.to_numeric(pps["f2060"], errors="coerce"),
            "depr_major_equip": pd.to_numeric(pps["f2062"], errors="coerce"),
            "depr_minor_equip": pd.to_numeric(pps["f2064"], errors="coerce"),
            "current_assets": pd.to_numeric(pps["f2048"], errors="coerce"),
            "current_liabilities": pd.to_numeric(pps["f2081"], errors="coerce"),
            "pps_ip_charges": np.nan,
            "pps_op_charges": np.nan,
            "pps_mcare_cost": np.nan,
            "pps_pgm_cost": np.nan,
        })
        frames.append(df[OUTPUT_COLS])
        print(f"  PPS {yr}: {len(df):,} reports")
    return pd.concat(frames, ignore_index=True)


# Import PPS 1985-1995 ----------------------------------------------------

def extract_pps_1985_1995():
    frames = []
    for yr in range(1985, 1996):
        yy = str(yr)[2:]
        pps = pd.read_stata(Path("data/input/hcris_pps_nber") / f"pps{yy}.dta")
        pps["provno"] = pad_provider(pps["provno"]).values

        df = pd.DataFrame({
            "report": pd.NA,
            "provider_number": pps["provno"],
            "npi": pd.NA,
            "fy_start": parse_julian_date(pps["begdate"]).values,
            "fy_end": parse_julian_date(pps["enddate"]).values,
            "date_processed": pd.NA,
            "date_created": pd.NA,
            "status": pps["status"].astype(str),
            "year": yr,
            "data_source": "pps",
            "beds": pd.to_numeric(pps["totbeds"], errors="coerce"),
            "tot_charges": pd.to_numeric(pps["totalg"], errors="coerce"),
            "net_pat_rev": np.nan,
            "tot_discounts": np.nan,
            "tot_operating_exp": pd.to_numeric(pps["opertots"], errors="coerce"),
            "ip_charges": pd.to_numeric(pps["mtotalg"], errors="coerce"),
            "icu_charges": np.nan,
            "ancillary_charges": pd.to_numeric(pps["outpatg"], errors="coerce"),
            "tot_discharges": pd.to_numeric(pps["f88"], errors="coerce"),
            "mcare_discharges": pd.to_numeric(pps["f82"], errors="coerce"),
            "mcaid_discharges": pd.to_numeric(pps["f84"], errors="coerce"),
            "tot_mcare_payment": pd.to_numeric(pps["amtdue"], errors="coerce"),
            "secondary_mcare_payment": np.nan,
            "street": pd.NA,
            "city": pd.NA,
            "state": get_state_from_provider(pps["provno"]).values,
            "zip": pd.NA,
            "county": pd.NA,
            "name": pps["provname"].astype(str),
            "uncomp_care": np.nan,
            "cost_to_charge": np.nan,
            "new_cap_ass": np.nan,
            "cash": np.nan,
            "fixed_assets": np.nan,
            "depr_land": np.nan,
            "depr_bldg": np.nan,
            "depr_lease": np.nan,
            "depr_fixed_equip": np.nan,
            "depr_auto": np.nan,
            "depr_major_equip": np.nan,
            "depr_minor_equip": np.nan,
            "current_assets": np.nan,
            "current_liabilities": np.nan,
            "pps_ip_charges": np.nan,
            "pps_op_charges": np.nan,
            "pps_mcare_cost": np.nan,
            "pps_pgm_cost": np.nan,
        })
        frames.append(df[OUTPUT_COLS])
        print(f"  PPS {yr}: {len(df):,} reports")
    return pd.concat(frames, ignore_index=True)


# Main ---------------------------------------------------------------------

def extract_pps():
    print("Extracting PPS data (1985-1999)...")
    early = extract_pps_1985_1995()
    late = extract_pps_1996_1999()
    combined = pd.concat([early, late], ignore_index=True)
    combined.to_csv("data/output/HCRIS_Data_PPS.txt", sep="\t", index=False)
    print(f"  PPS total: {len(combined):,} rows written")
    return combined


if __name__ == "__main__":
    extract_pps()
