import { NavLink, Route, Routes } from "react-router-dom";
import Home from "./pages/Home.jsx";
import Sentiment from "./pages/Sentiment.jsx";
import Models from "./pages/Models.jsx";
import Analyzer from "./pages/Analyzer.jsx";

const navLinkClass = ({ isActive }) =>
  `nav-link ${isActive ? "nav-link-active" : "nav-link-idle"}`;

export default function App() {
  return (
    <div className="min-h-screen">
      <header className="border-b border-white/40 bg-white/70 backdrop-blur">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-4">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-muted">Market Pulse</p>
            <h1 className="text-2xl font-semibold text-ink">ML Serving Console</h1>
          </div>
          <nav className="flex items-center gap-3 text-sm">
            <NavLink to="/" className={navLinkClass}>
              Prediction
            </NavLink>
            <NavLink to="/analyzer" className={navLinkClass}>
              Analyzer
            </NavLink>
            <NavLink to="/sentiment" className={navLinkClass}>
              History
            </NavLink>
            <NavLink to="/models" className={navLinkClass}>
              Models
            </NavLink>
          </nav>
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl px-6 py-10">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/analyzer" element={<Analyzer />} />
          <Route path="/sentiment" element={<Sentiment />} />
          <Route path="/models" element={<Models />} />
        </Routes>
      </main>
    </div>
  );
}
