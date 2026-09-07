# Reverse SOP (Human Fallback): HR_OnboardingOrchestrator

**Intent.** Creates Active Directory accounts and processes HR approvals for new hires using data from an Excel template.

**Applications touched.** ActiveDirectory, Browser, Excel
**Capability tags.** queue_producer, queue_consumer, hitl_form_task, hitl_approval_gate, browser_automation, ad_provisioning
**Failure modes handled.** ui:SelectorNotFoundException
**Human-in-the-loop touchpoints.** 3

> ⚠️ Use this procedure if the bot is unavailable. Steps are written for a human operator.

## Overview (for the human operator)

You need to help a new employee get set up. First, you'll get their details from a list and check the instructions. Then, you must wait for HR to approve the setup. After approval, you will log into the company’s system to create their login account by entering their first and last name. Finally, you’ll let their manager know and request a laptop for them. If HR says no, you’ll stop and note that the setup was not approved.

---

## Workflow: `Main.xaml`
1. Pick the next item from the NewHires queue
2. Perform the sub-procedure documented in ..\Shared_Utilities\ExcelReader.xaml
3. Wait for human input: Approve New Hire AD Account
4. Continue once the human task is completed
5. Open a browser and navigate to https://ad.contoso.com/users/new
6. Type the value into the field labelled: First Name
7. Type the value into the field labelled: Last Name
8. Click: Create Account
9. Wait for human input: AD Portal Unavailable - Manual Creation
10. Perform the sub-procedure documented in ..\Shared_Utilities\EmailSender.xaml
11. Push the result into the LaptopRequests queue
12. Note in the log: Onboarding rejected by HR

---
_Last updated from run window ending 2026-07-08T09:00:00Z._