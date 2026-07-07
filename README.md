# 📋 Post Manager

**Post Manager** is a desktop application for managing posts with a role-based access control system. It consists of an **async FastAPI backend** with JWT authentication and a **PySide6 desktop client**.

---

## ✨ Features

- 🔐 **JWT Authentication** — secure login with token-based auth
- 👥 **Role-Based Access** — Admin and regular users with different permissions
- 📝 **Post Management** — create, edit, delete posts with public/private visibility
- 👤 **User Management** — admins can view, create, and edit users
- 🖥️ **Desktop Client** — PySide6 GUI with tabs for posts and users
- 🐳 **Docker Support** — one-command setup for MySQL and backend
- 🌐 **Public/Private Posts** — public posts visible to all, private only to authors
- 🔍 **"My Posts" Filter** — toggle to show only your own posts

---

## 🖼️ Screenshots

### Login Window
![Login Window](docs/login_window.png)

### Admin View — Users Tab
![Admin Users Tab](docs/admin_users_tab.png)

### Admin View — Posts Tab
![Admin Posts Tab](docs/admin_posts_tab.png)

### Regular User View — Posts Tab
![User Posts Tab](docs/user_posts_tab.png)

---

## 🛠️ Tech Stack

| Category | Technologies |
|----------|--------------|
| **Backend** | FastAPI, SQLAlchemy 2.0, MySQL, JWT, bcrypt |
| **Frontend** | PySide6 (Qt for Python) |
| **Database** | MySQL 8 (via asyncmy) |
| **Containerization** | Docker, Docker Compose |
| **Language** | Python 3.12+ |

---

## 📁 Project Structure
```
app/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Environment variables
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── .env                 # Secrets (not in repo)
│   └── .env.example         # Template for .env
│
├── frontend/
│   ├── main.py              # PySide6 entry point
│   ├── api_client.py        # HTTP client
│   ├── auth_manager.py      # Token storage
│   ├── async_utils.py       # Async helpers
│   ├── requirements.txt
│   ├── windows/
│   │   ├── login_window.py
│   │   ├── register_window.py
│   │   └── main_window.py
│   └── styles/
│       └── style.qss
│
├── docker-compose.yml
├── .gitignore
├── LICENSE
└── README.md
```
---

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- Docker (optional, for MySQL)
- Git

---

### Option 1: Run with Docker (Recommended)
```
bash
# 1. Clone the repository
git clone https://github.com/yourusername/post-manager.git
cd post-manager

# 2. Start MySQL + Backend with Docker Compose
docker-compose up -d

# 3. Run the desktop client (in a separate terminal)
cd frontend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python main.py
```
---

### Option 2: Run Locally (without Docker)

#### Backend
```
bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
# Edit .env with your database credentials

# Start MySQL (if not using Docker)
# Ensure MySQL is running on localhost:3306

# Run the server
uvicorn main:app --reload
```
#### Frontend
```
bash
cd frontend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Run the client
python main.py
```

---

## 🔧 Environment Variables

Create a `.env` file in the `backend/` folder based on `.env.example`:
```
env
# JWT
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL=mysql+asyncmy://root:secret@localhost:3306/fastapi_db
```

---

## 🧪 Testing the API

Once the backend is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Example API Requests

#### Register
```bash
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","email":"alice@ex.com","password":"secret123"}'
```
#### Login
```bash
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=alice@ex.com&password=secret123"
```
#### Create Post (with JWT)
```bash
curl -X POST http://localhost:8000/posts \
  -H "Authorization: Bearer <YOUR_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"title":"Hello","content":"World","is_public":true}'
```
---

## 👥 User Roles

| Role | Permissions |
|------|-------------|
| **Admin** | View all users, create users, edit users, view/edit/delete all posts |
| **User** | Create/edit/delete own posts, view public posts + own posts |

> 💡 **The first registered user automatically becomes the admin.**

---

## 🤝 Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---

## 🙏 Acknowledgements

- [FastAPI](https://fastapi.tiangolo.com/)
- [PySide6](https://doc.qt.io/qtforpython-6/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [Docker](https://www.docker.com/)

---
