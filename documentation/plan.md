# 🏍️ DC Financing Corporation – Financing & Inventory Management System (Django Edition)

> **Scope:** Internal management system for motorcycle dealership/KASA operations.
> Roles: **Admin** and **Finance Officer**.
> Includes financing workflow, payments, rule-based risk scoring, repossession management, inventory control, user management, audit trail, and centralized archive management.

---

## 1) Concept Overview

**Goal:** Centralize dealership financing and inventory operations with transparent tracking, automated schedules, and complete auditability.

**Primary Actors**

* **Admin:** Superuser; full system access. Can manage users, inventory, global settings, and audit logs.
* **Finance Officer:** Handles loan applications, payments, risk assessments, and repossession cases.

**Core Modules**

1. **Dashboard** – KPI and analytics per role
2. **Loans** – Application wizard, approval, and schedule generation
3. **Payments** – Due tracking, payment recording, and collection analytics
4. **Risk Scoring** – Rule-based evaluation with adjustable thresholds
5. **Repossession** – Manage at-risk accounts and recovery process
6. **Inventory** – CRUD for motorcycle units (Admin full control; Finance read-only)
7. **Users** – Role-based user management
8. **Audit Trail** – Complete record of user and system actions
9. **Archives** – Centralized archive for all modules
10. **Reports** – Exportable data (PDF/Excel)

---

## 2) UX: Pages & Components

DC Financing Corporation UI follows **Atomic Design Principles**:

* **Atoms:** Buttons, inputs, badges, modals
* **Molecules:** Form groups, cards, tables
* **Organisms:** Dashboards, wizards, reports

> Each module’s templates and components will follow this structure for reusability and clean scalability.

### Example Directory

```
templates/
  components/
    atoms/
    molecules/
    organisms/
  pages/
  layouts/
```

---

### A. Finance Dashboard

* **Cards:** Total Loans • Approved • Pending • Overdue • Total Collected (Month)
* **Recent Applications Table:** Applicant | Motor | Status | Date
* **Alerts Section:** Risk summary (Low/Med/High), linked to repossession cases

---

### B. Loan Application Wizard

Multi-step Django FormView / HTMX-powered:

1. **Personal Info** – Basic applicant details
2. **Employment Info** – Job, income, years employed
3. **Motor Info** – Select from available inventory; auto-compute monthly
4. **Documents Upload** – Multiple files (proofs, IDs, etc.) → stored via CDN

**Actions:** Save Draft • Submit • Approve/Reject

---

### C. Payments Page

* **Analytics:** Total Collected • Pending Amount • Overdue Accounts • Collection Rate
* **Table:** Loan | Customer | Due Date | Paid Date | Amount Due | Status
* **Auto Rules:** Overdue if `today > due_date`; updates risk score dynamically.

---

### D. Risk Scoring (Rule-Based)

* **Analytics:** Distribution (Low/Med/High), Factor Impacts
* **Cards:** Applicant | Risk Score | DTI | Income | Status | Insights

**Formula Example:**

```python
risk_score = base \
    + (missed_payments * 15) \
    + min((loan_amount / max(monthly_income, 1)) * 10, 30) \
    - min(credit_score / 20, 25) \
    + employment_penalty
```

Thresholds adjustable in Admin settings.

---

### E. Repossession Management

* **Cards:** Total At Risk • Critical Cases • Recovery Rate
* **Flow:** Overdue → Warning → Active Case → Reminder → Recovered/Closed → Archive

---

## 3) Admin UX

* **Dashboard:** Combined finance + inventory + audit KPIs
* **Inventory:** CRUD motorcycles with images (CDN-hosted)
* **Users:** Manage staff, assign roles, suspend/reactivate
* **Audit Trail:** Search by date/user/module/action; export to PDF/CSV
* **Settings:** Interest rates, risk thresholds, notifications (Phase 2)

---

## 4) Data Model (Django ORM)

| Table             | Description                                      |      |         |       |          |
| ----------------- | ------------------------------------------------ | ---- | ------- | ----- | -------- |
| `User`            | Built from Django Auth (roles: admin, finance)   |      |         |       |          |
| `AuditLog`        | Tracks actions (`ADD                             | EDIT | ARCHIVE | LOGIN | LOGOUT`) |
| `Motor`           | Motor info (brand, model, price, image via CDN)  |      |         |       |          |
| `FinancingTerm`   | Term years + interest rate                       |      |         |       |          |
| `LoanApplication` | Applicant info, linked to Motor, Terms, and User |      |         |       |          |
| `LoanDocument`    | Uploaded files linked to a loan (CDN URLs)       |      |         |       |          |
| `Payment`         | Monthly dues with status tracking                |      |         |       |          |
| `RiskAssessment`  | Computed risk data per loan                      |      |         |       |          |
| `Repossession`    | Active recovery cases                            |      |         |       |          |
| `Archive`         | Snapshot of any record (polymorphic reference)   |      |         |       |          |

---

## 5) Business Workflow

**Loan Lifecycle**

1. Create Application → `pending`
2. Upload Docs → validate
3. Compute Risk Score → save
4. Approve/Reject

   * Approve → Generate N `Payment` entries
   * Reject → move to archive
5. Payment updates → Auto-flag overdue
6. Complete → all payments done

**Audit Policy**

* Every CRUD/auth event logs to `AuditLog`
* Description is human-readable
* Sensitive data excluded

**Archive Policy**

* Any module can be archived → JSON snapshot saved
* Restore = rebuild record from snapshot

---

## 6) Computations

**Installment Calculation**

```python
total_interest = principal * rate * term_years
total_amount = principal + total_interest
monthly_payment = round(total_amount / (term_years * 12), 2)
```

---

## 7) Routes & Views (Django Style)

### Auth

* `/login/` • `/logout/`

### Users

* `/users/` • `/users/create/` • `/users/<id>/edit/` • `/users/<id>/suspend/`

### Inventory

* `/inventory/` • `/inventory/create/` • `/inventory/<id>/edit/`

### Loans

* `/loans/` • `/loans/new/` • `/loans/<id>/approve/` • `/loans/<id>/reject/`
* `/loans/<id>/documents/` • `/loans/<id>/payments/`

### Payments

* `/payments/` • `/payments/<id>/record/`

### Risk

* `/risk/summary/` • `/risk/recompute/<loan_id>/`

### Repossession

* `/repos/` • `/repos/<id>/remind/` • `/repos/<id>/close/`

### Audit & Archive

* `/audits/` • `/archives/` • `/archives/restore/<id>/`

---

## 8) Permissions Matrix

| Feature                 |    Admin    |    Finance   |
| ----------------------- | :---------: | :----------: |
| Dashboard               |      ✅      |       ✅      |
| Loans                   |      ✅      |       ✅      |
| Payments                |      ✅      |       ✅      |
| Risk                    |      ✅      |       ✅      |
| Risk Threshold Settings |      ✅      |       ❌      |
| Repossession            |      ✅      |       ✅      |
| Inventory               |      ✅      |    🔍 Read   |
| Users                   |      ✅      |       ❌      |
| Audit Logs              |      ✅      |    🔍 Read   |
| Archive                 | ✅ (restore) | Archive-only |

---

## 9) Non-Functional Requirements

* **Security:** Django Auth + JWT (optional), hashed passwords, form validation
* **Storage:** CDN-based (Cloudflare R2 / AWS S3) via `django-storages`
* **Reliability:** MySQL + transaction integrity
* **Performance:** Query optimizations + pagination
* **Auditability:** Centralized logs per module
* **Backup:** Daily DB + object storage backups

---

## 10) Tech Stack & Setup

| Layer           | Technology                            |
| --------------- | ------------------------------------- |
| **Framework**   | Django (latest LTS)                   |
| **Database**    | MySQL 8+, sqlite for testing          |
| **Frontend**    | Django Templates + TailwindCSS + HTMX |
| **Storage/CDN** | Cloudflare R2 (S3-compatible)         |
| **Reports**     | `xhtml2pdf`, `openpyxl`               |
| **Logging**     | Django Signals + custom Audit model   |

### Environment (.env)

```
DB_NAME=
DB_USER=
DB_PASSWORD=
STORAGE_ACCESS_KEY=
STORAGE_SECRET_KEY=
STORAGE_BUCKET_NAME=
STORAGE_ENDPOINT_URL=
```

---

## 11) Project Structure

```
motofinai/
  settings.py
  urls.py
  wsgi.py
  templates/
    components/
      atoms/
      molecules/
      organisms/
    pages/
    layouts/
  static/
    css/
    js/
  apps/
    auth/
    users/
    inventory/
    loans/
    payments/
    risk/
    repossession/
    audit/
    archive/
  media/  (linked to CDN)
```

---

## 12) Development Phases

1. **Models & Migrations**

   * Build all models
   * Create superuser + seed roles
2. **Auth & RBAC**

   * Role-based access via decorators/mixins
3. **Modules**

   * Inventory → Financing Terms → Loans → Payments → Risk → Repo → Archive → Reports
4. **Templates (Atomic)**

   * Reusable components per module
5. **Dashboards & Reports**
6. **Audit + Archive Integration**
7. **Deploy**

   * Configure CDN, backups, and cron jobs

---

## 13) Testing Checklist

✅ Payment schedule generation
✅ Risk score recalculation
✅ Archive + restore
✅ Audit logging on all CRUD
✅ Role permissions
✅ File upload to CDN verified

---

## 14) Notes

* Central archive table ensures full traceability.
* Risk scoring and thresholds adjustable via Admin.
* Media storage defaults to local filesystem for development; set `DEFAULT_FILE_STORAGE=storages.backends.s3boto3.S3Boto3Storage` with the provided AWS keys for CDN-backed uploads (no direct downloads).
* `USE_WHITENOISE=true` enables compressed static serving in production while tests override it for faster execution.
* Atomic template structure ensures scalability and design consistency.

