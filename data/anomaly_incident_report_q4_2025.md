# Acme Corp — Cloud Spend Anomaly & Incident Report
**Report Period:** Q4 2025 + January 2026  
**Prepared by:** FinOps CoE  
**Distribution:** Engineering Leads, VP Engineering, CFO Office  

---

## Executive Summary

This report documents all cloud cost anomalies detected, investigated, and resolved during Q4 2025 and January 2026. Three P1 incidents, two P2 incidents, and four P3 incidents were recorded. Total unplanned spend attributed to anomalies: **$41,820**.

---

## Incident Log

### INC-2025-041 — P1 | BigQuery Cost Spike (Data Analytics Team)
**Date Detected:** October 14, 2025  
**Detection Method:** Day-over-day threshold alert (>300%)  
**Affected Service:** BigQuery — Analysis Queries  
**Affected Project:** data-analytics-prod  
**Normal Daily Spend:** $92/day  
**Anomaly Day Spend:** $4,840  
**Spike Magnitude:** 5,261% above baseline  

**Root Cause:** A data pipeline job was accidentally deployed without a `WHERE` clause filter, causing a full table scan across a 342TB dataset. The query ran 47 times before it was caught, scanning approximately 16PB of data total.

**Resolution:** Pipeline job was rolled back within 4 hours of detection. `require_partition_filter = TRUE` was applied to the source table to prevent unpartitioned scans going forward. Query cost estimator checks were added to the CI/CD pipeline.

**Financial Impact:** $4,748 excess spend. FinOps CoE absorbed cost against central reserve; no team chargeback applied as root cause was tooling gap, not negligence.

**Preventive Action:** All BigQuery tables with >1TB data must now have partition filter requirements enabled. Implemented by: Nov 1, 2025.

---

### INC-2025-052 — P1 | Runaway GPU Training Job (ML & AI Team)
**Date Detected:** November 3, 2025  
**Detection Method:** Weekly budget burn rate alert (projected month-end >200% of budget)  
**Affected Service:** Compute Engine — NVIDIA A100 GPU instances  
**Affected Project:** ml-ai-prod  
**Normal Monthly GPU Spend:** $2,840  
**Anomaly Period Spend (3 days):** $18,420  

**Root Cause:** An experimental distributed training job was accidentally submitted to the production GPU cluster instead of the sandbox environment. The job spun up 24 A100 instances with no time limit set. The job ran for 71 hours before detection.

**Resolution:** Job terminated manually. GPU instance count limits were applied at the project level (maximum 8 GPU instances per project). A separate `ml-ai-sandbox` project with hard spend caps of $500/day was created.

**Financial Impact:** $18,420 excess spend. $15,580 absorbed by central FinOps reserve. ML & AI team budgeted for remaining $2,840 in November remediation plan.

**Preventive Action:** All GPU job submissions now require a `max_runtime_hours` parameter. Automated kill switches trigger if a job exceeds 24 hours without a checkpoint. Implemented by: Nov 20, 2025.

---

### INC-2025-067 — P1 | Untagged Resources Proliferation (Unknown Origin)
**Date Detected:** December 2, 2025  
**Detection Method:** Weekly tagging compliance scan  
**Affected Service:** Multiple (Compute Engine, Cloud Storage)  
**Affected Project:** untagged-project-99  
**Spend Since First Detected:** $8,240  

**Root Cause:** A contractor account was provisioned with Owner-level IAM permissions in December 2024. The contractor created multiple VMs and storage buckets without applying any required labels. The contractor's engagement ended in April 2025 but the IAM account was not revoked, and the resources were never cleaned up.

**Resolution:** Resources inventoried via Cloud Asset Inventory. VMs were found to be running at approximately 3% CPU utilization. Contractor account IAM permissions revoked. Resources scheduled for termination after 7-day review period.

**Financial Impact:** $8,240 spend over 8 months attributed to this account. Data on resources has been preserved in Cloud Storage before termination.

**Preventive Action:** Contractor IAM account lifecycle policy implemented — all contractor accounts now have a mandatory 90-day expiration. Automated audit runs monthly. Implemented by: Jan 1, 2026.

---

### INC-2025-073 — P2 | Cloud SQL Idle Instances (Backend Team)
**Date Detected:** December 10, 2025  
**Detection Method:** Idle resource scan — zero connections for 21 days  
**Affected Service:** Cloud SQL (PostgreSQL)  
**Affected Project:** backend-dev-01  
**Resource:** `orders-db-dev-IDLE`  
**Monthly Spend:** $445.70  

**Root Cause:** A development database instance was provisioned by an engineer who subsequently moved to a different team. The receiving team was unaware the instance existed. The `owner-email` label referenced an employee who had left the company 3 months prior.

**Resolution:** FinOps CoE flagged instance, contacted current backend team lead. Team confirmed the instance had no current users. Instance backed up and terminated December 17, 2025.

**Financial Impact:** $1,783 spend over 4 months. No reimbursement applied; used as a case study for the idle resource policy rollout.

**Preventive Action:** Monthly idle resource reports now sent directly to team leads. `owner-email` labels are validated against active employee directory. Implemented by: Jan 15, 2026.

---

### INC-2025-079 — P2 | Cloud Storage Egress Spike (Platform Team)
**Date Detected:** December 19, 2025  
**Detection Method:** Week-over-week alert (2× prior week spend)  
**Affected Service:** Cloud Storage — Networking Egress  
**Affected Project:** platform-prod-01  
**Normal Weekly Egress Spend:** $420  
**Anomaly Week Spend:** $1,840  

**Root Cause:** A misconfigured CDN cache policy caused cache bypass for a high-traffic API response that should have been cached. All API responses were served directly from Cloud Storage origin for 5 days.

**Resolution:** CDN cache policy corrected. Cache hit rate restored from 12% to 94%.

**Financial Impact:** $1,420 excess egress spend. Resolved within 6 hours of detection.

---

### INC-2026-003 — P3 | BigQuery Query Cost Spike (Data Analytics — January 2026)
**Date Detected:** January 22, 2026  
**Detection Method:** Monthly budget burn rate projection  
**Affected Service:** BigQuery — Analysis Queries  
**Affected Project:** data-analytics-prod  
**Normal Monthly BigQuery Query Spend:** $2,840  
**January Projected Spend:** $9,680  

**Root Cause:** Under investigation. Preliminary analysis suggests a newly onboarded analyst ran multiple exploratory queries against un-partitioned historical tables. The queries were not run through the cost estimation workflow that was mandated after INC-2025-041. Total data scanned: approximately 342TB additional in January.

**Status:** OPEN. Team has been notified. Mandatory query cost estimation training scheduled for data analytics team in February 2026.

**Estimated Financial Impact:** $6,840 excess spend for January 2026.

---

## Trend Summary — Anomaly Categories

| Category | Q4 2025 Count | Jan 2026 Count | Total Excess Spend |
|----------|---------------|----------------|--------------------|
| Runaway compute/training jobs | 1 | 0 | $18,420 |
| Query inefficiency (BigQuery) | 1 | 1 | $11,588 |
| Idle/untagged resources | 2 | 0 | $10,023 |
| Egress/networking | 1 | 0 | $1,420 |
| **Total** | **5** | **1** | **$41,451** |

---

## Recommendations for Q2 2026

1. **Mandatory query cost preview:** Enforce pre-execution cost estimation for all BigQuery queries scanning >100GB. Block queries exceeding $500 without manager approval.
2. **GPU job governance:** Extend `max_runtime_hours` enforcement to all ML environments, not just production.
3. **Contractor lifecycle automation:** Automate contractor account deprovisioning via HR system integration (target: Q2 2026).
4. **Idle resource auto-remediation:** Move from notification-based to automated shutdown for idle resources older than 30 days with no `keep-alive` justification filed.
