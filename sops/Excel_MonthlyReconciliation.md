# Living SOP: Excel_MonthlyReconciliation

**Intent.** Compares SAP general ledger data with budget figures in Excel to identify and report discrepancies.

**Applications touched.** Excel, Outlook
**Capability tags.** excel_ingest, excel_output, email_send
**Failure modes handled.** System.IO.IOException

> This SOP is generated from the automation's actual XAML and refreshes on every run.

## What this bot does

This bot triggers monthly to reconcile SAP general ledger data against budget figures. It opens two Excel files, reads the data, computes discrepancies, and writes the findings to a new report. Once complete, it emails the results to controllers; if the output file is locked, it logs a failure message and retries on the next scheduled run.

---

## Workflow: `Main.xaml`
1. `ExcelApplicationScope` — Open SAP GL Export
2. `ReadRange` — Read GL Data
3. `ExcelApplicationScope` — Open Budget
4. `ReadRange` — Read Budget
5. `InvokeCode` — Compute Discrepancies
6. `ExcelApplicationScope` — Write Discrepancies
7. `WriteRange` — Write Findings
8. `SendOutlookMail` — Email Controllers
9. `LogMessage` — Output file locked - retrying next run

---
_Last updated from run window ending 2026-07-08T09:00:00Z._