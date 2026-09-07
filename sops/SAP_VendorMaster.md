# Living SOP: SAP_VendorMaster

**Intent.** Creates or updates vendor records in SAP by entering data from an Excel file.

**Applications touched.** Excel, SAP
**Capability tags.** sap_vendor_master, sap_ui_automation, excel_ingest, multi_exception_handling
**Failure modes handled.** System.Exception, ui:SelectorNotFoundException

> This SOP is generated from the automation's actual XAML and refreshes on every run.

## What this bot does

This bot reads vendor details from an Excel file, logs into SAP, and navigates to transaction XK02 to update payment terms for each vendor. It enters the vendor ID, modifies the payment terms field, and saves the record. If the bot fails to find a required SAP field or encounters another system error, it logs the specific failure and continues processing the remaining rows in the file.

---

## Workflow: `Main.xaml`
1. `ExcelApplicationScope` — Open Vendor Excel
2. `ReadRange` — Read Vendor Rows
3. `InvokeWorkflowFile` — Login to SAP
4. `TypeInto` — Open XK02
5. `TypeInto` — Enter Vendor ID
6. `Click` — Continue
7. `TypeInto` — Update Payment Terms
8. `Click` — Save
9. `LogMessage` — SAP selector missing for vendor row
10. `LogMessage` — Row failed

## Workflow: `Workflows/SAPLogin.xaml`
1. `OpenApplication` — Launch SAP Logon
2. `Click` — Select System
3. `TypeInto` — Enter Username
4. `TypeInto` — Enter Password
5. `Click` — Click Logon

---
_Last updated from run window ending 2026-07-08T09:00:00Z._