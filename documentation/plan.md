# MotofinAI – Financing & Inventory Management System

> **Scope:** Internal system for a motorcycle dealership/KASA. No customer portal. Roles: **Admin**, **Finance Officer**. Includes financing workflow, payments, risk scoring (rule-based), repossession management, inventory, user management, audit trail, and centralized archive table.

---

## 1) Concept Overview

**Goal:** Centralize operations for motorcycle financing and inventory with transparent tracking, automated schedules, and auditability.

**Primary Actors**

* **Admin**: Superuser. Everything Finance can do, plus **User Management**, **Inventory CRUD**, **Global Overrides**, **Audit Trail** access.
* **Finance Officer**: Handles loan applications, documents, payments, risk, and repossession.

**High-Level Modules**

1. **Dashboard** (per role) – KPIs, recent applications, alerts.
2. **Loans** – Multi-step application form, approval, schedule generation.
3. **Payments** – Due list, record payment, statuses, history.
4. **Risk Scoring (Algorithmic)** – Distribution, factor impacts, per-customer cards with Approve/Reject.
5. **Repossession** – Track at-risk accounts, reminders, recovery.
6. **Inventory** – Motor units CRUD (Admin full control; Finance read/use).
7. **Users** (Admin) – Create/suspend users and reset passwords.
8. **Audit Trail** – System-wide action logs.
9. **Archives** – Centralized archive of records (any module).
10. **Reports** – Finance, risk, repo, inventory, user activity.

---

## 2) UX: Pages & Components (Finance Officer)

### A. Finance Dashboard

**Top Cards:** Total Loans • Approved • Pending • Overdue • Total Collected (month)

**Recent Applications Table:** Name | Motor | Status | SubmittedAt

**Repossession Alerts:** Low/Med/High risk summary, clickable to cases.

---

### B. Loan Application Wizard (like Google Forms)

**Step 1 – Personal Info**: first_name, last_name, email, phone, dob, address

**Step 2 – Employment Info**: employment_status, employer_name, monthly_income, last_paycheck, years_employed

**Step 3 – Motorcycle Info**: year, brand/make, model, purchase_price, term_years (1–5) → **auto-compute monthly** via Admin-set interest per term

**Step 4 – Required Documents**: proof_of_income, bank_statements (opt), valid_id, proof_of_address (opt) – multi-upload

**Actions:** Save Draft • Submit • Approve/Reject (post-review)

---

### C. Payments Page

**Analytics:** Total Collected • Pending Amount • Overdue Accounts • Collection Rate

**Controls:** Search (Customer/LoanID) • Filter: All | Paid | Pending | Overdue • Date range

**Table:** Customer | Motor | Due Date | Paid Date | Amount Due | Amount Paid | Status | Actions (Record/View History)

**Rules:**

* System generates monthly dues on approval.
* Overdue if `today > due_date` and unpaid → risk score increases.

---

### D. Risk Scoring (Rule-based, not AI)

**Analytics:** Risk Distribution (Low/Medium/High) • Factor Impact (Loan Amount, Payment History, Employment Stability, DTI, Credit Score)

**Cards per Applicant:** Name • Motor • Risk Level • Risk Score (0–100) • Credit Score • Monthly Income • DTI • Loan Amount • Insights • **Approve/Reject**

**Example Formula:**

```
riskScore = base
          + (missedPayments * 15)
          + clamp((loanAmount / max(monthlyIncome,1)) * 10, 0, 30)
          - clamp(creditScore / 20, 0, 25)
          + employmentPenalty
```

* `employmentPenalty`: 0 (employed), +5 (self-employed low docs), +10 (unemployed)
* Thresholds: Low < 40, Medium 40–70, High > 70 (Admin-adjustable)

---

### E. Repossession Management

**Cards:** Total At Risk • Critical Cases • Warning Cases • Recovery Rate

**Table (Active Cases):** Customer | Motor | Last Payment | Risk | Status | Actions (Details • Send Reminder • Mark Recovered)

**Flow:** Overdue→ Warning → High Risk → Case Opened → Reminders → Recovery/Close → Archive

---

## 3) UX: Pages & Components (Admin)

**Dashboard (Admin)**: Finance KPIs + Inventory KPIs + User Count + Recent Audit Logs.

**Inventory**: CRUD Motors (type, brand, model, year, chassis, color, purchase_price, status, image). Status: available | reserved | sold | repossessed.

**Users**: Create user, set role (admin/finance), suspend/reactivate, reset password.

**Audit Trail**: Search by date/user/module/action; export CSV/PDF.

**Settings** (Phase 2): interest per term years, risk thresholds, notification preferences.

---

## 4) Data Model (Relational Schema)

### Core Tables

* **users**(id, username, email, password, role: `admin|finance`, status: `active|suspended`, last_login, created_at, updated_at)
* **audit_logs**(id, user_id→users, module, action: `ADD|EDIT|DELETE|ARCHIVE|LOGIN|LOGOUT`, record_id, description, created_at)
* **motors**(id, type, brand, model, year, chassis_no, color, purchase_price, status: `available|reserved|sold|repossessed`, image_url, created_at, updated_at)
* **financing_terms**(id, term_years, interest_rate, created_at)
* **loan_applications**(id, first_name, last_name, email, phone, dob, address, employment_status, employer_name, monthly_income, last_paycheck, motor_id→motors, purchase_price, term_id→financing_terms, monthly_payment, total_amount, application_status: `pending|approved|rejected|active|completed`, risk_level, risk_score, created_by→users, created_at, updated_at)
* **loan_documents**(id, loan_id→loan_applications, doc_type: `proof_of_income|bank_statement|valid_id|others`, file_url, uploaded_at)
* **payments**(id, loan_id→loan_applications, amount_due, amount_paid, due_date, paid_date, status: `pending|paid|overdue`, created_at, updated_at)
* **risk_assessments**(id, loan_id→loan_applications, credit_score, monthly_income, debt_to_income_ratio, loan_amount, payment_history_score, risk_score, risk_level, created_at)
* **repossessions**(id, loan_id→loan_applications, reason, status: `warning|active|recovered|closed`, assigned_to→users, remarks, created_at, updated_at)
* **archives**(id, module, record_id, archived_by→users, reason, data_snapshot JSON, created_at, restored_at NULL, status: `archived|restored`)

**Relationships**

```
users (1)─< audit_logs
users (1)─< loan_applications
users (1)─< repossessions

motors (1)─< loan_applications
financing_terms (1)─< loan_applications

loan_applications (1)─< loan_documents
loan_applications (1)─< payments
loan_applications (1)─< risk_assessments
loan_applications (1)─< repossessions

archives: polymorphic reference via (module, record_id)
```

**Indexes (recommended)**

* `payments(loan_id, status, due_date)`
* `loan_applications(status, created_at)`
* `audit_logs(module, action, created_at)`
* `archives(module, record_id, status, created_at)`

---

## 5) Business Rules & Workflow

### Loan Lifecycle

1. **Create Application** → status=`pending` (draft allowed)
2. **Docs Uploaded** → validation checklist
3. **Risk Score Computed** (on submit / update)
4. **Approve/Reject**

   * Approve → status=`approved` then `active` on first payment schedule issue
   * Reject → status=`rejected` (can archive)
5. **Schedule Generation**: create N monthly `payments` rows based on `term_years` and interest.
6. **Payments**: update `amount_paid`, `status` per row. Auto-flag overdue.
7. **Complete**: when all dues paid → status=`completed`.

### Archiving Policy

* Any record can be archived by creating a row in **archives** with `data_snapshot` of the record.
* Option A: keep the original row active but flagged as archived via business rule; Option B: mark original row as inactive/hidden (soft strategy) — **Implementation: A or B configurable**, but archive table remains the source of truth for historical state.
* **Restore**: write back from `data_snapshot` and set `status='restored'` in **archives**.

### Audit Policy

* Log all `ADD|EDIT|DELETE|ARCHIVE|LOGIN|LOGOUT` in **audit_logs** with human-readable `description`.
* Sensitive fields (password) never included in descriptions.

---

## 6) Calculations

### Installment Computation

```
rate = interest_rate (per year)
months = term_years * 12
principal = purchase_price

// Simple interest (dealership style) example:
total_interest = principal * rate * term_years
total_amount  = principal + total_interest
monthly_payment = round(total_amount / months, 2)
```

> Swap to amortized loan formula if required later.

### Risk Scoring (Configurable thresholds)

* Missed payments weight = 15/each
* DTI = (existing debts + new monthly_payment) / monthly_income
* Credit contribution = `-(credit_score/20)` capped at -25
* Employment penalty by status

---

## 7) API Surface (Draft)

### Auth

* `POST /auth/login`
* `POST /auth/logout`

### Users (Admin)

* `GET /users` • `POST /users` • `PATCH /users/:id` • `PATCH /users/:id/suspend` • `POST /users/:id/reset-password`

### Inventory

* `GET /motors` • `POST /motors` • `PATCH /motors/:id` • `DELETE /motors/:id`
* `GET /financing-terms` • `POST /financing-terms` • `PATCH /financing-terms/:id`

### Loans

* `GET /loans` • `POST /loans` (wizard submit) • `GET /loans/:id` • `PATCH /loans/:id`
* `POST /loans/:id/approve` • `POST /loans/:id/reject`
* `POST /loans/:id/schedule/generate`
* `POST /loans/:id/documents` (upload)

### Payments

* `GET /payments` (filters) • `POST /payments` (record) • `GET /loans/:id/payments`

### Risk

* `GET /risk/summary` • `GET /risk/cards` • `POST /risk/recompute/:loanId`

### Repossession

* `GET /repos` • `POST /repos` (open case) • `PATCH /repos/:id` • `POST /repos/:id/remind`

### Audit & Archive

* `GET /audits` (admin only)
* `POST /archive` • `POST /archive/restore/:archiveId` • `GET /archive?module=&record_id=`

---

## 8) Permissions Matrix

| Feature                 | Admin |                   Finance |
| ----------------------- | ----: | ------------------------: |
| Dashboard               |     ✅ |                         ✅ |
| Loans CRUD              |     ✅ |                         ✅ |
| Documents Upload        |     ✅ |                         ✅ |
| Payments CRUD           |     ✅ |                         ✅ |
| Risk Views              |     ✅ |                         ✅ |
| Risk Threshold Settings |     ✅ |                         ❌ |
| Repossession CRUD       |     ✅ |                         ✅ |
| Inventory CRUD          |     ✅ |                 🔍 (read) |
| Users CRUD              |     ✅ |                         ❌ |
| Audit Trail             |     ✅ |           🔍 (limited/no) |
| Archive/Restore         |     ✅ | Archive-only (no restore) |

---

## 9) Non-Functional Requirements

* **Security:** JWT Auth, RBAC middleware, hashed passwords (bcrypt), input validation, file type checks for uploads.
* **Reliability:** ACID (MySQL), transaction use for multi-table ops (e.g., approval + schedule generation).
* **Observability:** request logs, error logs, audit logs.
* **Performance:** indexes on FK and search fields; pagination on all list endpoints.
* **Backups:** daily DB backup; object storage for documents (S3/minio) with lifecycle rules.

---

## 10) Tech Stack & Setup

* **Backend:** Node.js (Express) + Prisma ORM
* **DB:** MySQL 8+
* **Frontend:** React/Next.js Admin panel or server-rendered EJS (your pick)
* **Uploads:** Local/S3-compatible (minio)
* **PDF/Excel:** pdfkit/jspdf, exceljs

**ENV (sample)**

```
DATABASE_URL=
JWT_SECRET=
STORAGE_BUCKET_URL=
STORAGE_ACCESS_KEY=
STORAGE_SECRET_KEY=
```

---

## 11) Project Structure (suggested)

```
backend/
  src/
    modules/
      auth/ users/ motors/ loans/ payments/ risk/ repos/ audit/ archive/
    middlewares/ utils/ prisma/
  prisma/
    schema.prisma
frontend/
  app/ (Next.js) or views/ (EJS)
  components/ pages/ lib/
```

---

## 12) Dev Phases (for Codex + GPT-5 Hybrid)

1. **Schema & Migrations** (Prisma) → seed roles, sample data
2. **Auth & RBAC** → JWT, role guards, audit middleware
3. **Modules**: motors → financing_terms → loans (wizard) → documents → schedule → payments → risk → repos → archive → reports
4. **Admin Pages**: users, inventory, audit
5. **Dashboards** with analytics
6. **QA & UAT**: fixtures, edge cases, CSV/PDF export
7. **Deploy**: containerize, DB backup scripts, object storage config

---

## 13) Testing Checklist

* Loan approval creates exact N monthly payment rows
* Overdue flips status & raises risk
* Archive writes snapshot and hides record; restore reinstates
* Audit logs written for all CRUD + auth events
* Permission checks per role on every route
* File uploads (type/size) validated and stored correctly

---

## 14) ERD (ASCII)

```
users ──< audit_logs
   └──< loan_applications
   └──< repossessions

motors ──< loan_applications ──< payments
                         └──< loan_documents
                         └──< risk_assessments
                         └──< repossessions

financing_terms ──< loan_applications

archives: (module, record_id, archived_by, data_snapshot)
```

---

### Notes

* Central **archives** table simplifies retention & restore.
* Risk thresholds adjustable in settings (phase 2).
* Can switch to amortized formula later without schema change.
