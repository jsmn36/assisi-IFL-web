# Hotel PMS - Setup and Run Guide

This guide will walk you through the complete setup of the Hotel Property Management System (PMS), including the Python backend, React frontend, and Electron desktop shell.

## 📋 Prerequisites

Ensure you have the following installed on your system:
- **Python 3.12+**
- **Node.js 18+** (and npm)
- **Git**

---

## 🛠️ Step 1: Initial Repository Setup

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repository-url>
   cd pms-hotel-desktop
   ```

---

## 🐍 Step 2: Backend Setup (FastAPI)

1. **Navigate to the backend directory**:
   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment**:
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate

   # macOS/Linux
   python3.12 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**:
   Create a `.env` file in the `backend/` directory by copying the example:
   ```bash
   cp .env.example .env
   ```
   **Important**: Open `.env` and ensure `SECRET_KEY` and `JWT_SECRET_KEY` are set. If they are missing, you can generate them using:
   ```bash
   python -c "import os; print(os.urandom(32).hex())"
   ```

5. **Initialize the Database**:
   The system uses SQLite by default. Run migrations to create the schema:
   ```bash
   alembic upgrade head
   ```

6. **Start the Backend Server**:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   *The API will be available at `http://localhost:8000` and the interactive documentation at `http://localhost:8000/docs`.*

---

## ⚛️ Step 3: Frontend Setup (React + Vite)

1. **Open a new terminal and navigate to the frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Configure Environment Variables**:
   Create a `.env` file in the `frontend/` directory:
   ```bash
   cp .env.example .env
   ```
   Ensure `VITE_API_BASE_URL` is set to `http://localhost:8000`.

4. **Start the Development Server**:
   ```bash
   npm run dev
   ```
   *The frontend will be available at `http://localhost:5173` (or the port shown in your terminal).*

---

## 🖥️ Step 4: Electron Setup (Desktop App)

1. **Open a third terminal and navigate to the electron directory**:
   ```bash
   cd electron
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Launch the Desktop Application**:
   *Make sure both backend and frontend are already running.*
   ```bash
   npm start
   ```

---

## 🧪 Step 5: Verification & Testing

### Backend Verification
- Visit `http://localhost:8000/docs` to see the OpenAPI documentation.
- Run tests:
  ```bash
  cd backend
  pytest tests/ -q --tb=short
  ```

### Frontend Verification
- Visit `http://localhost:5173` in your browser.
- Run tests:
  ```bash
  cd frontend
  npm test
  ```

---

## 💡 Important Notes

- **Hybrid Database**: By default, the app uses **SQLite** for local development. To use **PostgreSQL**, update the `DATABASE_URL` in `backend/.env`.
- **Gate Framework**: All mutations must follow the Gate Framework architecture. Direct database edits are discouraged.
- **Background Tasks**: In SQLite mode, tasks are handled by **APScheduler**. Redis/Celery is only used in PostgreSQL mode.
