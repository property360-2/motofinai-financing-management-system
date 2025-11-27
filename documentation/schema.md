## 🗄️ **DC Financing Corporation Database Schema (v4 – with Central Archive Table)**

### 🧩 **1. users**

| Field      | Type                        | Description     |
| ---------- | --------------------------- | --------------- |
| id         | INT (PK, AI)                | User ID         |
| username   | VARCHAR(100)                |                 |
| email      | VARCHAR(255)                |                 |
| password   | VARCHAR(255)                | Hashed password |
| role       | ENUM('admin', 'finance')    |                 |
| status     | ENUM('active', 'suspended') |                 |
| last_login | DATETIME                    |                 |
| created_at | DATETIME                    |                 |
| updated_at | DATETIME                    |                 |

---

### 🧾 **2. audit_logs**

| Field       | Type                                                        | Description                     |
| ----------- | ----------------------------------------------------------- | ------------------------------- |
| id          | INT (PK, AI)                                                | Log ID                          |
| user_id     | INT (FK → users.id)                                         | Who did it                      |
| module      | VARCHAR(100)                                                | (Loans, Motors, Payments, etc.) |
| action      | ENUM('ADD', 'EDIT', 'DELETE', 'ARCHIVE', 'LOGIN', 'LOGOUT') |                                 |
| record_id   | INT                                                         | Primary key of affected record  |
| description | TEXT                                                        | Human-readable description      |
| created_at  | DATETIME                                                    |                                 |

---

### 🏍️ **3. motors**

| Field          | Type                                                 | Description |
| -------------- | ---------------------------------------------------- | ----------- |
| id             | INT (PK, AI)                                         | Motor ID    |
| type           | VARCHAR(100)                                         |             |
| brand          | VARCHAR(100)                                         |             |
| model          | VARCHAR(100)                                         |             |
| year           | YEAR                                                 |             |
| chassis_no     | VARCHAR(100)                                         | Optional    |
| color          | VARCHAR(50)                                          |             |
| purchase_price | DECIMAL(12,2)                                        |             |
| status         | ENUM('available', 'reserved', 'sold', 'repossessed') |             |
| image_url      | TEXT                                                 |             |
| created_at     | DATETIME                                             |             |
| updated_at     | DATETIME                                             |             |

---

### 💵 **4. financing_terms**

| Field         | Type         | Description |
| ------------- | ------------ | ----------- |
| id            | INT (PK, AI) | Term ID     |
| term_years    | INT          | 1–5         |
| interest_rate | DECIMAL(5,2) |             |
| created_at    | DATETIME     |             |

---

### 🧾 **5. loan_applications**

| Field              | Type                                                           | Description         |
| ------------------ | -------------------------------------------------------------- | ------------------- |
| id                 | INT (PK, AI)                                                   | Loan ID             |
| first_name         | VARCHAR(100)                                                   |                     |
| last_name          | VARCHAR(100)                                                   |                     |
| email              | VARCHAR(255)                                                   |                     |
| phone              | VARCHAR(20)                                                    |                     |
| date_of_birth      | DATE                                                           |                     |
| address            | TEXT                                                           |                     |
| employment_status  | VARCHAR(100)                                                   |                     |
| employer_name      | VARCHAR(150)                                                   |                     |
| monthly_income     | DECIMAL(10,2)                                                  |                     |
| last_paycheck      | DATE                                                           |                     |
| motor_id           | INT (FK → motors.id)                                           |                     |
| purchase_price     | DECIMAL(12,2)                                                  |                     |
| term_id            | INT (FK → financing_terms.id)                                  |                     |
| monthly_payment    | DECIMAL(12,2)                                                  |                     |
| total_amount       | DECIMAL(12,2)                                                  |                     |
| application_status | ENUM('pending', 'approved', 'rejected', 'active', 'completed') |                     |
| risk_level         | ENUM('low', 'medium', 'high')                                  |                     |
| risk_score         | DECIMAL(5,2)                                                   |                     |
| created_by         | INT (FK → users.id)                                            | Finance who created |
| created_at         | DATETIME                                                       |                     |
| updated_at         | DATETIME                                                       |                     |

---

### 📄 **6. loan_documents**

| Field       | Type                                                            | Description |
| ----------- | --------------------------------------------------------------- | ----------- |
| id          | INT (PK, AI)                                                    | Document ID |
| loan_id     | INT (FK → loan_applications.id)                                 |             |
| doc_type    | ENUM('proof_of_income', 'bank_statement', 'valid_id', 'others') |             |
| file_url    | TEXT                                                            |             |
| uploaded_at | DATETIME                                                        |             |

---

### 💳 **7. payments**

| Field       | Type                               | Description |
| ----------- | ---------------------------------- | ----------- |
| id          | INT (PK, AI)                       | Payment ID  |
| loan_id     | INT (FK → loan_applications.id)    |             |
| amount_due  | DECIMAL(12,2)                      |             |
| amount_paid | DECIMAL(12,2)                      |             |
| due_date    | DATE                               |             |
| paid_date   | DATE                               | Nullable    |
| status      | ENUM('pending', 'paid', 'overdue') |             |
| created_at  | DATETIME                           |             |
| updated_at  | DATETIME                           |             |

---

### 🚨 **8. repossessions**

| Field       | Type                                             | Description |
| ----------- | ------------------------------------------------ | ----------- |
| id          | INT (PK, AI)                                     | Repo ID     |
| loan_id     | INT (FK → loan_applications.id)                  |             |
| reason      | TEXT                                             |             |
| status      | ENUM('warning', 'active', 'recovered', 'closed') |             |
| assigned_to | INT (FK → users.id)                              |             |
| remarks     | TEXT                                             |             |
| created_at  | DATETIME                                         |             |
| updated_at  | DATETIME                                         |             |

---

### 📊 **9. risk_assessments**

| Field                 | Type                            | Description |
| --------------------- | ------------------------------- | ----------- |
| id                    | INT (PK, AI)                    | Risk ID     |
| loan_id               | INT (FK → loan_applications.id) |             |
| credit_score          | DECIMAL(5,2)                    |             |
| monthly_income        | DECIMAL(10,2)                   |             |
| debt_to_income_ratio  | DECIMAL(5,2)                    |             |
| loan_amount           | DECIMAL(12,2)                   |             |
| payment_history_score | DECIMAL(5,2)                    |             |
| risk_score            | DECIMAL(5,2)                    |             |
| risk_level            | ENUM('low', 'medium', 'high')   |             |
| created_at            | DATETIME                        |             |

---

### 🗂️ **10. archives (🆕 centralized archive table)**

| Field         | Type                         | Description                                    |
| ------------- | ---------------------------- | ---------------------------------------------- |
| id            | INT (PK, AI)                 | Archive ID                                     |
| module        | VARCHAR(100)                 | e.g. 'motors', 'loan_applications', 'payments' |
| record_id     | INT                          | ID of the archived record                      |
| archived_by   | INT (FK → users.id)          | User who archived it                           |
| reason        | TEXT                         | Optional reason                                |
| data_snapshot | JSON                         | Snapshot of the record at archive time         |
| created_at    | DATETIME                     | Date archived                                  |
| restored_at   | DATETIME, NULL               | If restored later                              |
| status        | ENUM('archived', 'restored') |                                                |

---

### ⚙️ **Archive Flow**

1. Any module record → `INSERT INTO archives (...)`

   * Store `module`, `record_id`, `archived_by`, `data_snapshot` (JSON dump of the record).
2. Optional → `DELETE` or mark inactive in original table (depends on your policy).
3. Restore = reverse: reinsert/update the original table and mark archive as `restored`.

---

### 💡 **Advantages**

✅ Centralized — one place for all archived records
✅ Traceable — can filter by `module`, `archived_by`, or date
✅ Lightweight — no need to modify every table
✅ Reversible — easy restoration mechanism

---
