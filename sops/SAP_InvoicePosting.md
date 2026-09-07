# Living SOP: SAP_InvoicePosting

**Intent.** Posts vendor invoices from email into SAP by entering transaction data and handling exceptions.

**Applications touched.** Outlook, SAP
**Capability tags.** queue_consumer, sap_posting, sap_ui_automation, email_send, hitl_form_task, multi_exception_handling
**Failure modes handled.** ui:BusinessRuleException, ui:SelectorNotFoundException
**Human-in-the-loop touchpoints.** 1

> This SOP is generated from the automation's actual XAML and refreshes on every run.

## What this bot does

This bot retrieves an invoice from a queue, logs into SAP, and posts the invoice using transaction FB60 by entering the vendor ID and amount. If the SAP interface is unavailable, it escalates for human review; if a duplicate invoice is detected, it logs the issue and notifies the accounts payable team via email. On failure, it retries the posting step and handles specific UI exceptions before escalating unresolved errors.

---

## Workflow: `Main.xaml`
1. `GetTransactionItem` — Get Invoice from Queue
2. `InvokeWorkflowFile` — Login to SAP
3. `TypeInto` — Open FB60 Transaction
4. `Click` — Continue
5. `TypeInto` — Enter Vendor ID
6. `TypeInto` — Enter Amount
7. `Click` — Post
8. `LogMessage` — SAP GUI selector missing - escalating
9. `CreateFormTask` — Human Review
10. `LogMessage` — Duplicate vendor invoice detected
11. `SetTransactionStatus` — SetTransactionStatus
12. `InvokeWorkflowFile` — Notify AP Team

## Workflow: `Workflows/NotifyAP.xaml`
1. `SendOutlookMail` — Send Confirmation Email

## Workflow: `Workflows/SAPLogin.xaml`
1. `OpenApplication` — Launch SAP Logon
2. `Click` — Select System
3. `TypeInto` — Enter Username
4. `TypeInto` — Enter Password
5. `Click` — Click Logon

---
_Last updated from run window ending 2026-07-08T09:00:00Z._