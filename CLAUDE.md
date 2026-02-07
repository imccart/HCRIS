# HCRIS Project

## Overview
R-based ETL pipeline for Medicare hospital cost report data. Extracts ~40 financial/operational variables from three overlapping data sources and consolidates into a single panel dataset.

## Data Sources
- **PPS** (1985-1999): NBER Prospective Payment System minimum dataset. Pre-extracted Stata flat files from Form 2552-85/89/92/96.
- **HCRIS v1996** (1998-2011): CMS HCRIS using Form 2552-96. Raw CSV (long format) extracted by worksheet/line/column codes.
- **HCRIS v2010** (2010-2020): CMS HCRIS using Form 2552-10. Same extraction approach as v1996.

## Pipeline
1. `data-code/0_download_pps.R` — Downloads PPS Stata files from NBER
2. `data-code/H3_HCRIS_PPS.R` — Extracts PPS data (1985-1999)
3. `data-code/H1_HCRISv1996.R` — Extracts HCRIS v1996 data (1998-2011)
4. `data-code/H2_HCRISv2010.R` — Extracts HCRIS v2010 data (2010-2020)
5. `data-code/_HCRIS_Data.R` — Orchestrates H1-H3, adds missing vars, deduplicates, writes final output

## Key Technical Details

### PPS Date Formats
- Pre-1996: Julian `YYDDD` (e.g., "91274" = Oct 1, 1991)
- 1996-1999: `CCYYMMDD` (e.g., "19971001")
- H3 converts both to `M/D/YYYY` to match HCRIS output

### PPS Variable Limitations (Pre-1996)
- `tot_charges` = `totalg` (from cost allocation, not revenue statement)
- `tot_operating_exp` = `opertots` (Medicare-specific operating costs only)
- `ip_charges` = `mtotalg` (Medicare inpatient charges, not total inpatient)
- `ancillary_charges` = `outpatg` (total outpatient charges, approximate match)
- Balance sheet variables (cash, assets, liabilities, depreciation) = NA for 1985-1995
- `net_pat_rev`, `tot_discounts` = NA for 1985-1995 (revenue statement not in minimum dataset)

### PPS Capital Files (1987-1991) — Deferred
- Separate raw EBCDIC files from NBER, stored in `data/input/hcris_pps_nber/capital/`
- **Not integrated.** Core operational data (beds, charges, discharges, payments) for 1985-1995 is already extracted from the minimum dataset. These capital files would only potentially fill balance sheet variables (cash, fixed assets, depreciation, etc.) that are currently NA for pre-1996 rows.
- **Why deferred:** The SAS reading program (`capital/docs/read_cap4.sas`) documents only 10 fields (~60 bytes) of a 4647-byte record. The layout PDF (`ppsc1_8.pdf`) is a scanned image, not text-parseable. The files only cover 1987-1991, leaving gaps for 1985-1986 and 1992-1995 regardless. High effort, uncertain payoff.
- **To restart:** Decompress `.Z` files (Unix compress/LZW), convert EBCDIC to ASCII, map the full 4647-byte record layout using the scanned PDF, then extract and merge relevant fields by provider number into H3.

### Duplicate Report Handling
The deduplication in `_HCRIS_Data.R` uses a 4-tier strategy:
1. Unique reports (one report per provider/fiscal year)
2. Sum if total days < 370
3. Pick primary report if one covers full year
4. Weighted average by time coverage

### Environment
- R at `/c/Program Files/R/R-4.4.1/bin/Rscript.exe` — segfaults in MINGW shell, run from RStudio or native Windows terminal
- Python works from MINGW: `python` at standard path
- Raw data in `data/input/` is gitignored; crosswalks in `data-code/pps-xwalk/` are tracked

## File Organization
```
data-code/
  _HCRIS_Data.R              # Main orchestrator
  0_download_pps.R            # PPS download script
  H1_HCRISv1996.R             # HCRIS v1996 extraction
  H2_HCRISv2010.R             # HCRIS v2010 extraction
  H3_HCRIS_PPS.R              # PPS extraction
  pps-xwalk/
    xwalk_2552-96.csv          # Field mapping for 1996-1999
    xwalk_pre1996.csv          # Field mapping for 1985-1995
    ssa_state_codes.csv        # SSA code to state abbreviation

data/input/
  hcris_pps_nber/              # PPS Stata files (gitignored)
    capital/                   # Capital EBCDIC files + docs (gitignored)
  HCRIS_v1996/                 # Raw HCRIS v1996 CSVs (gitignored)
  HCRIS_v2010/                 # Raw HCRIS v2010 CSVs (gitignored)

data/output/
  HCRIS_Data.txt               # Final combined dataset
  HCRIS_Data_v1996.txt         # Intermediate v1996 output
  HCRIS_Data_v2010.txt         # Intermediate v2010 output
  HCRIS_Data_PPS.txt           # Intermediate PPS output
```

### Source-Priority Deduplication
When the same `provider_number + fy_start + fy_end` appears across sources, `_HCRIS_Data.R` keeps the highest-priority row (v2010 > v1996 > pps), breaking ties by latest `date_created`.

### NA-Safe Aggregation
`_HCRIS_Data.R` uses helpers `na_sum`, `na_max`, `na_min` so all-NA groups return `NA` (not `0` or `-Inf`).

### Provider Number Padding
All extraction scripts pad provider numbers to 6 digits with leading zeros (`pad_provider()` in H3; equivalent logic in H1/H2).

### Data Source Flag
Each extraction script tags rows: `data_source = "pps"` / `"v1996"` / `"v2010"`.

### PPS-Equivalent Variables for Imputation

Pre-1996 PPS variables measure different things than their HCRIS counterparts:

| Variable | PPS (pre-1996) definition | HCRIS v1996+ definition |
|----------|--------------------------|------------------------|
| `tot_operating_exp` | `opertots` — Medicare-specific operating costs | Total operating expenses (all payers) |
| `tot_charges` | `totalg` — cost-allocation charges | Revenue-statement charges |
| `ip_charges` | `mtotalg` — Medicare inpatient charges | Total inpatient charges |

To support downstream imputation models that bridge these measurement systems, H1 extracts the cost-allocation equivalents from the HCRIS v1996 raw data (Form 2552-96 still contains both measurement systems on different worksheets):

| Column | Source | Description |
|--------|--------|-------------|
| `pps_ip_charges` | Wkst C Part I (C000001), Line 101, Col 6 | Inpatient charges from cost allocation |
| `pps_op_charges` | Wkst C Part I (C000001), Line 101, Col 7 | Outpatient charges from cost allocation |
| `pps_mcare_cost` | Wkst D (D10A181), Line 49, Col 1 | Total Medicare inpatient operating costs |
| `pps_pgm_cost` | Wkst D (D10A181), Line 53, Col 1 | Program inpatient operating cost (net of pass-throughs) |

These are populated for v1996 rows (~98% coverage) and NA for PPS and v2010 rows. Downstream projects can train models on v1996 data where both measurement systems are observed, then apply to pre-1996 PPS data.

## Status (2026-02-07)
- PPS minimum dataset fully integrated: H3 + crosswalks + download script + all 19 Stata files downloaded.
- PPS-equivalent variables (`pps_ip_charges`, `pps_op_charges`, `pps_mcare_cost`, `pps_pgm_cost`) extracted in H1 and carried through pipeline.
- Capital files downloaded but intentionally deferred (see "PPS Capital Files" above).
- `0_download_pps.R` handles both minimum dataset and capital file downloads.
- Rscript in MINGW segfaults; run from RStudio or Windows terminal.
