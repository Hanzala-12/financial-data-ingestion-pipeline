import { useState } from "react";
import { getPrediction } from "../api/client";

export default function Home() {
  const [ticker, setTicker] = useState("AAPL");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handlePredict = async (e) => {
    e.preventDefault();
    if (!ticker.trim()) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await getPrediction(ticker.trim().toUpperCase());
      setResult(data);
    } catch (err) {
      setError(
        err.response?.data?.detail || "Failed to fetch prediction. Is the backend running?"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-xl animate-fade-up space-y-8">
      <div className="card text-center">
        <h2 className="mb-2 text-2xl font-bold">Predict Direction</h2>
        <p className="text-sm text-muted">
          Get the next-hour market direction prediction.
        </p>

        <form onSubmit={handlePredict} className="mt-8 flex gap-3">
          <input
            type="text"
            value={ticker}
            onChange={(e) => setTicker(e.target.value.toUpperCase())}
            placeholder="AAPL"
            className="input text-center text-lg uppercase tracking-wider"
          />
          <button type="submit" disabled={loading} className="button w-32">
            {loading ? "..." : "Predict"}
          </button>
        </form>

        {error && (
          <div className="mt-6 rounded-xl bg-red-50 p-4 text-sm text-red-600">
            {error}
          </div>
        )}
      </div>

      {result && (
        <div className="card animate-fade-up text-center">
          <p className="label mb-6">Prediction Result &bull; {result.timestamp}</p>

          <div className="mb-8 flex items-center justify-center gap-4">
            <h3 className="text-6xl font-bold tracking-tighter">
              {result.ticker}
            </h3>
            <div
              className={`rounded-full px-6 py-2 text-2xl font-bold ${
                result.direction === "UP"
                  ? "bg-emerald-100 text-emerald-700"
                  : "bg-rose-100 text-rose-700"
              }`}
            >
              {result.direction === "UP" ? "↑ UP" : "↓ DOWN"}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="rounded-xl border border-white/50 bg-white/40 p-4">
              <p className="label mb-1">Confidence</p>
              <p className="text-2xl font-semibold">
                {(result.confidence * 100).toFixed(1)}%
              </p>
            </div>
            <div className="rounded-xl border border-white/50 bg-white/40 p-4">
              <p className="label mb-1">Model</p>
              <p className="text-2xl font-semibold">{result.model}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
