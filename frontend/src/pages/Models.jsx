import { useEffect, useState } from "react";
import { getModels } from "../api/client";

export default function Models() {
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await getModels();
        // Sort by F1 descending
        setModels(data.sort((a, b) => (b.f1 || 0) - (a.f1 || 0)));
      } catch (err) {
        setError(err.message || "Failed to load models.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) return <div className="text-center text-muted">Loading models...</div>;
  if (error) return <div className="text-center text-red-500">{error}</div>;
  if (!models.length) return <div className="text-center text-muted">No models found.</div>;

  return (
    <div className="animate-fade-up space-y-6">
      <div className="card">
        <h2 className="mb-6 text-2xl font-bold">Model Registry</h2>
        <div className="overflow-hidden rounded-xl border border-white/80">
          <table className="w-full text-left text-sm">
            <thead className="bg-white/50 text-xs uppercase tracking-wider text-muted">
              <tr>
                <th className="px-6 py-4 font-medium">Model Name</th>
                <th className="px-6 py-4 font-medium">F1 Score</th>
                <th className="px-6 py-4 font-medium">Accuracy</th>
                <th className="px-6 py-4 font-medium">RMSE</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/60 bg-white/30">
              {models.map((model, index) => (
                <tr
                  key={model.name || index}
                  className={`transition hover:bg-white/60 ${
                    index === 0 ? "bg-emerald-50/50" : ""
                  }`}
                >
                  <td className="px-6 py-4 font-semibold text-ink">
                    {model.name}
                    {index === 0 && (
                      <span className="ml-3 rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-bold text-emerald-700">
                        BEST
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    {model.f1 ? model.f1.toFixed(4) : "N/A"}
                  </td>
                  <td className="px-6 py-4">
                    {model.accuracy ? model.accuracy.toFixed(4) : "N/A"}
                  </td>
                  <td className="px-6 py-4">
                    {model.rmse ? model.rmse.toFixed(4) : "N/A"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
