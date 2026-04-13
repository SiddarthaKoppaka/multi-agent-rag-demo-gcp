# Google Cloud Platform — Committed Use Discount Agreement
**Contract Reference:** GCP-CUD-ACME-2025-0047  
**Billing Account:** 01A2B3-C4D5E6-F7G8H9  
**Customer:** Acme Corp, Inc.  
**Google Account Manager:** Jennifer Wu (j.wu@google.com)  
**Contract Start Date:** March 1, 2025  
**Contract End Date:** February 28, 2026 (1-Year Term)  
**Renewal Date:** December 1, 2025 (90-day notice required to cancel or modify)  

---

## 1. Commitment Summary

Acme Corp has entered into the following resource-based Committed Use Discount commitments for the contract term defined above.

| Commitment ID | Resource Type | Region | vCPUs | Memory (GB) | Monthly Commitment (USD) | Annual Total (USD) | Discount Rate |
|---------------|--------------|--------|-------|-------------|-------------------------|--------------------|---------------|
| CUD-001 | N2 Standard | us-central1 | 64 | 256 | $4,100 | $49,200 | 37% |
| CUD-002 | N2 Standard | us-east1 | 32 | 128 | $2,050 | $24,600 | 37% |
| CUD-003 | C2 Compute-Optimized | us-central1 | 16 | 64 | $1,890 | $22,680 | 57% |
| CUD-004 | Memory-Optimized M1 | us-central1 | 8 | 208 | $1,420 | $17,040 | 28% |
| CUD-005 | GPU (NVIDIA T4) | us-central1 | 4 | 15 | $680 | $8,160 | 15% |

**Total Monthly Commitment: $10,140 USD**  
**Total Annual Commitment: $121,680 USD**  

---

## 2. Payment Terms

### 2.1 Billing Cycle
Committed Use Discount charges are billed monthly in arrears. Invoices are issued on the first business day of each calendar month for the prior month's commitment charges. Payment is due **Net 30** from invoice date.

### 2.2 Upfront vs. Monthly Payment
This agreement uses **monthly payment** structure. No upfront payment was made. Acme Corp is billed $10,140 per month regardless of actual resource utilization against the commitment.

### 2.3 Currency
All charges are denominated in **US Dollars (USD)**. Exchange rate fluctuations do not apply.

### 2.4 Late Payment Penalty
Payments received more than 30 days past the invoice due date will incur a late fee of **1.5% per month** on the outstanding balance. Payments more than 60 days overdue may result in suspension of GCP services.

---

## 3. Commitment Utilization & Overage

### 3.1 Under-Utilization
If Acme Corp's actual resource usage falls below the committed amounts in any month, Acme Corp is still charged the full monthly commitment amount. **There are no refunds or credits for under-utilized commitments.**

As of Q1 2026, utilization tracking shows:
- CUD-001 (N2 us-central1): 94% utilized — compliant.
- CUD-002 (N2 us-east1): 71% utilized — under-utilized. Monthly waste: ~$594.
- CUD-003 (C2 us-central1): 88% utilized — compliant.
- CUD-004 (M1 us-central1): 52% utilized — significantly under-utilized. Monthly waste: ~$682.
- CUD-005 (T4 GPU): 103% utilized — over-commitment, overage billed at on-demand rate.

**Total monthly waste from under-utilized CUDs: approximately $1,276.**

### 3.2 Over-Utilization (Overage)
Resource usage exceeding the committed amounts is billed at standard **on-demand pricing**. Sustained Use Discounts (SUDs) still apply to on-demand usage where eligible. Overages do not adjust or extend the commitment.

### 3.3 CUD Sharing
CUD discounts apply at the **billing account level**, not the project level. All projects under billing account `01A2B3-C4D5E6-F7G8H9` share the benefit of CUD discounts proportionally based on eligible usage.

---

## 4. Renewal & Cancellation Terms

### 4.1 Renewal
This agreement **auto-renews** for an identical 1-year term unless Acme Corp provides written cancellation or modification notice to Google no later than **December 1, 2025** (90 days before contract end). The renewal notice must be sent to gcp-contracts@google.com and copied to the assigned Account Manager.

**Important:** The renewal deadline for the current contract is December 1, 2025. As of the current date (Q1 2026), this contract has already been auto-renewed for the period March 1, 2026 – February 28, 2027 at the same terms, as no cancellation notice was received.

### 4.2 Modification
Committed Use Discounts **cannot be canceled or reduced** once purchased. Acme Corp may purchase additional CUD commitments at any time. Modifications to resource type or region require purchase of a new commitment; existing commitments cannot be transferred.

### 4.3 Early Termination
There is no early termination option for resource-based CUDs. In the event of account closure, all outstanding commitment charges for the remaining contract term become immediately due and payable.

---

## 5. Applicable Discounts Summary

| Discount Type | Description | Applicability |
|---------------|-------------|---------------|
| CUD Resource-Based | Discount on committed vCPU/memory resource hours | Applied automatically to eligible Compute Engine usage |
| Sustained Use Discount (SUD) | Automatic discount for VMs running >25% of month | Applied to on-demand Compute Engine usage not covered by CUD |
| Spend-Based CUD | Not applicable to this agreement | N/A |
| Free Tier | First 720 hours of f1-micro per month | Applies across all projects |
| Networking Egress | No discount; standard pricing applies | Billed separately |

---

## 6. Penalties & SLA Credits

### 6.1 Google Service Availability SLA
Google guarantees 99.99% monthly uptime for covered services. In the event of an outage attributable to Google infrastructure:
- 10–25% downtime in a month: 25% credit on affected service charges.
- 25–50% downtime: 50% credit.
- Over 50% downtime: 100% credit.

Credits are applied to the next billing cycle and do not exceed the monthly charge for the affected service.

### 6.2 Credits Do Not Apply To
- Downtime caused by Acme Corp configurations, custom software, or third-party services.
- Scheduled maintenance windows communicated 72 hours in advance.
- Force majeure events.

---

## 7. Data Governance & Compliance

All data processed under this agreement is subject to Google Cloud's Data Processing Addendum (DPA) and the Google Cloud Terms of Service. Acme Corp retains ownership of all customer data. Google does not use customer data to train AI/ML models without explicit written consent.

Acme Corp is responsible for compliance with applicable data residency regulations. Data processed in `us-central1` and `us-east1` regions remains within the United States.

---

## 8. Governing Law

This agreement is governed by the laws of the State of Delaware, USA. Any disputes shall be resolved through binding arbitration in San Jose, California.

---

## 9. Signature Block

| Party | Name | Title | Date Signed |
|-------|------|-------|-------------|
| Acme Corp | David Okafor | VP Engineering | Feb 14, 2025 |
| Acme Corp | Sandra Lin | CFO | Feb 14, 2025 |
| Google Cloud | Jennifer Wu | Account Manager | Feb 17, 2025 |
