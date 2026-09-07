# Reverse SOP (Human Fallback): SAP_InvoicePosting

**Intent.** Posts vendor invoices from email into SAP by entering transaction data and handling exceptions.

**Applications touched.** Outlook, SAP
**Capability tags.** queue_consumer, sap_posting, sap_ui_automation, email_send, hitl_form_task, multi_exception_handling
**Failure modes handled.** ui:BusinessRuleException, ui:SelectorNotFoundException
**Human-in-the-loop touchpoints.** 1

> ⚠️ Use this procedure if the bot is unavailable. Steps are written for a human operator.

## Overview (for the human operator)

You need to log into the company system, enter an invoice from a specific vendor, and then send a confirmation email. First, open the SAP program on your computer and sign in. Then, find the invoice entry screen, type in the vendor’s number and the amount, and finalize the posting. Finally, go to your email and send a quick note to the accounts payable team to let them know it’s done.

---

## Workflow: `Main.xaml`
1. Pick the next item from the InvoicesToPost queue
2. Perform the sub-procedure documented in Workflows\SAPLogin.xaml
3. Type the value into the field labelled: Open FB60 Transaction
4. Click: Continue
5. Type the value into the field labelled: Enter Vendor ID
6. Type the value into the field labelled: Enter Amount
7. Click: Post
8. Note in the log: SAP GUI selector missing - escalating
9. Wait for human input: SAP Invoice Manual Review
10. Note in the log: Duplicate vendor invoice detected
11. Mark the current queue item as failed with a business exception
12. Perform the sub-procedure documented in Workflows\NotifyAP.xaml

## Workflow: `Workflows/NotifyAP.xaml`
1. Compose and send an email (subject: Invoice Posted)

## Workflow: `Workflows/SAPLogin.xaml`
1. Launch saplogon.exe
2. Click: Select System
3. Type the value into the field labelled: Enter Username
4. Type the value into the field labelled: Enter Password
5. Click: Click Logon

---
_Last updated from run window ending 2026-07-08T09:00:00Z._