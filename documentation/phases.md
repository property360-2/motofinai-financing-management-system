# ⚙️ DC Financing Corporation – Financing & Inventory Management System

### 🧭 Development Phases (Django Edition)

---

### 🧩 **Phase 1: Initialization & Setup**

* Initialize Django project `motofinai/`
* Configure MySQL connection in `settings.py`
* Install and configure `django-tailwind` or static Tailwind build
* Setup `.env` (DB, CDN, secrets)
* Create base apps: `users`, `inventory`, `loans`, `payments`, `risk`, `repossession`, `audit`, `archive`
* Prepare `base.html` layout and Atomic structure for templates

**Deliverables:**

* Project initialized with modular app folders
* `.env` + MySQL connection working
* Tailwind configured
* Atomic folder structure ready

---

### 🧠 **Phase 2: Authentication & RBAC**

* Use Django’s built-in `User` model (extend via AbstractUser)
* Roles: `admin`, `finance`
* JWT or session-based authentication
* Custom `role_required` decorators for view restrictions
* Implement login/logout with audit logs

**Deliverables:**

* Auth pages (`/login`, `/logout`)
* RBAC middleware
* User model + role system
* Initial superuser seeder
* Audit log for login/logout actions

---

### 🏍️ **Phase 3: Inventory & Financing Terms**

* Create `Motor` model for inventory CRUD
* Create `FinancingTerm` model for loan interest/terms
* Integrate `django-storages` with CDN (Cloudflare R2/S3) for image uploads
* Admin: full CRUD
* Finance: read-only access
* Use atomic templates (cards, tables)

**Status:** Core inventory CRUD and financing term management shipped in Django (Nov 2025).

**Deliverables:**

* `/inventory/` views and templates
* `/terms/` CRUD pages
* Working image uploads to CDN

---

### 💸 **Phase 4: Loan Applications Module**

* Multi-step form wizard (personal → employment → motorcycle → documents)
* Compute monthly payment via admin-set interest rate
* Status flow: `pending → approved → active → completed`
* Approval triggers payment schedule creation
* Draft/save state supported

**Deliverables:**

* `/loans/new/` multi-step form
* `/loans/<id>/` detail + approval
* Auto payment schedule generator
* Validation + status updates

---

### 📑 **Phase 5: Documents Management**

* Loan-linked document uploads (`proof_of_income`, `valid_id`, etc.)
* File validation (PDF/JPEG/PNG)
* Stored directly to CDN
* Inline preview (no downloads)

**Deliverables:**

* `/loans/<id>/documents/` management
* File upload + validation service
* CDN-backed storage integration

---

### 💰 **Phase 6: Payments Module**

* Display generated payment schedules (due/paid/overdue)
* Record payments with audit logs
* Auto flag overdue + recalc risk
* Generate receipts (PDF with `xhtml2pdf`)

**Deliverables:**

* `/payments/` list + record pages
* Overdue detection logic
* Optional PDF receipt generator

---

### ⚖️ **Phase 7: Risk Assessment & Algorithm**

* Implement configurable rule-based risk scoring
* View per-loan risk breakdown
* Admin-adjustable thresholds
* Recalculate after payments or overdue changes

**Deliverables:**

* `/risk/summary/` & `/risk/recompute/<loan_id>/`
* Risk formula implementation
* Dashboard analytics for risk levels

---

### 🚨 **Phase 8: Repossession Management**

* Manage delinquent accounts
* Status flow: `warning → active → recovered → closed`
* Reminder sending (email/SMS optional)
* Auto archive upon closure

**Deliverables:**

* `/repos/` CRUD views
* Reminder system stub
* Repo analytics cards

---

### 🗂️ **Phase 9: Archive & Audit Trail**

* Implement centralized archive model with JSON snapshots
* Any module can push archived data
* Restore function (Admin only)
* Global audit logger using Django signals for all CRUD/auth events

**Deliverables:**

* `/archive/` (archive + restore)
* `/audit/` (logs + filters)
* Middleware + signal integration

---

### 📊 **Phase 10: Reports & Dashboards**

* Admin Dashboard: KPIs for loans, payments, users, audit highlights
* Finance Dashboard: loan stats, overdue alerts, risk distribution
* Charts via Chart.js or ApexCharts
* Export to PDF/Excel

**Deliverables:**

* `/dashboard/` for each role
* `/reports/finance|inventory|risk/` endpoints
* PDF/Excel export tools

---

### 🧪 **Phase 11: Testing & Optimization**

* Unit + integration tests via Django’s test suite
* UAT for workflows (loan approval, payments, archiving)
* Query optimization (indexes, select_related)
* UI responsiveness testing

**Deliverables:**

* Test coverage report
* Optimization checklist

---

### 🚀 **Phase 12: Deployment & Maintenance**

* Dockerize Django app + MySQL
* Use Gunicorn + NGINX in production
* Configure static/media via CDN
* Set up daily database backups
* Create admin credentials for production

**Deliverables:**

* Dockerfile + Compose
* Production `.env` ready
* Deployment guide
* Backup + monitoring scripts

---

## ✅ Summary Roadmap

| Range       | Focus                                    |
| ----------- | ---------------------------------------- |
| **P1–P3**   | Core setup & inventory foundation        |
| **P4–P6**   | Loan + payment workflows                 |
| **P7–P9**   | Intelligence: risk, repo, archive, audit |
| **P10–P12** | Dashboards, testing, deployment          |

---
