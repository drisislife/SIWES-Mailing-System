# Council Workspace System (CWS)
### Local Government Digital Mailing & Memoranda Management System

[![Python Version](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-6.1-green?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple?logo=bootstrap&logoColor=white)](https://getbootstrap.com/)
[![Tests](https://img.shields.io/badge/Tests-Passing%20(7%2F7)-brightgreen)](#automated-testing)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🏛️ Project Overview

The **Council Workspace System (CWS)** is an enterprise intranet platform engineered to modernise, streamline, and secure internal administrative correspondence within local government council secretariats.

Historically, municipal council administrations have relied on physical paper memorandums, physical dispatch ledgers, and manual courier movement between departments. This traditional workflow poses critical administrative challenges:
- **File Loss & Misplacement:** Vital correspondence misplaced in transit.
- **Approval Bottlenecks:** Memos sitting on desks without tracking or status visibility.
- **Lack of Accountability:** Inability to legally verify who received, viewed, or actioned a memorandum.
- **Security Vulnerabilities:** Unauthorized access to confidential council documents.

**CWS replaces physical paperwork with a digital, role-governed memorandum pipeline** that enforces statutory administrative hierarchy:
$$\text{Staff Officer} \longrightarrow \text{Head of Department (HOD)} \longrightarrow \text{Council Manager (CM)}$$

---

## 🏗️ Architecture & Technology Stack

| Layer | Technology | Description |
|---|---|---|
| **Backend Framework** | **Django 6.x (Python 3.12+)** | Implements Model-Template-View (MTV) architecture, ORM database modeling, session management, CSRF defense, and authentication. |
| **Frontend UI** | **HTML5, CSS3, Bootstrap 5** | Jobnt-inspired administrative interface featuring a dark navy sidebar (`#0c1427`), emerald green action accents (`#00875a`), and responsive cards. |
| **Icons & Design** | **Bootstrap Icons (`bi-*`)** | Consistent iconography for status indicators, priority tags, and role badges. |
| **Client Scripting** | **Vanilla JavaScript (ES6+)** | Template autofill, session inactivity modal timer, and interactive confirmation modals. |
| **Database** | **SQLite (Dev) / PostgreSQL (Prod)** | Relational database modeling users, departments, memos, minutes, acknowledgements, and audit logs. |
| **Print & Export Engine** | **CSS `@media print` Letterhead** | High-fidelity printable council memorandums with the Nigerian Coat of Arms emblem, security watermark, automated reference numbers, verified digital signatures, and endorsement minutes. |
| **Security & Auth** | **Django Auth, PBKDF2, Session Middleware** | Role-Based Access Control (RBAC), Email OTP Two-Factor Authentication (2FA), and immutable security audit logs. |

---

## 🏛️ Canonical Council Departments

The system models the operational reality of local government council administration across **16 canonical departments**:
1. **Office of the Council Manager** *(Executive Leadership & Council Administration)*
2. **Human Resources & Administration (HR/Admin)**
3. **Information & Communication Technology (ICT)**
4. **Works & Infrastructure**
5. **Procurement**
6. **Internal Audit**
7. **Legal**
8. **Budget & Fiscal Planning**
9. **Health Care**
10. **Education**
11. **Environment & Health**
12. **Public Affairs**
13. **Women Affairs & Poverty Alleviation (WAPA)**
14. **Agriculture (Agric)**
15. **Tourism**
16. **Chieftaincy Affairs**

---

## 🌟 Key Features & Capabilities

### 1. 🛡️ Verification Badge Hierarchy
Accounts are vetted by administration before sending memos:
- 🟡 **Gold Checkmark (`#f59e0b`):** Council Manager / Super Administrator
- 🔵 **Blue Checkmark (`#0d6efd`):** Heads of Departments (HODs)
- 🟢 **Green Checkmark (`#198754`):** Certified Council Staff Officers
- ⏳ **Amber Hourglass (`#ffc107`):** Unverified Accounts *(restricted access until approved)*

### 2. 📝 Automated Reference Numbering & Dispatch
- Auto-generates official council tracking codes (e.g., `CWS/WRK/2026/A4164`).
- **Intra-Department:** Delivered instantly to the recipient.
- **Cross-Department:** Automatically routed to the sender's HOD approval queue (`pending_hod`) for endorsement before delivery.

### 3. ⏱️ Memo Read Receipts & Formal Acknowledgement
- Records the exact timestamp when a recipient opens a memo (`read_at`), displaying a visual receipt to the sender.
- **Formal Sign-off:** Addressed officers can formally sign off on receipt with an optional action note (`MessageAcknowledgement`).

### 4. 🧵 Conversation Threading & Hierarchical Replies
- Replies link back to parent memorandums (`parent` ForeignKey), auto-prefacing subjects (`"Re: ..."`) and maintaining a chronological thread history.

### 5. 🔄 Memo Recall / Withdrawal
- Senders can officially withdraw memos sent in error (if unread) with a mandatory recorded justification.

### 6. 📑 Pre-formatted Council Memo Templates
- One-click template selector in the compose screen:
  - *Consolidated Staff Leave Schedule*
  - *Explanation in Response to Official Query*
  - *Internal Store Requisition*
  - *Facility / Infrastructure Inspection Report*
  - *Council Directive / Policy Notice*
  - *General Council Circular*

### 7. 🗄️ Central Records Registry & Archive
- Searchable registry for Council Leadership and HODs featuring keyword search, department and date filters, and **CSV export**.

### 8. 🖨️ Official Printable Memo Letterhead / PDF Export
- Dedicated printable template featuring the Nigerian National Coat of Arms header, watermarked background, reference numbers, verified signatures, and recorded endorsement minutes.

### 9. 📢 Council Notice Board & Bulletin
- Broadcast board for circulars, directives, meetings, and staff welfare announcements with pinned notice support.

### 10. 👥 Council Personnel Directory & Duty Tracking
- Searchable staff roster with direct compose links.
- Real-time duty status flags:
  - `🟢 On Active Duty`
  - `🟡 On Official Assignment / Field`
  - `🔴 On Approved Leave`

### 11. 📊 Executive Analytics Dashboard
- Leadership metrics for total memos dispatched, monthly traffic volumes, department activity breakdown, and priority distributions.

### 12. 🔒 Security & Administrative Audit Trail
- Immutable audit trail (`AuditLog`) capturing logins, logouts, dispatches, reads, sign-offs, and recalls with IP addresses.
- **Session Inactivity Guard:** 30-minute idle session timeout with a 2-minute countdown warning modal.
- **Two-Factor Authentication (2FA):** User-configurable email OTP verification gate on login.

### 13. 📥 Bulk Staff CSV Importer
- Administration tool for importing staff in bulk with downloadable sample CSV roster template.

---

## 🚀 Quick Start & Installation

### Prerequisites
- Python 3.12 or higher
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/drisislife/SIWES-Mailing-System.git
cd SIWES-Mailing-System
```

### 2. Create and Activate Virtual Environment
**On Windows:**
```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

**On macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run Database Migrations
```bash
python manage.py migrate
```

### 5. Seed Test Council Data (Recommended)
Populate the database with canonical council departments, mock personnel, sample memos, and bulletin notices:
```bash
python manage.py seed_test_data
```

### 6. Start the Development Server
```bash
python manage.py runserver
```
Visit `http://127.0.0.1:8000/` in your browser.

---

## 🔑 Demo Accounts & Credentials

All demo accounts created by `seed_test_data` share the default password:
> **Default Password:** `CouncilPass123!`

| Role / Badge | Officer Name | Department | Email / Login | Duty Status |
|---|---|---|---|---|
| 🟡 **ADMIN** | **Rashidat Adeleke** | Office of the Council Manager | `cm@council.gov.ng` | Active Duty |
| 🔵 **HOD** | **Folashade Balogun** | HR/Admin | `hod.hr@council.gov.ng` | Active Duty |
| 🟢 **STAFF** | **Tunde Bakare** | HR/Admin | `staff.hr@council.gov.ng` | Active Duty |
| 🔵 **HOD** | **Damilola Idris** | ICT | `hod.ict@council.gov.ng` | Active Duty |
| 🟢 **STAFF** | **Chinedu Eze** | ICT | `staff.ict@council.gov.ng` | Active Duty |
| 🔵 **HOD** | **Mustapha Bello** | Works | `hod.works@council.gov.ng` | Field Duty |
| 🟢 **STAFF** | **Kabiru Alabi** | Works | `staff.works@council.gov.ng` | Field Duty |
| 🔵 **HOD** | **Ngozi Okonkwo** | Procurement | `hod.procurement@council.gov.ng` | Active Duty |
| 🟢 **STAFF** | **Ayomide Bilesanmi** | Procurement | `staff.procurement@council.gov.ng` | Active Duty |
| 🔵 **HOD** | **Samuel Adelekan** | Audit | `hod.audit@council.gov.ng` | Active Duty |
| 🔵 **HOD** | **Amaka Obi** | Legal | `hod.legal@council.gov.ng` | Official Duty |
| 🔵 **HOD** | **Babatunde Jinadu** | Budget | `hod.budget@council.gov.ng` | Active Duty |
| 🔵 **HOD** | **Kelechi Nwosu** | Health Care | `hod.health@council.gov.ng` | Active Duty |
| 🔵 **HOD** | **Mariam Sanni** | WAPA | `hod.wapa@council.gov.ng` | On Leave |

---

## 🧪 Automated Testing

Execute the automated test suite covering read receipts, acknowledgement, reply threading, memo recall, PDF export, staff directory, and archive access controls:

```bash
python manage.py test messaging
```

---

## 📄 License
This project is licensed under the [MIT License](LICENSE).
