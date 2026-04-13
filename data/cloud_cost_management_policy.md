# Acme Corp — Cloud Cost Management & FinOps Policy
**Document ID:** FINOPS-POL-001  
**Version:** 2.4  
**Effective Date:** January 1, 2026  
**Owner:** FinOps Center of Excellence (CoE)  
**Review Cadence:** Quarterly  

---

## 1. Purpose & Scope

This policy establishes the financial governance rules for all Google Cloud Platform (GCP) usage across Acme Corp. It applies to all engineering teams, business units, and contractors that provision or consume GCP resources under the corporate billing account `01A2B3-C4D5E6-F7G8H9`.

Failure to comply with this policy may result in resource suspension, escalation to departmental VPs, and mandatory cost remediation plans.

---

## 2. Budget Thresholds & Approval Requirements

### 2.1 Monthly Spend Limits by Team

| Team | Monthly Budget (USD) | Alert at 80% | Hard Cap |
|------|---------------------|--------------|----------|
| Platform Engineering | $12,000 | $9,600 | $14,400 |
| Data & Analytics | $8,500 | $6,800 | $10,200 |
| ML & AI | $15,000 | $12,000 | $18,000 |
| Backend Services | $6,000 | $4,800 | $7,200 |
| Frontend & Mobile | $2,000 | $1,600 | $2,400 |
| Security & Compliance | $3,500 | $2,800 | $4,200 |

### 2.2 Single Purchase Approval Thresholds

- **Under $500:** Engineer can self-approve. Must apply required tags within 24 hours.
- **$500 – $2,499:** Team Lead approval required within 48 hours of provisioning.
- **$2,500 – $9,999:** Engineering Manager + FinOps CoE joint approval required before provisioning.
- **$10,000 and above:** VP Engineering + CFO approval required. Minimum 5-business-day lead time. A written justification and 12-month cost projection must accompany the request.
- **Committed Use Discounts (CUDs) over $25,000:** Board-level Finance Committee sign-off required.

### 2.3 Budget Overrun Consequences

- 100–110% of monthly budget: Automated Slack alert to team lead and FinOps CoE.
- 110–125% of monthly budget: Engineering Manager must submit a cost remediation plan within 72 hours.
- Over 125% of monthly budget: Resource provisioning freeze on non-critical services until remediation plan is approved.

---

## 3. Mandatory Resource Tagging Policy

All GCP resources must carry the following labels at time of provisioning. Resources without mandatory tags will be flagged in weekly compliance reports and may be subject to forced termination after a 7-day grace period.

### 3.1 Required Labels

| Label Key | Description | Allowed Values / Format |
|-----------|-------------|------------------------|
| `team` | Owning team | `platform`, `data-analytics`, `ml-ai`, `backend`, `frontend`, `security` |
| `environment` | Deployment environment | `prod`, `staging`, `dev`, `sandbox` |
| `cost-center` | Internal cost center code | e.g., `CC-1042`, `CC-2017` |
| `project-id` | Internal project identifier | e.g., `PROJ-0091`, `PROJ-0134` |
| `owner-email` | Individual responsible | Valid `@acmecorp.com` email |
| `created-date` | ISO 8601 creation date | `YYYY-MM-DD` |

### 3.2 Optional but Recommended Labels

| Label Key | Description |
|-----------|-------------|
| `service-name` | Microservice or application name |
| `data-classification` | `public`, `internal`, `confidential`, `restricted` |
| `expiry-date` | For temporary/sandbox resources |
| `jira-ticket` | Linked JIRA issue for provisioning request |

### 3.3 Tagging Compliance Targets

- **Target:** 95% of all active resources tagged with all 6 required labels.
- **Measurement:** Automated weekly scan via Cloud Asset Inventory.
- **Current company-wide compliance rate:** 81% (as of Q1 2026).

---

## 4. Idle Resource Policy

### 4.1 Definition of Idle

A resource is considered **idle** if it meets any of the following:

- **Compute Engine VM:** CPU utilization < 5% averaged over 14 consecutive days.
- **Cloud Run service:** Zero invocations in the past 21 days.
- **GKE Node Pool:** Average pod CPU request < 10% of capacity over 14 days.
- **Cloud Storage bucket:** Zero read/write operations in 30 days AND bucket size > 1GB.
- **AlloyDB / Cloud SQL instance:** Zero connections in 14 consecutive days.
- **Load Balancer:** Zero requests in 21 days.
- **Static IP address:** Unattached for 7 days.

### 4.2 Idle Resource Actions

1. **Day 0:** Resource flagged as idle in weekly FinOps report.
2. **Day 7:** Automated notification sent to `owner-email` tag and team lead.
3. **Day 14:** If no response, FinOps CoE will attempt to contact team via Slack.
4. **Day 21:** Resource scheduled for suspension pending team acknowledgment.
5. **Day 30:** Resource terminated unless team submits a keep-alive justification.

Cost of idle resources is tracked under the `idle_waste` cost category and included in monthly team scorecards.

---

## 5. Anomaly Detection & Spike Response

### 5.1 Anomaly Thresholds

An anomaly is flagged when spend on any single GCP service exceeds:
- **Day-over-day:** 3× the 30-day daily average for that service.
- **Week-over-week:** 2× the spend of the same 7-day period in the prior month.
- **Monthly budget burn rate:** If projected month-end spend exceeds approved budget by more than 15% before the 20th of the month.

### 5.2 Response SLA

- **P1 (>300% spike):** FinOps CoE and Engineering Manager notified within 1 hour. Root cause analysis required within 24 hours.
- **P2 (150–300% spike):** Team lead notified within 4 hours. Investigation within 48 hours.
- **P3 (115–150% spike):** Logged in weekly report. Team reviews at next sprint planning.

---

## 6. Committed Use Discounts (CUD) & Sustained Use Policy

### 6.1 CUD Eligibility

Teams running stable, predictable workloads exceeding $3,000/month on Compute Engine or Cloud Run are required to evaluate 1-year CUD commitments. FinOps CoE will provide quarterly CUD recommendations.

### 6.2 CUD Coverage Target

- **Minimum CUD coverage:** 60% of eligible compute spend must be covered by active CUD commitments.
- **Optimal target:** 80% CUD coverage to maximize discount without over-commitment.
- **Current coverage:** 67% (Q1 2026).

### 6.3 CUD Termination

CUDs cannot be canceled once purchased. Teams that are dissolved or have projects cancelled must transfer CUD coverage to the FinOps CoE pool for redistribution.

---

## 7. Chargeback & Showback

### 7.1 Showback Reports

Monthly showback reports are published to all team leads by the 5th of each following month. Reports include:
- Total spend by service, project, and environment.
- Budget utilization percentage.
- Idle resource cost.
- Tagging compliance score.
- Month-over-month variance.

### 7.2 Chargeback Model

Effective Q3 2026, Acme Corp will transition from showback to chargeback for the following teams: Platform Engineering, Data & Analytics, ML & AI. Remaining teams will remain on showback model until Q1 2027.

Under chargeback, cloud costs will be deducted directly from each team's departmental budget, transferring full financial ownership to engineering leadership.

---

## 8. Sandbox & Development Environment Controls

- Sandbox resources must carry `environment: sandbox` label.
- Sandbox resources are automatically terminated after **72 hours** unless a `expiry-date` label extending the lifecycle is applied.
- Sandbox spend is capped at **$200/engineer/month**.
- No production data may be loaded into sandbox environments.

---

## 9. Escalation Contacts

| Role | Name | Email |
|------|------|-------|
| FinOps CoE Lead | Priya Mehta | p.mehta@acmecorp.com |
| VP Engineering | David Okafor | d.okafor@acmecorp.com |
| CFO | Sandra Lin | s.lin@acmecorp.com |
| Cloud Architecture | Raj Patel | r.patel@acmecorp.com |

---

## 10. Policy Review History

| Version | Date | Changes |
|---------|------|---------|
| 2.4 | Jan 2026 | Updated CUD coverage targets; added Cloud Run idle thresholds |
| 2.3 | Oct 2025 | Added chargeback rollout timeline for Q3 2026 |
| 2.2 | Jul 2025 | Revised single-purchase thresholds; added board approval for CUDs >$25K |
| 2.1 | Apr 2025 | Added mandatory `created-date` label requirement |
| 2.0 | Jan 2025 | Major rewrite; introduced idle resource termination SLA |
