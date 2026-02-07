
# Meta --------------------------------------------------------------------

## Notes:  PPS (Prospective Payment System) minimum dataset from NBER
##         These data use the same underlying Form 2552 as HCRIS but are
##         pre-extracted flat files covering 1985-1999.
##         - 1985-1995: limited variable set (no balance sheet, no revenue stmt)
##         - 1996-1999: full variable set including balance sheet and revenue stmt
##         - 1996-1999 files are split into two parts due to Stata variable limits
##         Date formats:
##         - Pre-1996: Julian YYDDD (e.g., "91274" = Oct 1, 1991)
##         - 1996-1999: CCYYMMDD (e.g., "19971001")
##         Output dates formatted as M/D/YYYY to match HCRIS H1/H2 output.


# SSA state code mapping --------------------------------------------------

ssa.state <- read_csv('data-code/pps-xwalk/ssa_state_codes.csv',
                       col_types=cols(ssa_code=col_character(), state=col_character()))


# Helper functions ---------------------------------------------------------

## Derive state from provider number (first 2 digits = SSA state code)
get_state_from_provider <- function(provider_num) {
  ssa_code <- substr(as.character(provider_num), 1, 2)
  state_map <- setNames(ssa.state$state, ssa.state$ssa_code)
  return(unname(state_map[ssa_code]))
}

## Pad provider number to 6 digits (preserve leading zeros)
pad_provider <- function(provider_num) {
  provider_num <- trimws(as.character(provider_num))
  ifelse(is.na(provider_num) | provider_num == "", NA_character_,
         str_pad(provider_num, width = 6, side = "left", pad = "0"))
}

## Parse Julian YYDDD date strings to M/D/YYYY
parse_julian_date <- function(date_str) {
  date_str <- trimws(as.character(date_str))
  result <- rep(NA_character_, length(date_str))
  valid <- !is.na(date_str) & nchar(date_str) >= 5
  if (any(valid)) {
    yy <- as.integer(substr(date_str[valid], 1, 2))
    ddd <- as.integer(substr(date_str[valid], 3, 5))
    year <- ifelse(yy >= 80, 1900 + yy, 2000 + yy)
    dates <- as.Date(paste0(year, "-01-01")) + (ddd - 1)
    result[valid] <- format(dates, "%m/%d/%Y")
  }
  return(result)
}

## Parse CCYYMMDD date strings to M/D/YYYY
parse_ccyymmdd <- function(date_str) {
  date_str <- trimws(as.character(date_str))
  result <- rep(NA_character_, length(date_str))
  valid <- !is.na(date_str) & nchar(date_str) == 8
  if (any(valid)) {
    dates <- ymd(date_str[valid])
    result[valid] <- format(dates, "%m/%d/%Y")
  }
  return(result)
}


# Import PPS 1996-1999 (Form 2552-96) -------------------------------------
## These files have the full variable set including balance sheet

for (i in 1996:1999) {

  ## file naming: pps96, pps97, pps98, pps99
  yy <- substr(as.character(i), 3, 4)

  ## load and merge split files
  pps.part1 <- haven::read_dta(paste0("data/input/hcris_pps_nber/pps", yy, "_f1_f1800.dta"))
  pps.part2 <- haven::read_dta(paste0("data/input/hcris_pps_nber/pps", yy, "_f1801_to_end.dta"))
  pps.part1 <- pps.part1 %>% mutate(f1 = pad_provider(f1))
  pps.part2 <- pps.part2 %>% mutate(f1 = pad_provider(f1))
  pps.data <- left_join(pps.part1, pps.part2, by="f1")

  ## extract and rename variables per crosswalk
  final.reports <- pps.data %>%
    transmute(
      report = NA_character_,
      provider_number = f1,
      npi = NA_character_,
      fy_start = parse_ccyymmdd(f22),
      fy_end = parse_ccyymmdd(f23),
      date_processed = NA_character_,
      date_created = parse_ccyymmdd(f69),
      status = as.character(f74),
      year = i,
      data_source = "pps",

      ## facility characteristics
      beds = as.numeric(f85),

      ## charges and revenue (Worksheet G-3)
      tot_charges = as.numeric(f2135),
      net_pat_rev = as.numeric(f2137),
      tot_discounts = as.numeric(f2136),
      tot_operating_exp = as.numeric(f2138),

      ## inpatient detail
      ip_charges = as.numeric(f2133),
      icu_charges = as.numeric(f2108),
      ancillary_charges = as.numeric(f2115),

      ## discharges
      tot_discharges = as.numeric(f178),
      mcare_discharges = as.numeric(f172),
      mcaid_discharges = as.numeric(f175),

      ## Medicare payments (Worksheet E Part A)
      tot_mcare_payment = as.numeric(f1833),
      secondary_mcare_payment = as.numeric(f1834),

      ## address info
      street = NA_character_,
      city = NA_character_,
      state = get_state_from_provider(f1),
      zip = NA_character_,
      county = NA_character_,
      name = as.character(f18),

      ## uncompensated care and cost-to-charge
      uncomp_care = NA_real_,
      cost_to_charge = NA_real_,

      ## capital and assets
      new_cap_ass = as.numeric(f1473),
      cash = as.numeric(f2038),
      fixed_assets = as.numeric(f2066),

      ## depreciation (accumulated, from balance sheet)
      depr_land = as.numeric(f2050),
      depr_bldg = as.numeric(f2054),
      depr_lease = as.numeric(f2056),
      depr_fixed_equip = as.numeric(f2058),
      depr_auto = as.numeric(f2060),
      depr_major_equip = as.numeric(f2062),
      depr_minor_equip = as.numeric(f2064),

      ## balance sheet
      current_assets = as.numeric(f2048),
      current_liabilities = as.numeric(f2081),

      ## PPS-equivalent variables (only populated in v1996 HCRIS)
      pps_ip_charges = NA_real_,
      pps_op_charges = NA_real_,
      pps_mcare_cost = NA_real_,
      pps_pgm_cost = NA_real_
    )

  assign(paste0("final.reports.", i), final.reports)
  if (i == 1996) {
    final.hcris.pps96 <- final.reports
  } else {
    final.hcris.pps96 <- rbind(final.hcris.pps96, final.reports)
  }
}


# Import PPS 1985-1995 (Forms 2552-85, 2552-89, 2552-92) ------------------
## These files have a more limited variable set
## No balance sheet, no revenue/expense statement, no capital asset detail
## Dates are in Julian YYDDD format

for (i in 1985:1995) {

  yy <- substr(as.character(i), 3, 4)
  pps.data <- haven::read_dta(paste0("data/input/hcris_pps_nber/pps", yy, ".dta")) %>%
    mutate(provno = pad_provider(provno))

  final.reports <- pps.data %>%
    transmute(
      report = NA_character_,
      provider_number = provno,
      npi = NA_character_,
      fy_start = parse_julian_date(begdate),
      fy_end = parse_julian_date(enddate),
      date_processed = NA_character_,
      date_created = NA_character_,
      status = as.character(status),
      year = i,
      data_source = "pps",

      ## facility characteristics
      beds = as.numeric(totbeds),

      ## charges (from cost allocation worksheets, not revenue stmt)
      tot_charges = as.numeric(totalg),
      net_pat_rev = NA_real_,
      tot_discounts = NA_real_,
      tot_operating_exp = as.numeric(opertots),

      ## inpatient detail
      ip_charges = as.numeric(mtotalg),
      icu_charges = NA_real_,
      ancillary_charges = as.numeric(outpatg),

      ## discharges
      tot_discharges = as.numeric(f88),
      mcare_discharges = as.numeric(f82),
      mcaid_discharges = as.numeric(f84),

      ## Medicare payments
      tot_mcare_payment = as.numeric(amtdue),
      secondary_mcare_payment = NA_real_,

      ## address info
      street = NA_character_,
      city = NA_character_,
      state = get_state_from_provider(provno),
      zip = NA_character_,
      county = NA_character_,
      name = as.character(provname),

      ## uncompensated care and cost-to-charge
      uncomp_care = NA_real_,
      cost_to_charge = NA_real_,

      ## capital and assets (not available pre-1996)
      new_cap_ass = NA_real_,
      cash = NA_real_,
      fixed_assets = NA_real_,

      ## depreciation (not available pre-1996)
      depr_land = NA_real_,
      depr_bldg = NA_real_,
      depr_lease = NA_real_,
      depr_fixed_equip = NA_real_,
      depr_auto = NA_real_,
      depr_major_equip = NA_real_,
      depr_minor_equip = NA_real_,

      ## balance sheet (not available pre-1996)
      current_assets = NA_real_,
      current_liabilities = NA_real_,

      ## PPS-equivalent variables (only populated in v1996 HCRIS)
      pps_ip_charges = NA_real_,
      pps_op_charges = NA_real_,
      pps_mcare_cost = NA_real_,
      pps_pgm_cost = NA_real_
    )

  assign(paste0("final.reports.", i), final.reports)
  if (i == 1985) {
    final.hcris.pps.early <- final.reports
  } else {
    final.hcris.pps.early <- rbind(final.hcris.pps.early, final.reports)
  }
}


# Combine all PPS data -----------------------------------------------------

final.hcris.pps <- rbind(final.hcris.pps.early, final.hcris.pps96)


# Write output -------------------------------------------------------------

write_tsv(final.hcris.pps, 'data/output/HCRIS_Data_PPS.txt', append=FALSE, col_names=TRUE)
