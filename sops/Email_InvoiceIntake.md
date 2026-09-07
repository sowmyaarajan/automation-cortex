# Living SOP: Email_InvoiceIntake

**Intent.** Extracts vendor, amount, and date from invoice attachments in Outlook emails for processing.

**Applications touched.** Outlook
**Capability tags.** document_extraction, document_understanding, hitl_validation, document_classification, queue_producer, email_ingest, hitl_form_task, multi_exception_handling
**Failure modes handled.** System.Exception, ui:DocumentExtractionException
**Human-in-the-loop touchpoints.** 2

> This SOP is generated from the automation's actual XAML and refreshes on every run.

## What this bot does

This bot monitors a designated Outlook inbox for new AP emails, saves any attachments, and processes them as invoices. It uses document understanding to classify and extract key fields like vendor, amount, and date, then presents the data for human validation before pushing it to an SAP queue. If extraction fails, it escalates the task to a human and logs the failure, otherwise it marks the original email as read.

---

## Workflow: `Main.xaml`
1. `GetOutlookMailMessages` — Fetch New AP Emails
2. `SaveAttachments` — Save Attachments
3. `DocumentUnderstandingScope` — Extract Invoice Fields
4. `DigitizeDocument` — Digitize
5. `ClassifyDocumentScope` — Classify Invoice vs Other
6. `DataExtractionScope` — Extract Vendor/Amount/Date
7. `MachineLearningExtractor` — ML Extractor
8. `PresentValidationStation` — Validation Station HITL
9. `AddQueueItem` — Push to SAP Queue
10. `MarkAsRead` — Mark Email Read
11. `CreateFormTask` — Escalate to Human
12. `LogMessage` — Email processing failed

---
_Last updated from run window ending 2026-07-08T09:00:00Z._