
# Variable locations ------------------------------------------------------

hcris.vars <- NULL
hcris.vars <- rbind(hcris.vars,c('beds','S300001','01200','0100','numeric'))
hcris.vars <- rbind(hcris.vars,c('tot_charges','G300000','00100','0100','numeric'))
hcris.vars <- rbind(hcris.vars,c('net_pat_rev','G300000','00300','0100','numeric'))
hcris.vars <- rbind(hcris.vars,c('tot_discounts','G300000','00200','0100','numeric'))
hcris.vars <- rbind(hcris.vars,c('tot_operating_exp','G300000','00400','0100','numeric'))
hcris.vars <- rbind(hcris.vars,c('ip_charges','G200000','00100','0100','numeric'))
hcris.vars <- rbind(hcris.vars,c('icu_charges','G200000','01500','0100','numeric'))
hcris.vars <- rbind(hcris.vars,c('ancillary_charges','G200000','01700','0100','numeric'))
hcris.vars <- rbind(hcris.vars,c('tot_discharges','S300001','00100','1500','numeric'))
hcris.vars <- rbind(hcris.vars,c('mcare_discharges','S300001','00100','1300','numeric'))
hcris.vars <- rbind(hcris.vars,c('mcaid_discharges','S300001','00100','1400','numeric'))
hcris.vars <- rbind(hcris.vars,c('tot_mcare_payment','E00A18A','01600','0100','numeric'))
hcris.vars <- rbind(hcris.vars,c('secondary_mcare_payment','E00A18A','01700','0100','numeric'))
hcris.vars <- rbind(hcris.vars,c('street','S200000','00100','0100','alpha'))
hcris.vars <- rbind(hcris.vars,c('city','S200000','00101','0100','alpha'))
hcris.vars <- rbind(hcris.vars,c('state','S200000','00101','0200','alpha'))
hcris.vars <- rbind(hcris.vars,c('zip','S200000','00101','0300','alpha'))
hcris.vars <- rbind(hcris.vars,c('county','S200000','00101','0400','alpha'))
hcris.vars <- rbind(hcris.vars,c('name','S200000','00200','0100','alpha'))
hcris.vars <- rbind(hcris.vars,c('uncomp_care','S100000','03000','0100','numeric'))
hcris.vars <- rbind(hcris.vars,c('cost_to_charge','S100000','02400','0100','numeric'))
hcris.vars <- rbind(hcris.vars,c('new_cap_ass','A700002','00900','0200','numeric'))
hcris.vars <- rbind(hcris.vars,c('cash','G000000','00100','0100','numeric'))
hcris.vars <- rbind(hcris.vars,c('fixed_assets','G000000','02100','0100','numeric'))
hcris.vars <- rbind(hcris.vars,c('depr_land','G000000','01301','0100','numeric'))
hcris.vars <- rbind(hcris.vars,c('depr_bldg','G000000','01401','0100','numeric'))
hcris.vars <- rbind(hcris.vars,c('depr_lease','G000000','01501','0100','numeric'))
hcris.vars <- rbind(hcris.vars,c('depr_fixed_equip','G000000','01601','0100','numeric'))
hcris.vars <- rbind(hcris.vars,c('depr_auto','G000000','01701','0100','numeric'))
hcris.vars <- rbind(hcris.vars,c('depr_major_equip','G000000','01801','0100','numeric'))
hcris.vars <- rbind(hcris.vars,c('depr_minor_equip','G000000','01901','0100','numeric'))
hcris.vars <- rbind(hcris.vars,c('current_assets','G000000','01100','0100','numeric'))
hcris.vars <- rbind(hcris.vars,c('current_liabilities','G000000','03600','0100','numeric'))
hcris.vars <- rbind(hcris.vars,c('pps_ip_charges','C000001','10100','0600','numeric'))
hcris.vars <- rbind(hcris.vars,c('pps_op_charges','C000001','10100','0700','numeric'))
hcris.vars <- rbind(hcris.vars,c('pps_mcare_cost','D10A181','04900','0100','numeric'))
hcris.vars <- rbind(hcris.vars,c('pps_pgm_cost','D10A181','05300','0100','numeric'))
colnames(hcris.vars) <- c("variable","WKSHT_CD","LINE_NUM","CLMN_NUM","source")


# Import data -------------------------------------------------------------

for (i in 1998:2011) {
  HCRIS.alpha <- read_csv(paste0("data/input/HCRIS_v1996/HospitalFY",i,"/hosp_",i,"_ALPHA.CSV"),
                       col_names=c('RPT_REC_NUM','WKSHT_CD','LINE_NUM','CLMN_NUM','ITM_VAL_NUM'))
  HCRIS.numeric <- read_csv(paste0("data/input/HCRIS_v1996/HospitalFY",i,"/hosp_",i,"_NMRC.CSV"),
                         col_names=c('RPT_REC_NUM','WKSHT_CD','LINE_NUM','CLMN_NUM','ITM_VAL_NUM'))
  HCRIS.report <- read_csv(paste0("data/input/HCRIS_v1996/HospitalFY",i,"/hosp_",i,"_RPT.CSV"),
                        col_names=c('RPT_REC_NUM','PRVDR_CTRL_TYPE_CD','PRVDR_NUM','NPI',
                                    'RPT_STUS_CD','FY_BGN_DT','FY_END_DT','PROC_DT',
                                    'INITL_RPT_SW','LAST_RPT_SW','TRNSMTL_NUM','FI_NUM',
                                    'ADR_VNDR_CD','FI_CREAT_DT','UTIL_CD','NPR_DT',
                                    'SPEC_IND','FI_RCPT_DT'))
  final.reports <- HCRIS.report %>%
    select(report=RPT_REC_NUM, provider_number=PRVDR_NUM, npi=NPI, 
           fy_start=FY_BGN_DT, fy_end=FY_END_DT, date_processed=PROC_DT, 
           date_created=FI_CREAT_DT, status=RPT_STUS_CD) %>%
    mutate(year=i, data_source="v1996")
  
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
  if (i==1998) {
    final.hcris.v1996 <- final.reports.1998
  } else {
    final.hcris.v1996 <- rbind(final.hcris.v1996,get(paste0("final.reports.",i)))
  }
  
}
write_tsv(final.hcris.v1996,'data/output/HCRIS_Data_v1996.txt',append=FALSE,col_names<-TRUE)
