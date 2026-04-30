import axios from "axios";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function getPrediction(ticker) {
  const response = await axios.get(`${API}/predict/${ticker}`);
  return response.data;
}

export async function getSentiment(ticker) {
  const response = await axios.get(`${API}/sentiment/${ticker}`);
  return response.data;
}

export async function getModels() {
  const response = await axios.get(`${API}/models`);
  return response.data;
}
