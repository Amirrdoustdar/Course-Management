# 📚 Course Management System

A functional **Course Management System** built with **Python** and the **Flask** framework, using **MySQL** for persistent data storage. This system supports two user roles — **Admin** and **Student** — each with their own dedicated panel and unique set of features.

---

## ✨ Key Features

### 🔐 Authentication System
- Secure user registration with password validation:
  - Must include uppercase, lowercase, number, and minimum length.
- Login system for both users and admin.
- Logout functionality.
- Password recovery via a security question.

### 👥 User Roles & Access Levels

#### 🛠️ Admin Panel
- Full **CRUD** capabilities for managing courses.
- Upload course images.
- View a list of all registered students.

#### 🎓 Student Panel
- View all available courses.
- Use a shopping cart system to select courses before enrolling.
- Finalize course enrollment.
- View personal profile and enrolled courses.
- Edit profile details (email, password, profile picture).

### 🗄️ Database
- **MySQL** as the database engine.
- Structured tables:
  - `users`, `courses`, and their many-to-many relationship.

### 🎨 Frontend
- Styled using **TailwindCSS** for a modern and responsive design.

---

## 🛠️ Tech Stack

- **Backend:** Python, Flask  
- **Database:** MySQL (via PyMySQL)  
- **Frontend:** HTML5, Jinja2, TailwindCSS  
- **Version Control:** Git

---

## 🚀 Installation and Setup

### 📦 Prerequisites
- Python 3.10+
- Git
- MySQL server (e.g., XAMPP, WAMP, MySQL Community Server)

### 🔧 Setup Steps

#### 1. Clone the Repository
```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

#### 2. Create and Activate a Virtual Environment
```bash
# Windows
python -m venv venv
.env\Scriptsctivate
```

#### 3. Install Dependencies
```bash
# Create requirements.txt (if not already created)
pip freeze > requirements.txt

# Install packages
pip install -r requirements.txt
```

#### 4. Configure the Database
- Open `database1.py`.
- Modify the `connection_params` dictionary to include your MySQL root password.

#### 5. Initialize Database and Tables
```bash
py database1.py
```

#### 6. Run the Application
```bash
py app.py
```
- Open `http://127.0.0.1:8888` in your browser (or whichever port you've configured).

---

## 📁 Project Structure

```
/
├── static/
│   └── style.css
├── templates/
│   ├── adminPanel.html
│   ├── home.html
│   └── ... (all other HTML files)
├── uploads/
├── venv/
├── app.py                  # Main Flask app
├── database1.py            # DB configuration and models
├── requirements.txt        # Dependencies
└── README.md               # This file
```

---

## 🤝 Contributing

This is a personal project, but you're welcome to share suggestions.  
Feel free to open an **Issue** if you spot bugs or want to propose improvements.

---

## 📄 License

Released under the **MIT License**. See the [LICENSE](./LICENSE) file for more details.
