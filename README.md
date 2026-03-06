<div align="center">

# 🩸 LifeFlow — Blood Bank Management System

### *Connecting donors, hospitals and admins to save lives*

[![Live Demo](https://img.shields.io/badge/🚀%20Live%20Demo-lifeflow--byi4.onrender.com-e02040?style=for-the-badge)](https://lifeflow-byi4.onrender.com)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Django](https://img.shields.io/badge/Django-4.2-092E20?style=for-the-badge&logo=django&logoColor=white)](https://djangoproject.com)
[![MySQL](https://img.shields.io/badge/MySQL-Workbench-4479A1?style=for-the-badge&logo=mysql&logoColor=white)](https://mysql.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Render-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://render.com)

<br/>

> **LifeFlow** is a full-stack Blood Bank Management System built with Django and MySQL.
> It features role-based access for **Admins**, **Donors**, and **Hospitals** with a
> stunning dark glassmorphism UI.

<br/>

## 🌐 [Click here to access the live app →](https://lifeflow-byi4.onrender.com)

> ⚠️ *Hosted on Render free tier — first load may take 30–50 seconds to wake up.*

</div>

---

## 🔐 Demo Login Credentials

| Role | Username | Password |
|------|----------|----------|
| 🔑 **Admin** | `admin` | `admin123` |
| 🧑 **Donor** | Register from the login page | — |
| 🏥 **Hospital** | Register from the login page | — |

---

## ✨ Features

### 👨‍💼 Admin Portal
- 📊 Dashboard with live blood stock overview
- ✅ Approve / reject donations
- 🩸 Fulfill / reject hospital blood requests (sorted by urgency)
- 📦 Manual inventory management
- 🧑 Browse and filter all donors
- 🏕️ Create and manage donation camps
- 🏥 Verify hospital accounts
- 📈 Reports — monthly trends, top donors, blood group breakdown

### 🧑 Donor Portal
- 💉 Submit blood donations
- 📋 Full donation history with status tracking
- 🏕️ Browse and register for donation camps
- ✅ Eligibility checker (90-day cooldown)
- 👤 Profile management

### 🏥 Hospital Portal
- 🆘 Request blood with urgency levels (Low / Medium / High / Critical)
- 📋 Track all requests with status updates
- 📦 View real-time blood stock availability

---

## 🗄️ Database & DBMS Concepts

| Concept | Implementation |
|---------|---------------|
| **Normalization (3NF)** | Separate User, Donor, Hospital models |
| **Foreign Keys** | Donor→User, Donation→Donor, Request→Hospital |
| **Views (4)** | blood_stock_view, eligible_donors_view, pending_requests_view, donor_summary_view |
| **Stored Procedures (3)** | approve_donation, fulfill_request, reject_donation |
| **Triggers (2)** | low_stock_alert (stock < 5), restore_donor_eligibility (90 days) |
| **Transactions** | ACID-compliant donation approval and request fulfillment |
| **Role-Based Access** | Custom `@role_required` decorator on all views |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Django 4.2 (Python 3.11) |
| **Database (Local)** | MySQL 8.0 via MySQL Workbench |
| **Database (Cloud)** | PostgreSQL via Render |
| **Frontend** | HTML5, CSS3 (Glassmorphism), Vanilla JS |
| **Fonts** | Sora + DM Sans (Google Fonts) |
| **Static Files** | WhiteNoise |
| **Deployment** | Render.com (Free tier) |

---

## 🚀 Run Locally

```bash
# 1. Clone the repository
git clone https://github.com/0Fauzan/Lifeflow.git
cd Lifeflow

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create MySQL database in Workbench
# Run: CREATE DATABASE lifeflow_db;

# 5. Run migrations
python manage.py makemigrations
python manage.py migrate

# 6. Seed default data
python manage.py seed

# 7. Start server
python manage.py runserver
```

Open **http://127.0.0.1:8000** and login with `admin` / `admin123`

---

## 📁 Project Structure

```
lifeflow/
├── core/                    ← Main Django app
│   ├── models.py            ← 9 database models
│   ├── views.py             ← All views (3 roles)
│   ├── forms.py             ← All forms
│   ├── urls.py              ← URL routes
│   └── management/
│       └── commands/
│           └── seed.py      ← Creates admin + inventory
├── templates/
│   ├── base.html            ← Shared navbar layout
│   ├── core/                ← Login + Register
│   ├── admin_panel/         ← 8 admin pages
│   ├── donor/               ← 5 donor pages
│   └── hospital/            ← 4 hospital pages
├── static/
│   └── css/style.css        ← Full glassmorphism design
├── sql/
│   ├── 1_views.sql          ← 4 database views
│   └── 2_procedures_triggers.sql ← 3 procedures + 2 triggers
└── lifeflow/
    └── settings.py          ← Auto-switches MySQL ↔ PostgreSQL
```

---

## 🗃️ Database Schema (9 Tables)

```
core_user              ← Custom user model (admin/donor/hospital)
core_donor             ← Donor profile + eligibility
core_hospital          ← Hospital profile + verification
core_bloodinventory    ← 8 blood group stock levels
core_camp              ← Donation camps
core_campregistration  ← Donor ↔ Camp registrations
core_donation          ← Donation submissions
core_bloodrequest      ← Hospital blood requests
core_notification      ← System alerts
```

---

## 📜 License

This project was built for academic submission as part of a DBMS course project.

---

<div align="center">

Made with ❤️ and 🩸

[![Live Demo](https://img.shields.io/badge/🚀%20Try%20it%20Live-lifeflow--byi4.onrender.com-e02040?style=for-the-badge)](https://lifeflow-byi4.onrender.com)

</div>
