🚀 Full-Stack ML Serving App TODO
🎯 Objective

Build a demo-ready ML prediction system:

Backend: FastAPI (serve models + data)
Frontend: React (Vite + TailwindCSS)
Goal: Show predictions, sentiment trends, and model comparison
📦 Project Structure
project/
│── data/
│   ├── processed/
│   │   └── sentiment_hourly.parquet
│
│── models/
│   └── (MLflow or saved models)
│
│── src/
│   ├── api/
│   │   ├── main.py
│   │   ├── routes/
│   │   │   ├── predict.py
│   │   │   ├── sentiment.py
│   │   │   ├── models.py
│   │   │   └── retrain.py
│   │   ├── services/
│   │   │   ├── model_loader.py
│   │   │   ├── feature_pipeline.py
│   │   │   └── sentiment_loader.py
│   │   └── utils/
│
│── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Home.jsx
│   │   │   ├── Sentiment.jsx
│   │   │   └── Models.jsx
│   │   ├── components/
│   │   └── api/
│   │       └── client.js
│
│── TODO.md
⚙️ Backend — FastAPI
🔧 Setup
 Install dependencies:
fastapi
uvicorn
pandas
torch
mlflow
python-multipart
 Enable CORS for frontend:
origins = ["http://localhost:3000"]
🧠 Model Loading
 Create model_loader.py
 Load best model:
mlflow.pytorch.load_model("models:/LSTM/Production")
 Cache model in memory (avoid reload per request)
📊 Feature Pipeline
 Create feature_pipeline.py
 Implement:
def get_latest_features(ticker: str) -> list:
 Logic:
Load latest 24-hour window
Ensure shape matches model input
Return feature array
🔮 Endpoint: /predict/{ticker}
 Create route in predict.py
 Steps:
Load features
Convert to tensor
Run model
Compute:
direction: UP | DOWN
confidence
 Response format:
{
  "ticker": "AAPL",
  "direction": "UP",
  "confidence": 0.73,
  "model": "LSTM"
}
📈 Endpoint: /sentiment/{ticker}
 Create sentiment_loader.py
 Load:
sentiment_hourly.parquet
 Filter:
last 24 hours
specific ticker
 Return JSON array
🤖 Endpoint: /models
 Create models.py
 Fetch from MLflow:
model name
run_id
val_accuracy
F1 / RMSE
 Return list:
[
  {"name": "LSTM", "accuracy": 0.91, "f1": 0.89},
  {"name": "GRU", "accuracy": 0.88, "f1": 0.85}
]
🔁 Endpoint: /retrain (Admin only)
 Create retrain.py
 Trigger:
Airflow DAG OR
local training function
 Keep simple:
No auth → just comment "admin only"
🧪 Backend Testing
 Test endpoints via:
Postman / curl
 Validate:
JSON structure
Model inference works
No crashes on bad ticker
🎨 Frontend — React (Vite + Tailwind)
⚙️ Setup
 Create app:
npm create vite@latest frontend
 Install:
axios
react-router-dom
recharts
tailwindcss
🌐 API Client
 Create api/client.js
const API = "http://localhost:8000";
 Functions:
getPrediction(ticker)
getSentiment(ticker)
getModels()
🏠 Page 1 — Home (Prediction)
 Input field (ticker)
 Button → call /predict
 Display:
Direction badge:
🟢 UP
🔴 DOWN
Confidence %
Model name
Timestamp
📈 Page 2 — Sentiment Explorer
 Call /sentiment
 Plot using Recharts:
LineChart → net_sentiment
Optional:
Bar chart → pos/neg/neu counts
 X-axis: time (hour)
 Y-axis: sentiment score
📊 Page 3 — Model Comparison
 Call /models
 Display table:
Model name
Accuracy
F1
RMSE
 Highlight best model:
Green background
🎯 UI Requirements
 Keep UI minimal
 No authentication
 Clean layout using Tailwind
 Focus on functionality over design
🔗 Integration
 Ensure frontend connects to backend
 Handle loading states
 Handle API errors gracefully
🚀 Final Deliverables
 Working FastAPI server
 Functional React app (3 pages)
 Model inference working
 Sentiment visualization working
 Models comparison visible
🧠 Agent Instructions
Do NOT over-engineer
Prioritize working demo over perfection
Keep components small and reusable
Ensure each backend function is testable
Avoid unnecessary abstractions