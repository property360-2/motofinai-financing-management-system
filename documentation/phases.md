# MotofinAI – Financing & Inventory Management System

> **Scope:** Internal system for a motorcycle dealership/KASA. Roles: **Admin**, **Finance Officer**. Includes financing workflow, payments, risk scoring (rule-based), repossession management, inventory, user management, audit trail, and centralized archive table.

---

## ⚙️ Development Phases

### 🧩 **Phase 1: Initialization & Planning**

* Finalize database schema & relationships (Prisma schema)
* Setup project structure (backend + frontend folders)
* Initialize Prisma, Express, React/Next.js base
* Configure `.env` and MySQL connection
* Implement seeder for roles (admin, finance)

**Deliverables:**

* schema.prisma
* Base Express + Prisma setup
* Environment variables ready

---

### 🧠 **Phase 2: Authentication & RBAC**

* JWT authentication (login/logout)
* Role-based access control middleware
* Password hashing & validation
* User creation & status management (active/suspended)
* Audit log for login/logout

**Deliverables:**

* /auth routes
* /users CRUD (Admin only)
* Middleware: authGuard, roleGuard, auditLogger

---

### 🏍️ **Phase 3: Inventory & Financing Terms**

* CRUD for motorcycles (Admin full, Finance read-only)
* CRUD for financing terms (Admin only)
* Inventory statuses: available | reserved | sold | repossessed
* Image uploads (local/S3)

**Deliverables:**

* /motors routes
* /financing-terms routes
* File upload service

---

### 💸 **Phase 4: Loan Applications Module**

* Multi-step loan application form (personal, employment, motorcycle, documents)
* Auto-compute payment based on interest rate & term
* Application statuses: pending | approved | rejected | active | completed
* Loan approval triggers payment schedule generation

**Deliverables:**

* /loans routes (CRUD)
* Loan validation logic
* Payment schedule generator utility

---

### 📑 **Phase 5: Documents Management**

* Upload & link supporting documents to loan applications
* File type validation (PDF/JPEG/PNG)
* Document view/download endpoints

**Deliverables:**

* /loans/:id/documents endpoints
* File service utils

---

### 💰 **Phase 6: Payments Module**

* Display payment schedules (due, paid, overdue)
* Record payments
* Auto-flag overdue & recalculate risk
* Generate receipts (PDF optional)

**Deliverables:**

* /payments routes
* Payment service
* Receipt PDF generator (optional)

---

### ⚖️ **Phase 7: Risk Assessment & Algorithm**

* Implement rule-based risk scoring system
* Dashboard analytics for low/medium/high distribution
* Risk factor visualization (for future analytics page)
* Update risk after every payment or overdue mark

**Deliverables:**

* /risk endpoints
* Risk computation function

---

### 🚨 **Phase 8: Repossession Module**

* Track delinquent accounts & recovery rate
* Manage warning → active → recovered flow
* Reminder notifications (email/SMS optional)

**Deliverables:**

* /repos routes
* Repo status workflows
* Reminder service stub

---

### 🗂️ **Phase 9: Archive & Audit Trail**

* Central `archives` table with JSON snapshot per archived record
* Archive/Restore endpoints
* Global audit logger for CRUD + auth actions

**Deliverables:**

* /archive routes (archive + restore)
* /audit routes
* Middleware integration for logging

---

### 📊 **Phase 10: Reports & Dashboards**

* Admin dashboard: KPIs, inventory & finance overview, audit highlights
* Finance dashboard: loan stats, risk alerts, recent payments
* Graphs/charts for trends (Recharts or Chart.js)
* Export reports (PDF/Excel)

**Deliverables:**

* Dashboard endpoints (summary data)
* Reporting utilities
* Chart integrations

---

### 🧪 **Phase 11: Testing & Optimization**

* Unit + integration tests (Jest)
* Manual UAT for all modules
* Optimize DB queries (indexes, pagination)
* Finalize UI polish

**Deliverables:**

* Test scripts
* Optimization logs

---

### 🚀 **Phase 12: Deployment & Maintenance**

* Dockerize backend
* Setup environment for production (NGINX, PM2, SSL)
* Automated DB backup & object storage
* Create admin credentials

**Deliverables:**

* Dockerfile + Compose
* Production build
* Deployment guide

---

## ✅ Summary

This phased plan ensures modular progress:

* **P1–P3:** Core setup & inventory base
* **P4–P6:** Loan & finance backbone
* **P7–P9:** Intelligence (risk, repossession, archive, audit)
* **P10–P12:** Polish, optimize, deploy
