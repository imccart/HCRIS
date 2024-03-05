# Healthcare Cost Report Information System (HCRIS)
This repository provides the necessary code and links to download and organize key hospital information contained in the Healthcare Cost Report Information System.

## Raw Data
All of the raw data are publicly available from the Centers for Medicare and Medicaid Services (CMS) website: [HCRIS DATA](https://www.cms.gov/Research-Statistics-Data-and-Systems/Downloadable-Public-Use-Files/Cost-Reports/Cost-Reports-by-Fiscal-Year.html). These data are also available through the NBER: [NBER HCRIS Data](https://www.nber.org/data/hcris.html). 

The flat files in the NBER source should match to the raw files downloadable from CMS, but the NBER page includes additional details and links to more documentation. You can also access a subset of variables directly as SAS, Stata, or .csv files, in which case you don't need any of the raw data or the code below.

## Raw Code Files
After downloading the flat files, the following code files will extract selected variables and form a final analytic dataset. There are two R code files, one for each of the different versions of HCRIS worksheets (v1996 at [H1_HCRISv1996.R](https://github.com/imccart/HCRIS/blob/master/data-code/H1_HCRISv1996.R) and v2010 at [H2_HCRISv2010.R](https://github.com/imccart/HCRIS/blob/master/data-code/H2_HCRISv2010.R), respectively). 

The top sections of each of the code files assign the location of the selected variables. These code files are almost identical; however, not all variables are in the same location of the HCRIS worksheets under v1996 and v2010. New variables can easily be added if you know the worksheet, line number, and column number of the relevant variable. If the variable is numeric, it should be in the numeric tables, and if its a character, it should be in the alphanumeric tables. This information should be indicated in the "source" column when assigning each variable's location, with possible values of 'numeric' or 'alpha'. 


## Master Code File
There is also a master code file that calls each of the individual code files and organizes the resulting data into unique hospital/year combinations: [_HCRIS_Data.R](https://github.com/imccart/HCRIS/blob/master/data-code/_HCRIS_Data.R)

There are two common issues with the HCRIS data that are resolved (at least, attempted to be resolved) in the master code file. There are of course other issues that you will encounter when trying to work with these data, including missing variables in some years and clear evidence of misreporting in some cases, not to mention just very noisy data in general.

1. Negative values: Variables that reflect a "loss" or a discount are often intended to take positive values in the worksheets but may sometimes take negative values for certain hospitals in certain years. For the subset of variables in these code files, I take the absolute value of all such variables. This may or may not apply to any additional variables that you want to add. To be sure if this is a mistake in the data, check the worksheet instruments in the documentation. 

2. Duplicate reports: Many hospitals change fiscal years at some point over the panel. Since HCRIS reports reflect data for each hospital's fiscal year, such a change will tend to result in more than one report for a given hospital in a given year. There also does not appear to be any systematic way in which hospitals submit data during these transitions. Some hospitals, for example, will transition with two reports that each cover less than a 12 month period; others will transition with one report that covers a longer period; and still others will transition with two reports that each cover a different 12 month period (one starting at the beginning of the original FY and going through the end of the original FY, and another starting at the new FY and ending at the new FY). The master code file collapses these instances with a series of different rules as commented in the code. The end result is a set of unique hospital/year combinations, where hospitals are defined by Medicare provider numbers and years are defined as hospital fiscal years.

