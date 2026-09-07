# Living SOP: Shared_Utilities

**Intent.** Sends an email via Outlook with data from an Excel file and SAP.

**Applications touched.** Excel, Outlook, SAP
**Capability tags.** sap_ui_automation, excel_ingest, email_send, library

> This SOP is generated from the automation's actual XAML and refreshes on every run.

## What this bot does

This bot begins by sending an email via Outlook, then opens an Excel workbook to read data from a specified range. It proceeds to launch SAP Logon, selects the target system, enters the provided username and password, and logs into the SAP application. No specific failure handling is implemented in this workflow.

---

## Workflow: `EmailSender.xaml`
1. `SendOutlookMail` — Send Email

## Workflow: `ExcelReader.xaml`
1. `ExcelApplicationScope` — Open Workbook
2. `ReadRange` — Read Range

## Workflow: `SAPLogin.xaml`
1. `OpenApplication` — Launch SAP Logon
2. `Click` — Select System
3. `TypeInto` — Enter Username
4. `TypeInto` — Enter Password
5. `Click` — Click Logon

---
_Last updated from run window ending 2026-07-08T09:00:00Z._