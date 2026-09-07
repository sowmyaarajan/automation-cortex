# Living SOP: HR_OnboardingOrchestrator

**Intent.** Creates Active Directory accounts and processes HR approvals for new hires using data from an Excel template.

**Applications touched.** ActiveDirectory, Browser, Excel
**Capability tags.** queue_producer, queue_consumer, hitl_form_task, hitl_approval_gate, browser_automation, ad_provisioning
**Failure modes handled.** ui:SelectorNotFoundException
**Human-in-the-loop touchpoints.** 3

> This SOP is generated from the automation's actual XAML and refreshes on every run.

## What this bot does

This bot triggers when a new hire item appears in a queue. It retrieves the onboarding template, pauses for HR approval, and then attempts to create an Active Directory account by entering the hire's details into the portal. If the account creation fails due to a missing UI element, it escalates the issue; if approved, it notifies the manager and queues a laptop request, otherwise it logs a rejection.

---

## Workflow: `Main.xaml`
1. `GetTransactionItem` — Get New Hire from Queue
2. `InvokeWorkflowFile` — Read Onboarding Template
3. `CreateFormTask` — HR Approval Gate
4. `WaitForFormTaskAndResume` — Wait for Approval
5. `OpenBrowser` — Open AD Portal
6. `TypeInto` — First Name
7. `TypeInto` — Last Name
8. `Click` — Create Account
9. `CreateFormTask` — Escalate
10. `InvokeWorkflowFile` — Notify Manager
11. `AddQueueItem` — Push Laptop Request
12. `LogMessage` — Onboarding rejected by HR

---
_Last updated from run window ending 2026-07-08T09:00:00Z._