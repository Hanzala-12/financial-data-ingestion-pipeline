import axios from "axios";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

// Create axios instance for direct use in components
const client = axios.create({
  baseURL: API,
});

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

// Export axios instance as default for components that need raw axios access
export default client;
