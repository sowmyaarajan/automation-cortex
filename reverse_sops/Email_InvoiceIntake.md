# Reverse SOP (Human Fallback): Email_InvoiceIntake

**Intent.** Extracts vendor, amount, and date from invoice attachments in Outlook emails for processing.

**Applications touched.** Outlook
**Capability tags.** document_extraction, document_understanding, hitl_validation, document_classification, queue_producer, email_ingest, hitl_form_task, multi_exception_handling
**Failure modes handled.** System.Exception, ui:DocumentExtractionException
**Human-in-the-loop touchpoints.** 2

> ⚠️ Use this procedure if the bot is unavailable. Steps are written for a human operator.

## Overview (for the human operator)

You need to check a specific email inbox for new messages about invoices. When you find one, save any files attached to the email, and then carefully review them. Your main job is to write down the vendor's name, the total amount, and the date from each invoice, and then send that information to the team that handles payments. Finally, mark the original email as read so it doesn't get checked again.

---

## Workflow: `Main.xaml`
1. Open Outlook and review new messages in the referenced item
2. Save any email attachments to the referenced item
3. Run document understanding on the attachment
4. Digitize the document (OCR)
5. Classify the document type
6. Extract fields from the document
7. Apply the ML extractor: the referenced item
8. Open Validation Station and confirm the extracted fields
9. Push the result into the InvoicesToPost queue
10. Mark the email as read
11. Wait for human input: Manual Invoice Review Required
12. Note in the log: Email processing failed

---
_Last updated from run window ending 2026-07-08T09:00:00Z._