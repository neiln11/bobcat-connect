# 🐾 Bobcat Connect

### **A Social Marketplace for UC Merced Student Organizations**

**Live Demo:** [http://darshmello.pythonanywhere.com](http://darshmello.pythonanywhere.com)

---

## 📖 Overview

**Bobcat Connect** is a full-stack web application designed to bridge the gap between students and campus organizations at UC Merced. It functions as a **two-sided marketplace**:

* **Supply:** Club Officers who need a platform to promote events and recruit members.
* **Demand:** Students looking to discover clubs, RSVP to events, and build their campus network.

Unlike static directories, Bobcat Connect features a dynamic **social feed**, real-time interactions, and a robust verification system to ensure content authenticity.

---

## 🚀 Key Features

### 👤 For Students
* **Global & Following Feeds:** Browse a public feed of all campus events or a curated feed of only the clubs you follow.
* **Event RSVPs:** One-click RSVP that integrates directly with **Google Calendar**.
* **Club Discovery:** Search and browse verified clubs by category (Academic, Social, Professional, etc.).
* **Interactions:** Like posts and follow clubs to stay updated.

### 🛡️ For Club Officers
* **Club Dashboard:** Analytics on follower growth and post engagement.
* **Content Management:** Create rich posts with images, or schedule events with specific times and locations.
* **Member Management:** View and manage your club's follower list.
* **Customization:** Update club profile pictures and bio details.

### 🔐 For Admins
* **Verification System:** Review and approve/reject student claims for club officer positions.
* **Content Moderation:** Remove inappropriate posts directly from the feed.
* **User Management:** Edit user roles and manage system access.

---

## 🛠️ Tech Stack

* **Backend:** Python, Flask, SQLAlchemy (ORM)
* **Database:** SQLite (Development), PostgreSQL (Production ready)
* **Frontend:** HTML5, CSS3 (Custom Dark Mode), Bootstrap 5, Jinja2 Templates
* **Scripting:** Pandas (for data seeding and CSV parsing)
* **Deployment:** PythonAnywhere

---

## 💻 Local Installation Guide

Follow these steps to run Bobcat Connect on your local machine.

### 1. Clone the Repository
```bash
git clone [https://github.com/Darshmello/bobcat-connect.git](https://github.com/Darshmello/bobcat-connect.git)
cd bobcat-connect
