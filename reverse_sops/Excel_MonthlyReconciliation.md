# Reverse SOP (Human Fallback): Excel_MonthlyReconciliation

**Intent.** Compares SAP general ledger data with budget figures in Excel to identify and report discrepancies.

**Applications touched.** Excel, Outlook
**Capability tags.** excel_ingest, excel_output, email_send
**Failure modes handled.** System.IO.IOException

> ⚠️ Use this procedure if the bot is unavailable. Steps are written for a human operator.

## Overview (for the human operator)

If the automated report fails, you will need to manually compare the two Excel files yourself. First, open the main financial report and the budget file side by side. Look for any numbers that don’t match between them, and note those differences in a new sheet. Finally, email that list of discrepancies to the finance team.

---

## Workflow: `Main.xaml`
1. Open the Excel workbook: Input\SAP_GL_Export.xlsx
2. Read the sheet: GL
3. Open the Excel workbook: Input\Budget.xlsx
4. Read the sheet: Budget
5. Run the embedded VB.NET calculation
6. Open the Excel workbook: Output\Discrepancies.xlsx
7. Write results to the sheet: Findings
8. Compose and send an email (subject: Monthly Reconciliation - [DateTime.Now.ToString("MMM yyyy")])
9. Note in the log: Output file locked - retrying next run

---
_Last updated from run window ending 2026-07-08T09:00:00Z._