# Viator

An AI-powered conversational agent that plans personalized travel itineraries with flight search, Reddit-based recommendations, and calendar integration.

---

##  Installation Instructions

### 1. Download and open the zip file. Make sure there's a .env file in the root of your directory

### 2. split your terminal

### 2. Backend Setup (Python + FastAPI)


#### a. Create a virtual environment
In one terminal run 

```
cd backend/app
python -m venv viator-env
# On windows
.\viator-env\Scripts\Activate.ps1
# on Mac
source venv/bin/activate
```

#### b. Install dependencies

```
pip install -r requirements.txt
```

Make sure `requirements.txt` includes:
```text
fastapi
uvicorn
openai
pydantic
python-dotenv
```
### c. run the FastAPI backend
```
uvicorn main:app --reload --port 8000
```
---

### 3. Frontend Setup (Next.js + Tailwind)

#### a. Install dependencies
Now in the other terminal that should still be in the root directory

```
cd frontend/viator-frontend
npm install
```

#### b. Run the development server

```
npm run dev
```

By default:
- Frontend runs on: `http://localhost:3000`
- Backend runs on: `http://localhost:8000`

---

## 💬 Usage Instructions

Once both frontend and backend are running:

1. Open [http://localhost:3000](http://localhost:3000).
2. Type your travel request into the chat (e.g., `Plan me a 5-day trip to Tokyo under $2000`).
3. The assistant will:
   - Respond conversationally with suggestions.
   - Display structured content like flight results and itinerary.
   - Optionally offer to add your trip to Google Calendar.

---

## 📌 Features
- 🔍 Live flight search integration
- 🗺️ Reddit-based hidden gem recommendations
- 📆 Google Calendar event creation
- 🧠 GPT-4o-mini powered agent orchestration

---

## 🛠 Tech Stack
- **Frontend**: Next.js, React, TailwindCSS
- **Backend**: FastAPI, Python
- **LLM**: OpenAI GPT-4o-mini

---
