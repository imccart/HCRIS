
# Download PPS Stata files from NBER ----------------------------------------
# Run this script once to download all PPS data files into data/input/hcris_pps_nber/

dir.create("data/input/hcris_pps_nber", recursive=TRUE, showWarnings=FALSE)
dir.create("data/input/hcris_pps_nber/capital/docs", recursive=TRUE, showWarnings=FALSE)
base_url <- "https://data.nber.org/pps/data/stata/"
cap_base_url <- "https://data.nber.org/pps"

## Single-file years (1985-1995): one .dta file per year
for (yr in 1985:1995) {
  yy <- substr(as.character(yr), 3, 4)
  fname <- paste0("pps", yy, ".dta")
  dest <- paste0("data/input/hcris_pps_nber/", fname)
  if (!file.exists(dest)) {
    cat("Downloading", fname, "...\n")
    download.file(paste0(base_url, fname), dest, mode="wb")
  } else {
    cat(fname, "already exists, skipping.\n")
  }
}

## Split-file years (1996-1999): two .dta files per year
for (yr in 1996:1999) {
  yy <- substr(as.character(yr), 3, 4)
  for (suffix in c("_f1_f1800", "_f1801_to_end")) {
    fname <- paste0("pps", yy, suffix, ".dta")
    dest <- paste0("data/input/hcris_pps_nber/", fname)
    if (!file.exists(dest)) {
      cat("Downloading", fname, "...\n")
      download.file(paste0(base_url, fname), dest, mode="wb")
    } else {
      cat(fname, "already exists, skipping.\n")
    }
  }
}

cat("Done. All PPS files downloaded to data/input/hcris_pps_nber/\n")

## Capital files + docs (1987-1991; raw EBCDIC .Z + documentation)
cap_files <- c("pps4cap.data.Z", "pps5cap.data.Z", "pps6cap.data.Z", "pps7cap.data.Z", "pps8cap.data.Z")
for (fname in cap_files) {
  dest <- paste0("data/input/hcris_pps_nber/capital/", fname)
  if (!file.exists(dest)) {
    cat("Downloading", fname, "...\n")
    download.file(paste0(cap_base_url, "/data/raw/", fname), dest, mode="wb")
  } else {
    cat(fname, "already exists, skipping.\n")
  }
}

cap_docs <- c("ppsc1_8.pdf", "read_cap4.sas")
for (fname in cap_docs) {
  dest <- paste0("data/input/hcris_pps_nber/capital/docs/", fname)
  if (!file.exists(dest)) {
    cat("Downloading", fname, "...\n")
    if (fname == "ppsc1_8.pdf") {
      download.file(paste0(cap_base_url, "/layout/", fname), dest, mode="wb")
    } else {
      download.file(paste0(cap_base_url, "/prog/sas/", fname), dest, mode="wb")
    }
  } else {
    cat(fname, "already exists, skipping.\n")
  }
}

cat("Done. Capital files and docs downloaded to data/input/hcris_pps_nber/capital/\n")
