

# Variable locations ------------------------------------------------------

hcris.vars <- NULL
hcris.vars <- rbind(hcris.vars,c('beds','S300001','01400','00200','numeric'))
hcris.vars <- rbind(hcris.vars,c('tot_charges','G300000','00100','00100','numeric'))
hcris.vars <- rbind(hcris.vars,c('tot_discounts','G300000','00200','00100','numeric'))
hcris.vars <- rbind(hcris.vars,c('net_pat_rev','G300000','00300','00100','numeric'))
hcris.vars <- rbind(hcris.vars,c('tot_operating_exp','G300000','00400','00100','numeric'))
hcris.vars <- rbind(hcris.vars,c('ip_charges','G200000','00100','00100','numeric'))
hcris.vars <- rbind(hcris.vars,c('icu_charges','G200000','01600','00100','numeric'))
hcris.vars <- rbind(hcris.vars,c('ancillary_charges','G200000','01800','00100','numeric'))
hcris.vars <- rbind(hcris.vars,c('tot_discharges','S300001','00100','01500','numeric'))
hcris.vars <- rbind(hcris.vars,c('mcare_discharges','S300001','00100','01300','numeric'))
hcris.vars <- rbind(hcris.vars,c('mcaid_discharges','S300001','00100','01400','numeric'))
hcris.vars <- rbind(hcris.vars,c('tot_mcare_payment','E00A18A','05900','00100','numeric'))
hcris.vars <- rbind(hcris.vars,c('secondary_mcare_payment','E00A18A','06000','00100','numeric'))
hcris.vars <- rbind(hcris.vars,c('street','S200001','00100','00100','alpha'))
hcris.vars <- rbind(hcris.vars,c('city','S200001','00200','00100','alpha'))
hcris.vars <- rbind(hcris.vars,c('state','S200001','00200','00200','alpha'))
hcris.vars <- rbind(hcris.vars,c('zip','S200001','00200','00300','alpha'))
hcris.vars <- rbind(hcris.vars,c('county','S200001','00200','00400','alpha'))
hcris.vars <- rbind(hcris.vars,c('name','S200001','00300','00100','alpha'))
hcris.vars <- rbind(hcris.vars,c('hvbp_payment','E00A18A','07093','00100','numeric'))
hcris.vars <- rbind(hcris.vars,c('hrrp_payment','E00A18A','07094','00100','numeric'))
hcris.vars <- rbind(hcris.vars,c('tot_uncomp_care_charges','S100000','02000','00300','numeric'))
hcris.vars <- rbind(hcris.vars,c('tot_uncomp_care_partial_pmts','S100000','02200','00300','numeric'))
hcris.vars <- rbind(hcris.vars,c('bad_debt','S100000','02800','00100','numeric'))
hcris.vars <- rbind(hcris.vars,c('cost_to_charge','S100000','00100','00100','numeric'))
hcris.vars <- rbind(hcris.vars,c('new_cap_ass','A700001','01000','00200','numeric'))
hcris.vars <- rbind(hcris.vars,c('cash','G000000','00100','00100','numeric'))
hcris.vars <- rbind(hcris.vars,c('fixed_assets','G000000','03000','00100','numeric'))
hcris.vars <- rbind(hcris.vars,c('depr_land','G000000','01400','00100','numeric'))
hcris.vars <- rbind(hcris.vars,c('depr_bldg','G000000','01600','00100','numeric'))
hcris.vars <- rbind(hcris.vars,c('depr_lease','G000000','01800','00100','numeric'))
hcris.vars <- rbind(hcris.vars,c('depr_fixed_equip','G000000','02000','00100','numeric'))
hcris.vars <- rbind(hcris.vars,c('depr_auto','G000000','02200','00100','numeric'))
hcris.vars <- rbind(hcris.vars,c('depr_major_equip','G000000','02400','00100','numeric'))
hcris.vars <- rbind(hcris.vars,c('depr_minor_equip','G000000','02600','00100','numeric'))
hcris.vars <- rbind(hcris.vars,c('depr_HIT','G000000','02800','00100','numeric'))
hcris.vars <- rbind(hcris.vars,c('current_assets','G000000','01100','00100','numeric'))
hcris.vars <- rbind(hcris.vars,c('current_liabilities','G000000','04500','00100','numeric'))
colnames(hcris.vars) <- c("variable","WKSHT_CD","LINE_NUM","CLMN_NUM","source")



# Import data -------------------------------------------------------------

## Helper: build file paths for each year, handling folder/file naming changes
## and reading from ZIP archives when unzipped folders don't exist
hcris_v2010_path <- function(year, suffix) {
  base <- "data/input/HCRIS_v2010"

  ## Try unzipped folder first (two naming conventions)
  folders <- c(paste0("HospitalFY", year), paste0("HOSP10FY", year))
  files <- c(paste0("hosp10_", year, "_", toupper(suffix), ".CSV"),
             paste0("HOSP10_", year, "_", tolower(suffix), ".csv"))
  for (folder in folders) {
    for (file in files) {
      path <- file.path(base, folder, file)
      if (file.exists(path)) return(list(type="file", path=path))
    }
  }

  ## Fall back to ZIP archive
  zips <- c(paste0("HOSP10FY", year, ".ZIP"), paste0("HOSP10FY", year, ".zip"),
            paste0("HospitalFY", year, ".ZIP"), paste0("HospitalFY", year, ".zip"))
  zip_entries <- c(paste0("HOSP10_", year, "_", tolower(suffix), ".csv"),
                   paste0("hosp10_", year, "_", toupper(suffix), ".CSV"))
  for (zf in zips) {
    zip_path <- file.path(base, zf)
    if (file.exists(zip_path)) {
      contents <- tryCatch(unzip(zip_path, list=TRUE)$Name, error=function(e) character(0))
      for (entry in zip_entries) {
        if (entry %in% contents) return(list(type="zip", path=zip_path, entry=entry))
      }
    }
  }
  stop(paste("Cannot find HCRIS v2010 data for year", year))
}

hcris_v2010_read <- function(year, suffix, col_names) {
  loc <- hcris_v2010_path(year, suffix)
  if (loc$type == "file") {
    read_csv(loc$path, col_names=col_names, show_col_types=FALSE)
  } else {
    read_csv(unz(loc$path, loc$entry), col_names=col_names, show_col_types=FALSE)
  }
}

for (i in 2010:2025) {
  HCRIS.alpha <- hcris_v2010_read(i, "alpha",
                       col_names=c('RPT_REC_NUM','WKSHT_CD','LINE_NUM','CLMN_NUM','ITM_VAL_NUM'))
  HCRIS.numeric <- hcris_v2010_read(i, "nmrc",
                         col_names=c('RPT_REC_NUM','WKSHT_CD','LINE_NUM','CLMN_NUM','ITM_VAL_NUM'))
  HCRIS.report <- hcris_v2010_read(i, "rpt",
                        col_names=c('RPT_REC_NUM','PRVDR_CTRL_TYPE_CD','PRVDR_NUM','NPI',
                                    'RPT_STUS_CD','FY_BGN_DT','FY_END_DT','PROC_DT',
                                    'INITL_RPT_SW','LAST_RPT_SW','TRNSMTL_NUM','FI_NUM',
                                    'ADR_VNDR_CD','FI_CREAT_DT','UTIL_CD','NPR_DT',
                                    'SPEC_IND','FI_RCPT_DT'))
  final.reports <- HCRIS.report %>%
    select(report=RPT_REC_NUM, provider_number=PRVDR_NUM, npi=NPI, 
           fy_start=FY_BGN_DT, fy_end=FY_END_DT, date_processed=PROC_DT, 
           date_created=FI_CREAT_DT, status=RPT_STUS_CD) %>%
    mutate(year=i, data_source="v2010")
  
  for (v in 1:nrow(hcris.vars)) {
    hcris.data <- get(paste("HCRIS.",hcris.vars[v,5],sep=""))
    var.name <- quo_name(hcris.vars[v,1])    
    val <- hcris.data %>%
      filter(WKSHT_CD==hcris.vars[v,2], LINE_NUM==hcris.vars[v,3], CLMN_NUM==hcris.vars[v,4]) %>%
      select(report=RPT_REC_NUM, !!var.name:=ITM_VAL_NUM) 
    assign(paste("val.",v,sep=""),val)
    final.reports <- left_join(final.reports, 
              get(paste("val.",v,sep="")),
              by="report")
  }
  assign(paste("final.reports.",i,sep=""),final.reports)
  if (i==2010) {
    final.hcris.v2010 <- final.reports.2010
  } else {
    final.hcris.v2010 <- rbind(final.hcris.v2010,get(paste0("final.reports.",i)))
  }
}
write_tsv(final.hcris.v2010,'data/output/HCRIS_Data_v2010.txt',append=FALSE,col_names=TRUE)
