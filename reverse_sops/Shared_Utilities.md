# Reverse SOP (Human Fallback): Shared_Utilities

**Intent.** Sends an email via Outlook with data from an Excel file and SAP.

**Applications touched.** Excel, Outlook, SAP
**Capability tags.** sap_ui_automation, excel_ingest, email_send, library

> ⚠️ Use this procedure if the bot is unavailable. Steps are written for a human operator.

## Overview (for the human operator)

If the automated system stops working, you will need to do these three main things in order. First, send an email to the correct person using Outlook. Next, open a specific Excel file and look up the information inside it. Finally, log into the SAP system by launching it, choosing the right server, and entering the username and password.

---

## Workflow: `EmailSender.xaml`
1. Compose and send an email (subject: [in_Subject])

## Workflow: `ExcelReader.xaml`
1. Open the Excel workbook: [in_Path]
2. Read the sheet: [in_SheetName]

## Workflow: `SAPLogin.xaml`
1. Launch saplogon.exe
2. Click: Select System
3. Type the value into the field labelled: Enter Username
4. Type the value into the field labelled: Enter Password
5. Click: Click Logon

---
_Last updated from run window ending 2026-07-08T09:00:00Z._