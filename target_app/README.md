# 🛒 Standalone Target E-Commerce Microservice (Port 5000)

This is an **independent external target microservice** built with FastAPI, running on **Port 5000**.

It acts as a real-world production microservice (E-Commerce Checkout API). When errors occur or when `/trigger-outage` is called, it sends live webhook alerts to the **AI Production Incident Response Platform** (`http://localhost:8000/api/incidents`).

---

## 🏗 System Architecture

```
[Standalone Target E-Commerce App (Port 5000)]
         │
         │ 💥 Outage / Error occurs
         ▼ (HTTP POST Webhook)
[AI Production Incident Response Platform (Port 8000)]
         │
         │ 🤖 5-Agent Pipeline Investigation (Gemini 2.5 Flash)
         ▼
[Human Approval -> Real GitHub Pull Request Created]
```

---

## 🚀 How to Run Standalone Target App

1. **Start the Target App**:
   ```powershell
   cd target_app
   ..\backend\.venv\Scripts\python.exe main.py
   ```

2. **Endpoints Available**:
   - `GET http://localhost:5000/`: Health status
   - `POST http://localhost:5000/checkout`: Try processing a transaction
   - `POST http://localhost:5000/trigger-outage?error_type=db`: Trigger DB timeout and send webhook to AI Platform
   - `POST http://localhost:5000/reset`: Restore target app back to healthy status
