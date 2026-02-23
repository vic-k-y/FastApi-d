# 🎨 AI Image Generation API

A simple FastAPI backend for AI image generation using Prodia and Together AI (Flux models).

Frontend:
[https://imagto.tech](https://imagto.tech)

---

## 🛠 Tech Stack

* FastAPI
* httpx
* Pydantic
* python-dotenv
* Uvicorn

---

## ⚙️ Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Create a `.env` file

```
PRODIA_API_KEY=your_key_here
TOGETHER_API_KEY=your_key_here
```

### 3. Run the server

```bash
uvicorn app:app --reload
```

Server runs at:

```
http://127.0.0.1:8000
```

---

## 📡 API Endpoints

* `POST /generate` → Generate image (Prodia)
* `POST /flux` → Generate image (Flux)
* `GET /` → Health check

---

This project focuses on clean structure, async handling, and safe external API integration.
