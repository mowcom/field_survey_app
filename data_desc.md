Well Data Files Overview

These two datasets are downloaded from https://oklahoma.gov/occ/divisions/oil-gas/oil-gas-data.html 

The STFD Well List is the List of wells with State Funds Plugging Orders Each is updated every Thursday and available to download as an xlsx file. Note that the OCC does not maintain regulatory data (oil/gas well records, utility oversight, environmental data) on tribal reservation lands in Oklahoma because those lands are outside its jurisdiction. We use this data to find and track leaking orphan oil and gas wells to determine feasibility for plugging operations

Here’s a breakdown of the two Excel/CSV files you uploaded so your dev knows what they’re dealing with:  
**1\. Orphan Well List (orphan-well-list 2025-09-04.csv)**

* **Rows:** 19,240  
* **Columns:** 26  
* **Key fields:**  
  * API: Unique well identifier  
  * WellType: Oil, Gas, etc.  
  * WellStatus: OR (Orphan)  
  * OrphanDate: Date/time the well was classified as orphaned  
  * WellName / WellNumber  
  * OperatorName / OperatorNumber (the last known operator)  
  * X, Y: Geographic coordinates (longitude, latitude)  
  * CountyName, CountyNo  
  * Survey details: Sec, Township, TownshipDir, Range, RangeDir, PM  
  * Location breakdowns: Quarter, QuarterQuarter, … down to QuarterQuarterQuarterQuarter  
  * Footage details: FootageNS, NS, FootageEW, EW  
* **Example entry (simplified):**  
  * API: 35003200000000  
  * WellType: GAS  
  * WellStatus: OR  
  * OrphanDate: 2022-05-03  
  * WellName: BLACKLEDGE  
  * Operator: HILL RESOURCES INC (6823)  
  * County: ALFALFA (3)  
  * Coordinates: (-98.237534, 36.820229)  
  * Location: Sec 14, T27N, R10W, NE/SE

**2\. STFD Well List (stfd-well-list 2025-09-04.csv)**

* **Rows:** 2,679  
* **Columns:** 26  
* **Key fields:**  
  * API: Unique well identifier  
  * WellType: Oil, Gas, etc.  
  * WellStatus: STFD (State Funded / Statewide Tracking for Financial Distress)  
  * WellName / WellNumber  
  * OperatorName / OperatorNumber  
  * IncidentNo: Tracking number (not present in Orphan file)  
  * X, Y: Geographic coordinates (longitude, latitude)  
  * CountyName, CountyNo  
  * Survey details: Sec, Township, TownshipDir, Range, RangeDir, PM  
  * Location breakdowns: Quarter, QuarterQuarter, … down to QuarterQuarterQuarterQuarter  
  * Footage details: FootageNS, NS, FootageEW, EW  
* **Example entry (simplified):**  
  * API: 35003201560000  
  * WellType: GAS  
  * WellStatus: STFD  
  * WellName: KEPHART  
  * Operator: RENEGADE OIL AND GAS LLC (24332)  
  * IncidentNo: 18522OGDO20698  
  * County: ALFALFA (3)  
  * Coordinates: (-98.401104, 36.612164)  
  * Location: Sec 29, T25N, R11W, SE/C

**Key Differences**

* **Orphan list** has OrphanDate, no IncidentNo.  
* **STFD list** has IncidentNo, no OrphanDate.  
* Both contain detailed location, operator, and well identification data.  
* Orphan dataset is much larger (19k wells vs \~2.7k).

