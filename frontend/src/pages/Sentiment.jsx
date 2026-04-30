import { useEffect, useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { getSentiment } from "../api/client";

export default function Sentiment() {
  const [ticker, setTicker] = useState("AAPL");
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchSentiment = async (targetTicker) => {
    if (!targetTicker) return;
    setLoading(true);
    setError(null);
    try {
      const res = await getSentiment(targetTicker);
      const formatted = res.map((d) => ({
        ...d,
        displayTime: new Date(d.hour).toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
      }));
      setData(formatted);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load sentiment data.");
      setData([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSentiment(ticker);
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    fetchSentiment(ticker.toUpperCase().trim());
  };

  return (
    <div className="animate-fade-up space-y-6">
      <div className="card flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold">Sentiment Trends</h2>
          <p className="text-sm text-muted">24-hour social and news sentiment</p>
        </div>
        <form onSubmit={handleSubmit} className="flex w-64 gap-2">
          <input
            type="text"
            value={ticker}
            onChange={(e) => setTicker(e.target.value.toUpperCase())}
            className="input py-2 text-center"
          />
          <button type="submit" disabled={loading} className="button py-2">
            Load
          </button>
        </form>
      </div>

      <div className="card min-h-[400px]">
        {error ? (
          <div className="flex h-full items-center justify-center text-red-500">
            {error}
          </div>
        ) : loading ? (
          <div className="flex h-[400px] items-center justify-center text-muted">
            Loading...
          </div>
        ) : data.length === 0 ? (
          <div className="flex h-[400px] items-center justify-center text-muted">
            No sentiment data found for '{ticker}'.
          </div>
        ) : (
          <div className="h-[400px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#ccc" />
                <XAxis
                  dataKey="displayTime"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fontSize: 12, fill: "#5f5b57" }}
                  dy={10}
                />
                <YAxis
                  domain={[-1, 1]}
                  axisLine={false}
                  tickLine={false}
                  tick={{ fontSize: 12, fill: "#5f5b57" }}
                  dx={-10}
                />
                <Tooltip
                  contentStyle={{
                    borderRadius: "12px",
                    border: "none",
                    boxShadow: "0 4px 20px rgba(0,0,0,0.08)",
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="net_sentiment"
                  stroke="#0f766e"
                  strokeWidth={3}
                  dot={{ r: 4, fill: "#0f766e", strokeWidth: 0 }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  );
}
