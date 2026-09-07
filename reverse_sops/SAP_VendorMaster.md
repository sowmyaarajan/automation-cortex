# Reverse SOP (Human Fallback): SAP_VendorMaster

**Intent.** Creates or updates vendor records in SAP by entering data from an Excel file.

**Applications touched.** Excel, SAP
**Capability tags.** sap_vendor_master, sap_ui_automation, excel_ingest, multi_exception_handling
**Failure modes handled.** System.Exception, ui:SelectorNotFoundException

> ⚠️ Use this procedure if the bot is unavailable. Steps are written for a human operator.

## Overview (for the human operator)

You need to update payment terms for a list of vendors in SAP. First, open the Excel file with the vendor list. Then, log into SAP, open the vendor change screen, and for each vendor, enter their ID and update their payment terms. Finally, save each change before moving to the next vendor.

---

## Workflow: `Main.xaml`
1. Open the Excel workbook: Input\VendorUpdates.xlsx
2. Read the sheet: Updates
3. Perform the sub-procedure documented in Workflows\SAPLogin.xaml
4. Type the value into the field labelled: Open XK02
5. Type the value into the field labelled: Enter Vendor ID
6. Click: Continue
7. Type the value into the field labelled: Update Payment Terms
8. Click: Save
9. Note in the log: SAP selector missing for vendor row
10. Note in the log: Row failed

## Workflow: `Workflows/SAPLogin.xaml`
1. Launch saplogon.exe
2. Click: Select System
3. Type the value into the field labelled: Enter Username
4. Type the value into the field labelled: Enter Password
5. Click: Click Logon

---
_Last updated from run window ending 2026-07-08T09:00:00Z._