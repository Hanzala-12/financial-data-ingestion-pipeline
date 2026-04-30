import { useState } from "react";
import client from "../api/client.js";

export default function Analyzer() {
  const [headline, setHeadline] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const analyzeHeadline = async (e) => {
    e.preventDefault();
    if (!headline.trim()) return;

    setLoading(true);
    setResult(null);
    setError(null);

    try {
      const { data } = await client.post("/sentiment/analyze", { text: headline });
      setResult(data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-2xl animate-fade-up">
      <div className="mb-8 items-end justify-between">
        <div>
          <h2 className="text-3xl font-semibold text-ink">Live Headline Analyzer</h2>
          <p className="mt-2 text-muted">Paste a headline or tweet to see instant sentiment breakdown and predicted directional momentum.</p>
        </div>
      </div>

      <div className="card">
        <form onSubmit={analyzeHeadline} className="flex flex-col gap-4">
          <label className="label">Enter Text</label>
          <textarea
            value={headline}
            onChange={(e) => setHeadline(e.target.value)}
            className="input min-h-[120px] resize-y"
            placeholder="E.g. Apple reports record-breaking revenue in Q4..."
          />
          <button type="submit" disabled={loading} className="button self-end">
            {loading ? "Analyzing..." : "Analyze Impact"}
          </button>
        </form>

        {error && (
          <div className="mt-6 rounded-lg bg-red-50 p-4 text-sm text-red-600">
            {error}
          </div>
        )}

        {result && (
          <div className="mt-8 animate-fade-up rounded-xl border border-white/50 bg-white/60 p-6 shadow-inner">
            <h3 className="mb-4 text-xs font-semibold uppercase tracking-widest text-muted">Analysis Result</h3>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="rounded-lg bg-white/80 p-4 border border-black/5">
                <span className="text-xs uppercase text-muted block mb-1">Sentiment</span>
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-1 rounded text-xs font-bold ${
                    result.sentiment.label === 'positive' ? 'bg-green-100 text-green-700' :
                    result.sentiment.label === 'negative' ? 'bg-red-100 text-red-700' :
                    'bg-gray-100 text-gray-700'
                  }`}>
                    {result.sentiment.label.toUpperCase()}
                  </span>
                  <span className="text-sm font-medium text-ink">({result.sentiment.score.toFixed(2)})</span>
                </div>
              </div>

              <div className="rounded-lg bg-white/80 p-4 border border-black/5">
                <span className="text-xs uppercase text-muted block mb-1">Predicted Direction</span>
                <div className="flex items-center gap-2">
                  <span className={`text-xl font-bold ${
                    result.predicted_direction === 'UP' ? 'text-green-600' :
                    result.predicted_direction === 'DOWN' ? 'text-red-600' :
                    'text-gray-600'
                  }`}>
                    {result.predicted_direction}
                  </span>
                  <span className="text-sm font-medium text-ink">{(result.confidence * 100).toFixed(1)}% weight</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}