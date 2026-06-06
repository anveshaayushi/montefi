import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import { motion, AnimatePresence } from "framer-motion";
import {
  Search, DollarSign, Zap, BarChart3, Target,
  TrendingDown, Plus, X, RefreshCw, Cpu,
  ShieldAlert, Activity, ArrowUpRight, ChevronRight,
  TrendingUp, Sun, Moon,
} from "lucide-react";

// Switch this based on environment:
// Local dev  → "http://localhost:8000"
// Production → "https://montefibackendd.up.railway.app"
const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8000";

/* ─── theme tokens ─── */
const DARK = {
  bg:           "#0d0f12",
  surface:      "rgba(255,255,255,0.025)",
  surfaceHover: "rgba(255,255,255,0.04)",
  border:       "rgba(255,255,255,0.07)",
  borderAccent: "rgba(45,212,191,0.25)",
  text:         "#ffffff",
  textSub:      "rgba(255,255,255,0.45)",
  textMuted:    "rgba(255,255,255,0.2)",
  accent:       "#2dd4bf",
  accentBg:     "rgba(45,212,191,0.08)",
  accentText:   "#0d0f12",
  green:        "#34d399",
  red:          "#f87171",
  purple:       "#a78bfa",
  orange:       "#fb923c",
  inputBg:      "rgba(255,255,255,0.04)",
  inputBorder:  "rgba(255,255,255,0.10)",
  navBg:        "rgba(13,15,18,0.85)",
  navBorder:    "rgba(255,255,255,0.05)",
  cardGlow:     "rgba(45,212,191,0.05)",
  btnPrimary:   "linear-gradient(135deg,#2dd4bf,#0891b2)",
  btnGhost:     "rgba(255,255,255,0.06)",
  btnGhostBorder:"rgba(255,255,255,0.08)",
  logoColor:    "#2dd4bf",
  labelColor:   "rgba(255,255,255,0.35)",
  divider:      "rgba(255,255,255,0.06)",
  scrollThumb:  "rgba(255,255,255,0.1)",
};

const LIGHT = {
  bg:           "#f5f3ee",
  surface:      "#ffffff",
  surfaceHover: "#fafaf8",
  border:       "rgba(0,0,0,0.08)",
  borderAccent: "rgba(22,101,52,0.3)",
  text:         "#0f1a12",
  textSub:      "rgba(15,26,18,0.5)",
  textMuted:    "rgba(15,26,18,0.3)",
  accent:       "#166534",
  accentBg:     "rgba(22,101,52,0.08)",
  accentText:   "#ffffff",
  green:        "#16a34a",
  red:          "#dc2626",
  purple:       "#7c3aed",
  orange:       "#ea580c",
  inputBg:      "#ffffff",
  inputBorder:  "rgba(0,0,0,0.12)",
  navBg:        "rgba(245,243,238,0.9)",
  navBorder:    "rgba(0,0,0,0.06)",
  cardGlow:     "rgba(22,101,52,0.04)",
  btnPrimary:   "linear-gradient(135deg,#166534,#14532d)",
  btnGhost:     "rgba(15,26,18,0.05)",
  btnGhostBorder:"rgba(15,26,18,0.12)",
  logoColor:    "#7c3aed",
  labelColor:   "rgba(15,26,18,0.4)",
  divider:      "rgba(0,0,0,0.06)",
  scrollThumb:  "rgba(0,0,0,0.1)",
};

/* ─── MetricCard ─── */
const MetricCard = ({ icon: Icon, label, value, sub, t, accentKey = "accent", delay = 0 }) => {
  const color = t[accentKey] || t.accent;
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.45, ease: [0.23,1,0.32,1] }}
      style={{
        background: t.surface, border: `1px solid ${t.border}`,
        borderRadius: 14, padding: "18px 20px", display: "flex",
        flexDirection: "column", gap: 7,
        boxShadow: t === LIGHT ? "0 1px 8px rgba(0,0,0,0.06)" : "none",
      }}
    >
      <div style={{ display:"flex", alignItems:"center", gap:7 }}>
        <Icon size={13} color={color} />
        <span style={{ fontSize:10, letterSpacing:"0.12em", textTransform:"uppercase",
          color: t.labelColor, fontFamily:"'DM Mono',monospace" }}>{label}</span>
      </div>
      <div style={{ fontSize:26, fontWeight:700, color:t.text,
        fontFamily:"'Cormorant Garamond',serif", letterSpacing:"-0.02em" }}>{value}</div>
      {sub && <div style={{ fontSize:12, color, fontFamily:"'DM Mono',monospace" }}>{sub}</div>}
    </motion.div>
  );
};

/* ════════════════════ MAIN ════════════════════ */
export default function StockSearch() {
  const [dark, setDark] = useState(true);
  const t = dark ? DARK : LIGHT;

  const [symbol, setSymbol]                   = useState("");
  const [stockData, setStockData]             = useState(null);
  const [loading, setLoading]                 = useState(false);
  const [portfolio, setPortfolio]             = useState([
    { ticker:"AAPL", weight:0.6 },
    { ticker:"TSLA", weight:0.4 },
  ]);
  const [simResults, setSimResults]           = useState(null);
  const [initialInv, setInitialInv]           = useState(10000);
  const [horizon, setHorizon]                 = useState(1);
  const [target, setTarget]                   = useState(12000);
  const [mcLoading, setMcLoading]             = useState(false);
  const [activeNav, setActiveNav]             = useState("Analytics");
  const [savedPortfolios, setSavedPortfolios] = useState([]);
  const [saveMsg, setSaveMsg]                 = useState("");
  const [showSaved, setShowSaved]             = useState(false);
  const [glowPos, setGlowPos]                 = useState({ x:50, y:50 });
  const heroRef = useRef(null);

  /* mouse glow (dark only) */
  useEffect(() => {
    if (!dark) return;
    const move = (e) => {
      if (!heroRef.current) return;
      const r = heroRef.current.getBoundingClientRect();
      setGlowPos({ x:((e.clientX-r.left)/r.width)*100, y:((e.clientY-r.top)/r.height)*100 });
    };
    window.addEventListener("mousemove", move);
    return () => window.removeEventListener("mousemove", move);
  }, [dark]);

  const sum = (arr) => arr.reduce((a,b) => a+b, 0);

  /* ── API ── */
  const searchStock = async () => {
    if (!symbol) return;
    setLoading(true);
    try {
      const res = await axios.get(`${API_BASE}/stock/${symbol}`);
      if (res.data?.error) { alert(res.data.error); setStockData(null); }
      else {
        setStockData(res.data);
        if (!portfolio.find(p => p.ticker === symbol.toUpperCase())) {
          const w = 1/(portfolio.length+1);
          setPortfolio([...portfolio.map(p=>({...p,weight:w})),{ticker:symbol.toUpperCase(),weight:w}]);
        }
      }
    } catch { alert("Error fetching stock data."); setStockData(null); }
    setLoading(false);
  };

  const runSim = async () => {
    setMcLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/simulate`, {
        tickers: portfolio.map(p=>p.ticker),
        weights: portfolio.map(p=>p.weight),
        initial_investment: initialInv,
        years: horizon,
        target_amount: target,
      });
      if (res.data?.error) { alert(res.data.error); setSimResults(null); }
      else setSimResults(res.data);
    } catch { alert("Simulation failed."); setSimResults(null); }
    setMcLoading(false);
  };

  const addStock    = (tk) => {
    if (portfolio.find(p=>p.ticker===tk)) return;
    const w = 1/(portfolio.length+1);
    setPortfolio([...portfolio.map(p=>({...p,weight:w})),{ticker:tk,weight:w}]);
  };
  const removeStock = (tk) => {
    if (portfolio.length<=1) return;
    const next = portfolio.filter(p=>p.ticker!==tk);
    const w = 1/next.length;
    setPortfolio(next.map(p=>({...p,weight:w})));
  };
  const updateWeight = (tk,v) => setPortfolio(portfolio.map(p=>p.ticker===tk?{...p,weight:v}:p));
  const autoBalance  = () => { const w=1/portfolio.length; setPortfolio(portfolio.map(p=>({...p,weight:w}))); };

  const loadSavedPortfolios = async () => {
    try {
      const res = await axios.get(`${API_BASE}/portfolios`);
      setSavedPortfolios(res.data || []);
      setShowSaved(true);
    } catch { setSavedPortfolios([]); }
  };

  const savePortfolio = async () => {
    const name = prompt("Portfolio name:");
    if (!name) return;
    try {
      await axios.post(`${API_BASE}/portfolios`, {
        name,
        holdings: portfolio.map(p => ({ ticker: p.ticker, weight: p.weight })),
        session_id: "default",
      });
      setSaveMsg("✓ Saved!");
      setTimeout(() => setSaveMsg(""), 2500);
    } catch { setSaveMsg("Save failed"); setTimeout(() => setSaveMsg(""), 2500); }
  };

  const loadPortfolio = (p) => {
    setPortfolio(p.holdings);
    setShowSaved(false);
  };

  const successProb = simResults?.final_values && target
    ? ((simResults.final_values.filter(v=>v>=target).length / simResults.final_values.length)*100).toFixed(1)
    : null;

  /* ── shared style helpers ── */
  const card  = (extra={}) => ({
    background: t.surface, border:`1px solid ${t.border}`, borderRadius:18,
    padding:34, marginBottom:18,
    boxShadow: dark ? "none" : "0 2px 16px rgba(0,0,0,0.05)",
    ...extra,
  });
  const inp   = (extra={}) => ({
    width:"100%", padding:"13px 15px",
    background:t.inputBg, border:`1px solid ${t.inputBorder}`,
    borderRadius:11, color:t.text, fontSize:14, outline:"none",
    transition:"border-color 0.2s", fontFamily:"inherit", boxSizing:"border-box", ...extra,
  });
  const label = { fontSize:10, letterSpacing:"0.12em", textTransform:"uppercase",
    color:t.labelColor, marginBottom:7, display:"block", fontFamily:"'DM Mono',monospace" };
  const divider = { height:1, background:t.divider, margin:"24px 0" };

  const btnPrimary = {
    padding:"13px 26px", borderRadius:11, border:"none", cursor:"pointer",
    fontSize:13, fontWeight:600, letterSpacing:"0.04em",
    display:"flex", alignItems:"center", gap:8,
    background: t.btnPrimary, color: t.accentText,
    boxShadow: dark ? "0 0 20px rgba(45,212,191,0.2)" : "0 2px 12px rgba(22,101,52,0.25)",
    fontFamily:"inherit",
  };
  const btnGhost = {
    padding:"13px 26px", borderRadius:11, cursor:"pointer",
    fontSize:13, fontWeight:500, letterSpacing:"0.03em",
    display:"flex", alignItems:"center", gap:8,
    background: t.btnGhost, color: t.textSub,
    border:`1px solid ${t.btnGhostBorder}`, fontFamily:"inherit",
  };
  const chip = (active) => ({
    padding:"6px 13px", borderRadius:99, fontSize:12,
    fontFamily:"'DM Mono',monospace", letterSpacing:"0.05em",
    cursor:"pointer", border:"1px solid",
    background: active ? t.accentBg : "transparent",
    borderColor: active ? t.borderAccent : t.border,
    color: active ? t.accent : t.textSub,
    transition:"all 0.15s",
  });

  return (
    <div ref={heroRef} style={{ minHeight:"100vh", background:t.bg, color:t.text,
      fontFamily:"'DM Sans',system-ui,sans-serif", position:"relative", overflowX:"hidden",
      transition:"background 0.4s, color 0.4s" }}>

      {/* noise grain — dark only */}
      {dark && <div style={{ position:"fixed", inset:0, zIndex:0, pointerEvents:"none",
        backgroundImage:`url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.04'/%3E%3C/svg%3E")`,
        opacity:0.35 }} />}

      {/* cursor glow — dark only */}
      {dark && <div style={{ position:"fixed", inset:0, zIndex:0, pointerEvents:"none",
        background:`radial-gradient(560px circle at ${glowPos.x}% ${glowPos.y}%, rgba(45,212,191,0.06) 0%, transparent 70%)`,
        transition:"background 0.08s" }} />}

      {/* light mode decorative blob */}
      {!dark && <>
        <div style={{ position:"fixed", top:-120, right:-120, width:500, height:500, borderRadius:"50%",
          background:"radial-gradient(circle, rgba(124,58,237,0.06) 0%, transparent 70%)", zIndex:0, pointerEvents:"none" }} />
        <div style={{ position:"fixed", bottom:-100, left:-100, width:400, height:400, borderRadius:"50%",
          background:"radial-gradient(circle, rgba(22,101,52,0.06) 0%, transparent 70%)", zIndex:0, pointerEvents:"none" }} />
      </>}

      {/* ── NAV ── */}
      <nav style={{ position:"sticky", top:0, zIndex:100, display:"flex", alignItems:"center",
        justifyContent:"space-between", padding:"0 40px", height:62,
        background:t.navBg, backdropFilter:"blur(20px)",
        borderBottom:`1px solid ${t.navBorder}`, transition:"background 0.4s, border-color 0.4s" }}>

        <div style={{ fontFamily:"'Cormorant Garamond',serif", fontSize:24, fontWeight:700,
          letterSpacing:"-0.03em", color:t.text }}>
          Monte<span style={{ color:t.logoColor }}>Fi</span>
        </div>

        <div style={{ display:"flex", gap:28 }}>
          {["Portfolio","Analytics","Markets"].map(n => (
            <span key={n} style={{ fontSize:13, cursor:"pointer", padding:"4px 0",
              color: activeNav===n ? t.accent : t.textSub,
              borderBottom: activeNav===n ? `1px solid ${t.accent}` : "1px solid transparent",
              transition:"all 0.2s", fontWeight: activeNav===n ? 500 : 400 }}
              onClick={() => {
                setActiveNav(n);
                const sectionMap = { Portfolio: "portfolio-section", Analytics: "sim-section", Markets: "market-section" };
                document.getElementById(sectionMap[n])?.scrollIntoView({ behavior: "smooth" });
              }}>{n}</span>
          ))}
        </div>

        <div style={{ display:"flex", alignItems:"center", gap:12 }}>
          <div style={{ display:"flex", alignItems:"center", gap:7 }}>
            <div style={{ width:7, height:7, borderRadius:"50%", background:t.green,
              boxShadow:`0 0 7px ${t.green}`, animation:"pulse 2s infinite" }} />
            <span style={{ fontSize:11, color:t.textMuted, fontFamily:"'DM Mono',monospace" }}>LIVE</span>
          </div>

          {/* ── THEME TOGGLE ── */}
          <motion.button
            onClick={() => setDark(d => !d)}
            whileHover={{ scale:1.05 }} whileTap={{ scale:0.92 }}
            style={{ width:40, height:40, borderRadius:12, border:`1px solid ${t.border}`,
              background:t.surface, cursor:"pointer", display:"flex", alignItems:"center",
              justifyContent:"center", color:t.textSub, transition:"all 0.3s" }}
          >
            {dark ? <Sun size={16} color="#fbbf24" /> : <Moon size={16} color={t.textSub} />}
          </motion.button>
        </div>
      </nav>

      {/* ── CONTENT ── */}
      <div style={{ position:"relative", zIndex:1, maxWidth:1080, margin:"0 auto", padding:"0 22px 80px" }}>

        {/* HERO */}
        <motion.div style={{ padding:"72px 0 52px" }}
          initial={{ opacity:0, y:28 }} animate={{ opacity:1, y:0 }}
          transition={{ duration:0.75, ease:[0.23,1,0.32,1] }}>
          <div style={{ fontSize:10, letterSpacing:"0.2em", textTransform:"uppercase",
            color:t.accent, fontFamily:"'DM Mono',monospace", marginBottom:14 }}>
            Quantitative Analytics Platform
          </div>
          <h1 style={{ fontFamily:"'Cormorant Garamond',serif",
            fontSize:"clamp(44px,6vw,76px)", fontWeight:700,
            lineHeight:1.05, letterSpacing:"-0.03em", margin:"0 0 18px",
            color:t.text }}>
            Redefining<br />
            <span style={{ color: dark ? "#2dd4bf" : t.purple, fontStyle:"italic" }}>Wealth</span>
          </h1>
          <p style={{ fontSize:15, color:t.textSub, maxWidth:460, lineHeight:1.7, marginBottom:28 }}>
            Experience a new era of capital management where quantitative simulation meets high-performance analytics.
          </p>
          <div style={{ display:"flex", gap:11 }}>
            <motion.button style={btnPrimary} whileHover={{ scale:1.02 }} whileTap={{ scale:0.97 }}
              onClick={() => document.getElementById("sim-section")?.scrollIntoView({ behavior:"smooth" })}>
              Get Started <ChevronRight size={14} />
            </motion.button>
            <motion.button style={btnGhost} whileHover={{ scale:1.01 }} whileTap={{ scale:0.97 }}
              onClick={() => document.getElementById("portfolio-section")?.scrollIntoView({ behavior: "smooth" })}>
              Explore Strategy
            </motion.button>
          </div>
        </motion.div>

        {/* STOCK SEARCH */}
        <motion.div id="market-section" style={card()} initial={{ opacity:0, y:18 }} animate={{ opacity:1, y:0 }}
          transition={{ delay:0.12, duration:0.55 }}>
          <div style={{ fontFamily:"'Cormorant Garamond',serif", fontSize:22, fontWeight:600,
            letterSpacing:"-0.02em", marginBottom:3 }}>Market Intelligence</div>
          <div style={{ fontSize:13, color:t.textSub, marginBottom:22 }}>Fetch real-time price data for any ticker</div>

          <div style={{ display:"flex", gap:10, marginBottom:14 }}>
            <div style={{ position:"relative", flex:1 }}>
              <Search size={14} color={t.textMuted} style={{ position:"absolute", left:14, top:"50%", transform:"translateY(-50%)" }} />
              <input style={{ ...inp(), paddingLeft:40, fontFamily:"'DM Mono',monospace", letterSpacing:"0.06em" }}
                placeholder="AAPL · TSLA · MSFT · NVDA"
                value={symbol} onChange={e => setSymbol(e.target.value.toUpperCase())}
                onKeyDown={e => e.key==="Enter" && searchStock()} />
            </div>
            <motion.button style={{ ...btnPrimary, opacity: loading||!symbol ? 0.45 : 1 }}
              onClick={searchStock} disabled={loading||!symbol}
              whileHover={{ scale:1.02 }} whileTap={{ scale:0.97 }}>
              {loading ? <RefreshCw size={14} style={{ animation:"spin 1s linear infinite" }} /> : <Search size={14} />}
              {loading ? "Fetching…" : "Search"}
            </motion.button>
          </div>

          <div style={{ display:"flex", gap:7, flexWrap:"wrap" }}>
            {["AAPL","TSLA","GOOGL","AMZN","MSFT","NVDA"].map(q => (
              <motion.button key={q} style={chip(false)}
                onClick={() => { setSymbol(q); addStock(q); }}
                whileHover={{ scale:1.05 }} whileTap={{ scale:0.95 }}>{q}</motion.button>
            ))}
          </div>

          <AnimatePresence>
            {stockData && (
              <motion.div initial={{ opacity:0, height:0, marginTop:0 }}
                animate={{ opacity:1, height:"auto", marginTop:20 }} exit={{ opacity:0, height:0 }}
                style={{ overflow:"hidden" }}>
                <div style={{ background:t.accentBg, border:`1px solid ${t.borderAccent}`,
                  borderRadius:13, padding:"18px 22px", display:"flex",
                  justifyContent:"space-between", alignItems:"center" }}>
                  <div>
                    <div style={{ fontSize:10, letterSpacing:"0.14em", color:t.accent,
                      fontFamily:"'DM Mono',monospace", marginBottom:3 }}>
                      {stockData.ticker} · USD · REAL-TIME
                    </div>
                    <div style={{ fontFamily:"'Cormorant Garamond',serif", fontSize:40,
                      fontWeight:700, letterSpacing:"-0.02em", color:t.text }}>
                      ${Number(stockData.price).toLocaleString()}
                    </div>
                  </div>
                  <motion.button style={{ ...btnPrimary, fontSize:12, padding:"9px 14px" }}
                    onClick={() => addStock(stockData.ticker)} whileHover={{ scale:1.03 }}>
                    <Plus size={12} /> Add to Portfolio
                  </motion.button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>

        {/* PORTFOLIO BUILDER */}
        <motion.div id="portfolio-section" style={card()} initial={{ opacity:0, y:18 }}
          animate={{ opacity:1, y:0 }} transition={{ delay:0.22, duration:0.55 }}>
          <div style={{ fontFamily:"'Cormorant Garamond',serif", fontSize:22, fontWeight:600,
            letterSpacing:"-0.02em", marginBottom:3 }}>Portfolio Builder</div>
          <div style={{ fontSize:13, color:t.textSub, marginBottom:22 }}>Configure holdings and run Monte Carlo simulation</div>

          {/* quick add */}
          <div style={{ marginBottom:18 }}>
            <span style={label}>Quick Add</span>
            <div style={{ display:"flex", gap:7, flexWrap:"wrap" }}>
              {["GOOGL","MSFT","AMZN","NVDA","META","NFLX"].map(s => (
                <motion.button key={s} style={chip(!!portfolio.find(p=>p.ticker===s))}
                  onClick={() => addStock(s)} whileHover={{ scale:1.04 }} whileTap={{ scale:0.95 }}>
                  {portfolio.find(p=>p.ticker===s) ? "✓ " : ""}{s}
                </motion.button>
              ))}
            </div>
          </div>

          <div style={divider} />
          <span style={label}>Holdings & Weights</span>

          {portfolio.map((stock,i) => (
            <motion.div key={stock.ticker}
              initial={{ opacity:0, x:-8 }} animate={{ opacity:1, x:0 }}
              transition={{ delay:i*0.04 }}
              style={{ display:"flex", alignItems:"center", gap:11, padding:"13px 15px",
                borderRadius:11, marginBottom:9, background:t.inputBg,
                border:`1px solid ${t.border}` }}>
              <div style={{ width:34, height:34, borderRadius:9, background:t.accentBg,
                border:`1px solid ${t.borderAccent}`, display:"flex", alignItems:"center",
                justifyContent:"center", flexShrink:0 }}>
                <span style={{ fontSize:9, fontFamily:"'DM Mono',monospace", color:t.accent }}>
                  {stock.ticker.slice(0,2)}
                </span>
              </div>
              <span style={{ fontFamily:"'DM Mono',monospace", fontSize:12,
                letterSpacing:"0.05em", width:52, flexShrink:0, color:t.text }}>
                {stock.ticker}
              </span>
              <input type="range" min="0" max="100" value={Math.round(stock.weight*100)}
                onChange={e => updateWeight(stock.ticker, e.target.value/100)}
                style={{ flex:1, accentColor:t.accent, cursor:"pointer" }} />
              <div style={{ display:"flex", alignItems:"center", gap:4 }}>
                <input type="number" min="0" max="100" value={Math.round(stock.weight*100)}
                  onChange={e => updateWeight(stock.ticker, Math.min(100,Math.max(0,parseInt(e.target.value)||0))/100)}
                  style={{ width:48, padding:"5px 7px", background:t.surface,
                    border:`1px solid ${t.border}`, borderRadius:7, color:t.text,
                    fontSize:12, textAlign:"center", fontFamily:"'DM Mono',monospace", outline:"none" }} />
                <span style={{ fontSize:11, color:t.textMuted }}>%</span>
              </div>
              {portfolio.length > 1 && (
                <button onClick={() => removeStock(stock.ticker)}
                  style={{ background:"none", border:"none", cursor:"pointer", padding:3,
                    color:t.textMuted, transition:"color 0.15s" }}
                  onMouseEnter={e => e.currentTarget.style.color="#f87171"}
                  onMouseLeave={e => e.currentTarget.style.color=t.textMuted}>
                  <X size={13} />
                </button>
              )}
            </motion.div>
          ))}

          <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:18 }}>
            <span style={{ fontSize:12, fontFamily:"'DM Mono',monospace",
              color: Math.abs(sum(portfolio.map(p=>p.weight))-1)>0.01 ? t.red : t.green }}>
              TOTAL: {(sum(portfolio.map(p=>p.weight))*100).toFixed(1)}%
              {Math.abs(sum(portfolio.map(p=>p.weight))-1)>0.01 && " — must equal 100%"}
            </span>
            <div style={{ display:"flex", gap:8, alignItems:"center" }}>
              <button style={{ ...btnGhost, fontSize:11, padding:"7px 13px" }} onClick={autoBalance}>
                <RefreshCw size={11} /> Auto-Balance
              </button>
              <motion.button style={{ ...btnGhost, fontSize:11, padding:"7px 13px" }}
                onClick={savePortfolio} whileHover={{ scale:1.03 }}>
                💾 Save
              </motion.button>
              <motion.button style={{ ...btnGhost, fontSize:11, padding:"7px 13px" }}
                onClick={loadSavedPortfolios} whileHover={{ scale:1.03 }}>
                📂 Load
              </motion.button>
              {saveMsg && <span style={{ fontSize:11, color:t.green, fontFamily:"'DM Mono',monospace" }}>{saveMsg}</span>}
            </div>
          </div>

          <div style={divider} />

          {/* sim controls */}
          <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fit,minmax(170px,1fr))",
            gap:13, marginBottom:22 }}>
            {[
              { label:"Initial Investment", val:initialInv, set:setInitialInv, prefix:"$" },
              { label:"Target Amount", val:target, set:setTarget, prefix:"$" },
            ].map(({ label:lb, val, set, prefix }) => (
              <div key={lb}>
                <span style={label}>{lb}</span>
                <div style={{ position:"relative" }}>
                  <span style={{ position:"absolute", left:13, top:"50%",
                    transform:"translateY(-50%)", color:t.textMuted, fontSize:13 }}>{prefix}</span>
                  <input type="number" value={val} onChange={e => set(Number(e.target.value))}
                    style={{ ...inp(), paddingLeft:26 }} />
                </div>
              </div>
            ))}
            <div>
              <span style={label}>Time Horizon</span>
              <select value={horizon} onChange={e => setHorizon(Number(e.target.value))} style={inp({ cursor:"pointer" })}>
                {[1,3,5,10].map(y => <option key={y} value={y}>{y} Year{y>1?"s":""}</option>)}
              </select>
            </div>
          </div>

          <motion.button style={{ ...btnPrimary, width:"100%", justifyContent:"center",
            padding:"15px 0", fontSize:14, letterSpacing:"0.07em",
            opacity: mcLoading ? 0.6 : 1 }}
            onClick={runSim} disabled={mcLoading}
            whileHover={!mcLoading ? { scale:1.01 } : {}}
            whileTap={!mcLoading ? { scale:0.98 } : {}}>
            {mcLoading
              ? <><RefreshCw size={15} style={{ animation:"spin 1s linear infinite" }} /> Running 10,000 Simulations…</>
              : <><Cpu size={15} /> Run Monte Carlo Simulation <ArrowUpRight size={13} /></>}
          </motion.button>
        </motion.div>

        {/* RESULTS */}
        <AnimatePresence>
          {simResults && !simResults.error && (
            <motion.div initial={{ opacity:0, y:28 }} animate={{ opacity:1, y:0 }}
              exit={{ opacity:0 }} transition={{ duration:0.6, ease:[0.23,1,0.32,1] }}>

              <div style={{ marginBottom:14 }}>
                <div style={{ fontSize:10, letterSpacing:"0.18em", textTransform:"uppercase",
                  color:t.accent, fontFamily:"'DM Mono',monospace", marginBottom:5 }}>
                  Simulation Complete · {(simResults.simulation_count||10000).toLocaleString()} Paths
                </div>
                <h2 style={{ fontFamily:"'Cormorant Garamond',serif", fontSize:30, fontWeight:700,
                  margin:"0 0 18px", letterSpacing:"-0.02em", color:t.text }}>Portfolio Analysis</h2>
              </div>

              <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fit,minmax(195px,1fr))", gap:11, marginBottom:11 }}>
                <MetricCard t={t} icon={BarChart3} label="Expected Value"
                  value={`$${simResults.expected_value?.toLocaleString(undefined,{maximumFractionDigits:0})}`}
                  sub={`${simResults.expected_return_pct != null ? "+" + simResults.expected_return_pct.toFixed(1) : ((simResults.expected_value-initialInv)/initialInv*100).toFixed(1)}% return`}
                  delay={0} />
                <MetricCard t={t} icon={TrendingUp} label="Bull Case (p90)" accentKey="green"
                  value={`$${(simResults.confidence_intervals?.p90 ?? simResults.best_case)?.toLocaleString(undefined,{maximumFractionDigits:0})}`}
                  sub="Top 10% outcomes" delay={0.05} />
                <MetricCard t={t} icon={TrendingDown} label="Bear Case (p10)" accentKey="red"
                  value={`$${(simResults.confidence_intervals?.p10 ?? simResults.worst_case)?.toLocaleString(undefined,{maximumFractionDigits:0})}`}
                  sub="Bottom 10% outcomes" delay={0.1} />
                {successProb && <MetricCard t={t} icon={Target} label="Success Probability" accentKey="purple"
                  value={`${successProb}%`} sub={`Reach $${target.toLocaleString()}`} delay={0.15} />}
              </div>

              <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fit,minmax(195px,1fr))", gap:11, marginBottom:11 }}>
                {simResults.sharpe_ratio != null && <MetricCard t={t} icon={Activity} label="Sharpe Ratio"
                  value={simResults.sharpe_ratio.toFixed(2)}
                  sub={simResults.sharpe_ratio>2?"Excellent":simResults.sharpe_ratio>1?"Good":"Below avg"} delay={0.2} />}
                {simResults.var?.var_95_pct != null && <MetricCard t={t} icon={ShieldAlert} label="VaR 95%" accentKey="orange"
                  value={`${simResults.var.var_95_pct.toFixed(1)}%`}
                  sub={`≈$${Math.abs(simResults.var.var_95_amount).toLocaleString(undefined,{maximumFractionDigits:0})} max loss`} delay={0.25} />}
                {simResults.max_drawdown_pct != null && <MetricCard t={t} icon={TrendingDown} label="Max Drawdown" accentKey="red"
                  value={`${simResults.max_drawdown_pct.toFixed(1)}%`} sub="Peak-to-trough" delay={0.3} />}
                {simResults.beta != null && <MetricCard t={t} icon={Zap} label="Portfolio Beta"
                  value={simResults.beta.toFixed(2)}
                  sub={simResults.beta>1?"More volatile than mkt":"Less volatile than mkt"} delay={0.35} />}
                {simResults.prob_profit_pct != null && <MetricCard t={t} icon={TrendingUp} label="Prob. of Profit" accentKey="green"
                  value={`${simResults.prob_profit_pct.toFixed(1)}%`} sub="Scenarios ending positive" delay={0.4} />}
                {simResults.annualised_return_pct != null && <MetricCard t={t} icon={DollarSign} label="Hist. Annual Return"
                  value={`${simResults.annualised_return_pct.toFixed(1)}%`} sub="5yr historical avg" delay={0.45} />}
              </div>

              {/* AI analysis — always visible, shows placeholder if Gemini key not set */}
              <motion.div initial={{ opacity:0 }} animate={{ opacity:1 }} transition={{ delay:0.5 }}
                style={{ background:t.accentBg, border:`1px solid ${t.borderAccent}`,
                  borderRadius:14, padding:"22px 26px", marginBottom:11 }}>
                <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", marginBottom:11 }}>
                  <div style={{ display:"flex", alignItems:"center", gap:8 }}>
                    <Cpu size={13} color={t.accent} />
                    <span style={{ fontSize:10, letterSpacing:"0.12em", textTransform:"uppercase",
                      color:t.accent, fontFamily:"'DM Mono',monospace" }}>AI Risk Analysis</span>
                  </div>
                  <span style={{ fontSize:10, color:t.textMuted, fontFamily:"'DM Mono',monospace" }}>
                    {simResults.ai_analysis ? "GEMINI · LANGCHAIN" : "KEY NOT SET"}
                  </span>
                </div>
                {simResults.ai_analysis ? (
                  <p style={{ fontSize:14, lineHeight:1.75, color:t.textSub, margin:0 }}>
                    {simResults.ai_analysis}
                  </p>
                ) : (
                  <div>
                    <p style={{ fontSize:14, lineHeight:1.75, color:t.textSub, margin:"0 0 12px" }}>
                      {(() => {
                        const s = simResults.sharpe_ratio;
                        const v = simResults.var?.var_95_pct;
                        const b = simResults.beta;
                        const dd = simResults.max_drawdown_pct;
                        const ret = simResults.expected_return_pct;
                        let analysis = `This portfolio has an expected return of ${ret?.toFixed(1)}% with `;
                        analysis += s > 2 ? `an excellent Sharpe ratio of ${s?.toFixed(2)}, indicating strong risk-adjusted returns. ` :
                                    s > 1 ? `a good Sharpe ratio of ${s?.toFixed(2)}, suggesting solid risk-adjusted performance. ` :
                                            `a below-average Sharpe ratio of ${s?.toFixed(2)}, meaning returns don't fully justify the risk taken. `;
                        analysis += `At 95% confidence, maximum expected loss is ${Math.abs(v)?.toFixed(1)}% (≈$${Math.abs(simResults.var?.var_95_amount)?.toLocaleString(undefined,{maximumFractionDigits:0})}). `;
                        analysis += b > 1.5 ? `Beta of ${b?.toFixed(2)} indicates significantly higher volatility than the market — this portfolio amplifies market moves. ` :
                                    b > 1   ? `Beta of ${b?.toFixed(2)} means slightly more volatile than the S&P 500. ` :
                                              `Beta of ${b?.toFixed(2)} shows lower sensitivity to market swings than the S&P 500. `;
                        analysis += `Median max drawdown of ${Math.abs(dd)?.toFixed(1)}% represents the typical worst peak-to-trough decline to expect.`;
                        return analysis;
                      })()}
                    </p>
                    <div style={{ padding:"8px 12px", background:`rgba(0,0,0,0.15)`, borderRadius:8,
                      display:"flex", alignItems:"center", gap:8 }}>
                      <span style={{ fontSize:11, color:t.textMuted }}>
                        💡 Add <code style={{ fontFamily:"'DM Mono',monospace", color:t.accent }}>GEMINI_API_KEY</code> to your 
                        <code style={{ fontFamily:"'DM Mono',monospace", color:t.accent }}> .env</code> file for AI-generated analysis
                      </span>
                    </div>
                  </div>
                )}
              </motion.div>

              {/* distribution bars */}
              {simResults.final_values?.length > 0 && (
                <motion.div initial={{ opacity:0 }} animate={{ opacity:1 }} transition={{ delay:0.55 }}
                  style={{ ...card(), padding:"18px 22px", marginBottom:0 }}>
                  <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center" }}>
                    <span style={label}>Simulation Distribution</span>
                    <span style={{ fontSize:10, color:t.textMuted, fontFamily:"'DM Mono',monospace" }}>
                      {simResults.final_values.length} paths shown
                    </span>
                  </div>
                  <div style={{ display:"flex", gap:3, alignItems:"flex-end", height:58, marginTop:8 }}>
                    {(() => {
                      const vals = simResults.final_values.slice(0,60);
                      const mn=Math.min(...vals), mx=Math.max(...vals), rng=mx-mn||1;
                      return vals.map((v,i) => (
                        <div key={i} style={{ flex:1, borderRadius:3,
                          height:`${((v-mn)/rng)*100}%`, minHeight:2,
                          background: v>=initialInv
                            ? (dark?"rgba(45,212,191,0.5)":"rgba(22,101,52,0.4)")
                            : (dark?"rgba(248,113,113,0.45)":"rgba(220,38,38,0.35)"),
                        }} />
                      ));
                    })()}
                  </div>
                  <div style={{ display:"flex", justifyContent:"space-between", marginTop:5 }}>
                    <span style={{ fontSize:9, color:t.textMuted, fontFamily:"'DM Mono',monospace" }}>BEAR</span>
                    <span style={{ fontSize:9, color:t.textMuted, fontFamily:"'DM Mono',monospace" }}>BULL</span>
                  </div>
                </motion.div>
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {/* FEATURE CARDS */}
        <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fit,minmax(230px,1fr))", gap:11, marginTop:18 }}>
          {[
            { icon:DollarSign, title:"Real-time Data",        body:"Live market prices via yfinance — no API key, no rate limits.",                       accentKey:"accent" },
            { icon:BarChart3,  title:"Quantitative Analytics", body:"Sharpe ratio, VaR, max drawdown, beta — the metrics hedge funds rely on.",           accentKey:"purple" },
            { icon:Cpu,        title:"AI Risk Analyst",        body:"LangChain + Gemini translates your metrics into plain-English risk summaries.",       accentKey:"green" },
          ].map(({ icon:Icon, title, body, accentKey },i) => {
            const color = t[accentKey]||t.accent;
            return (
              <motion.div key={title} style={{ ...card(), marginBottom:0 }}
                initial={{ opacity:0, y:14 }} animate={{ opacity:1, y:0 }}
                transition={{ delay:0.08*i, duration:0.5 }}
                whileHover={{ borderColor:`${color}40`, transition:{ duration:0.2 } }}>
                <div style={{ width:34, height:34, borderRadius:9, background:`${color}15`,
                  border:`1px solid ${color}30`, display:"flex", alignItems:"center",
                  justifyContent:"center", marginBottom:13 }}>
                  <Icon size={15} color={color} />
                </div>
                <div style={{ fontSize:15, fontWeight:600, marginBottom:5, color:t.text }}>{title}</div>
                <div style={{ fontSize:13, color:t.textSub, lineHeight:1.65 }}>{body}</div>
              </motion.div>
            );
          })}
        </div>

        {/* SAVED PORTFOLIOS MODAL */}
        <AnimatePresence>
          {showSaved && (
            <motion.div
              initial={{ opacity:0 }} animate={{ opacity:1 }} exit={{ opacity:0 }}
              style={{ position:"fixed", inset:0, zIndex:200,
                background:"rgba(0,0,0,0.6)", backdropFilter:"blur(4px)",
                display:"flex", alignItems:"center", justifyContent:"center" }}
              onClick={() => setShowSaved(false)}
            >
              <motion.div
                initial={{ scale:0.9, y:20 }} animate={{ scale:1, y:0 }}
                onClick={e => e.stopPropagation()}
                style={{ background:t.surface, border:`1px solid ${t.border}`,
                  borderRadius:18, padding:28, width:420, maxHeight:"70vh",
                  overflowY:"auto", boxShadow:"0 20px 60px rgba(0,0,0,0.4)" }}
              >
                <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:18 }}>
                  <div style={{ fontFamily:"'Cormorant Garamond',serif", fontSize:22, fontWeight:700, color:t.text }}>
                    Saved Portfolios
                  </div>
                  <button onClick={() => setShowSaved(false)}
                    style={{ background:"none", border:"none", cursor:"pointer", color:t.textMuted, fontSize:18 }}>✕</button>
                </div>
                {savedPortfolios.length === 0 ? (
                  <div style={{ fontSize:14, color:t.textSub, textAlign:"center", padding:"20px 0" }}>
                    No saved portfolios yet. Build a portfolio and click 💾 Save.
                  </div>
                ) : savedPortfolios.map(p => (
                  <div key={p.id} style={{ background:t.inputBg, border:`1px solid ${t.border}`,
                    borderRadius:12, padding:"14px 16px", marginBottom:10 }}>
                    <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:8 }}>
                      <div style={{ fontSize:14, fontWeight:600, color:t.text }}>{p.name}</div>
                      <motion.button
                        onClick={() => loadPortfolio(p)}
                        style={{ ...btnGhost, fontSize:11, padding:"5px 12px" }}
                        whileHover={{ scale:1.03 }}>
                        Load
                      </motion.button>
                    </div>
                    <div style={{ display:"flex", gap:7, flexWrap:"wrap" }}>
                      {p.holdings.map(h => (
                        <span key={h.ticker} style={{ fontSize:11, padding:"2px 8px",
                          borderRadius:99, background:t.accentBg,
                          color:t.accent, fontFamily:"'DM Mono',monospace" }}>
                          {h.ticker} {(h.weight*100).toFixed(0)}%
                        </span>
                      ))}
                    </div>
                    <div style={{ fontSize:11, color:t.textMuted, marginTop:6, fontFamily:"'DM Mono',monospace" }}>
                      Saved {new Date(p.created_at).toLocaleDateString()}
                    </div>
                  </div>
                ))}
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* FOOTER */}
        <div style={{ textAlign:"center", marginTop:56, paddingTop:26,
          borderTop:`1px solid ${t.divider}` }}>
          <div style={{ fontFamily:"'Cormorant Garamond',serif", fontSize:20, marginBottom:5, color:t.text }}>
            Monte<span style={{ color:t.logoColor }}>Fi</span>
          </div>
          <p style={{ fontSize:11, color:t.textMuted, fontFamily:"'DM Mono',monospace" }}>
            React · FastAPI · LangChain · yfinance · peewee
          </p>
        </div>
      </div>

      {/* FLOATING CHATBOT */}
      <Chatbot t={t} API_BASE={API_BASE} />

      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;0,700;1,400;1,700&family=DM+Sans:wght@400;500;600&family=DM+Mono:wght@400;500&display=swap');
        @keyframes spin  { to { transform: rotate(360deg); } }
        @keyframes pulse { 0%,100%{ opacity:1; } 50%{ opacity:0.35; } }
        input[type=range]{ -webkit-appearance:none; height:3px; border-radius:99px; background:rgba(128,128,128,0.2); }
        input[type=range]::-webkit-slider-thumb{ -webkit-appearance:none; width:13px; height:13px; border-radius:50%; background:#2dd4bf; cursor:pointer; box-shadow:0 0 7px rgba(45,212,191,0.45); }
        input:focus, select:focus { border-color:rgba(45,212,191,0.4) !important; box-shadow:0 0 0 3px rgba(45,212,191,0.07); }
        select option { background:#1a1d21; }
        ::-webkit-scrollbar{ width:4px; }
        ::-webkit-scrollbar-track{ background:transparent; }
        ::-webkit-scrollbar-thumb{ background:rgba(128,128,128,0.2); border-radius:99px; }
      `}</style>
    </div>
  );
}

/* ══════════════════════════════════════════════════════════
   CHATBOT COMPONENT
   Floating button → expands to chat panel
   Uses POST /chat — LangChain + Gemini + DuckDuckGo news
   ══════════════════════════════════════════════════════════ */
export function Chatbot({ t, API_BASE }) {
  const [open, setOpen]       = useState(false);
  const [input, setInput]     = useState("");
  const [messages, setMessages] = useState([
    { role: "assistant", content: "Hi! I'm MonteFi's AI assistant. Ask me about financial metrics, company news (e.g. 'news about Tesla'), or how to use the platform." }
  ]);
  const [loading, setLoading] = useState(false);
  const bottomRef             = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async () => {
    if (!input.trim() || loading) return;
    const userMsg = { role: "user", content: input };
    const newHistory = [...messages, userMsg];
    setMessages(newHistory);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: input,
          history: messages.slice(-6),
        }),
      });
      const data = await res.json();

      let content = data.reply || "Sorry, I couldn't process that.";

      // Append source links if news was fetched
      if (data.sources?.length > 0) {
        content += "\n\n📰 Sources:";
        data.sources.slice(0, 3).forEach(s => {
          if (s.url) content += `\n• ${s.source}: ${s.url}`;
        });
      }

      setMessages([...newHistory, { role: "assistant", content }]);
    } catch {
      setMessages([...newHistory, {
        role: "assistant",
        content: "Connection error — make sure the backend is running on port 8000."
      }]);
    }
    setLoading(false);
  };

  const quickPrompts = [
    "What is Sharpe Ratio?",
    "News about Tesla",
    "Explain VaR 95%",
    "How do I save a portfolio?",
    "What does beta mean?",
    "News about Apple",
  ];

  return (
    <>
      {/* Floating button */}
      <motion.button
        onClick={() => setOpen(o => !o)}
        whileHover={{ scale: 1.08 }}
        whileTap={{ scale: 0.93 }}
        style={{
          position: "fixed", bottom: 28, right: 28, zIndex: 999,
          width: 52, height: 52, borderRadius: "50%", border: "none",
          background: open ? t.btnGhost : `linear-gradient(135deg, ${t.accent}, ${t.accent}cc)`,
          cursor: "pointer", display: "flex", alignItems: "center",
          justifyContent: "center",
          boxShadow: `0 4px 20px ${t.accent}44`,
          color: open ? t.textSub : t.accentText,
          transition: "all 0.3s",
        }}
      >
        {open
          ? <span style={{ fontSize: 18 }}>✕</span>
          : <span style={{ fontSize: 20 }}>💬</span>}
      </motion.button>

      {/* Chat panel */}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ duration: 0.25, ease: [0.23, 1, 0.32, 1] }}
            style={{
              position: "fixed", bottom: 92, right: 28, zIndex: 998,
              width: 360, maxHeight: 520,
              background: t.surface,
              border: `1px solid ${t.border}`,
              borderRadius: 18,
              boxShadow: `0 8px 40px rgba(0,0,0,0.3)`,
              display: "flex", flexDirection: "column",
              overflow: "hidden",
            }}
          >
            {/* Header */}
            <div style={{
              padding: "14px 18px",
              borderBottom: `1px solid ${t.border}`,
              display: "flex", alignItems: "center", gap: 10,
            }}>
              <div style={{
                width: 32, height: 32, borderRadius: "50%",
                background: t.accentBg, border: `1px solid ${t.borderAccent}`,
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: 14,
              }}>🤖</div>
              <div>
                <div style={{ fontSize: 13, fontWeight: 600, color: t.text }}>MonteFi Assistant</div>
                <div style={{ fontSize: 11, color: t.accent, fontFamily: "'DM Mono',monospace" }}>
                  Powered by Gemini · LangChain
                </div>
              </div>
              <div style={{
                marginLeft: "auto", width: 7, height: 7, borderRadius: "50%",
                background: t.green, boxShadow: `0 0 6px ${t.green}`,
                animation: "pulse 2s infinite",
              }} />
            </div>

            {/* Messages */}
            <div style={{
              flex: 1, overflowY: "auto", padding: "14px 16px",
              display: "flex", flexDirection: "column", gap: 10,
            }}>
              {messages.map((msg, i) => (
                <div key={i} style={{
                  display: "flex",
                  justifyContent: msg.role === "user" ? "flex-end" : "flex-start",
                }}>
                  <div style={{
                    maxWidth: "85%",
                    padding: "9px 13px",
                    borderRadius: msg.role === "user" ? "14px 14px 4px 14px" : "14px 14px 14px 4px",
                    background: msg.role === "user"
                      ? `linear-gradient(135deg, ${t.accent}, ${t.accent}cc)`
                      : t.inputBg,
                    border: msg.role === "user" ? "none" : `1px solid ${t.border}`,
                    color: msg.role === "user" ? t.accentText : t.text,
                    fontSize: 13,
                    lineHeight: 1.6,
                    whiteSpace: "pre-wrap",
                    wordBreak: "break-word",
                  }}>
                    {msg.content}
                  </div>
                </div>
              ))}

              {loading && (
                <div style={{ display: "flex", justifyContent: "flex-start" }}>
                  <div style={{
                    padding: "9px 14px", borderRadius: "14px 14px 14px 4px",
                    background: t.inputBg, border: `1px solid ${t.border}`,
                    display: "flex", gap: 4, alignItems: "center",
                  }}>
                    {[0, 1, 2].map(i => (
                      <div key={i} style={{
                        width: 6, height: 6, borderRadius: "50%",
                        background: t.accent, opacity: 0.6,
                        animation: `pulse 1.2s ${i * 0.2}s infinite`,
                      }} />
                    ))}
                  </div>
                </div>
              )}
              <div ref={bottomRef} />
            </div>

            {/* Quick prompts */}
            {messages.length <= 1 && (
              <div style={{
                padding: "0 12px 10px",
                display: "flex", flexWrap: "wrap", gap: 6,
              }}>
                {quickPrompts.map(p => (
                  <button key={p}
                    onClick={() => { setInput(p); }}
                    style={{
                      padding: "4px 10px", borderRadius: 99, fontSize: 11,
                      border: `1px solid ${t.border}`, background: t.inputBg,
                      color: t.textSub, cursor: "pointer", fontFamily: "inherit",
                      transition: "all 0.15s",
                    }}
                    onMouseEnter={e => { e.currentTarget.style.borderColor = t.accent; e.currentTarget.style.color = t.accent; }}
                    onMouseLeave={e => { e.currentTarget.style.borderColor = t.border; e.currentTarget.style.color = t.textSub; }}
                  >{p}</button>
                ))}
              </div>
            )}

            {/* Input */}
            <div style={{
              padding: "10px 12px",
              borderTop: `1px solid ${t.border}`,
              display: "flex", gap: 8,
            }}>
              <input
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => e.key === "Enter" && send()}
                placeholder="Ask about stocks, metrics, news…"
                style={{
                  flex: 1, padding: "9px 12px",
                  background: t.inputBg, border: `1px solid ${t.inputBorder}`,
                  borderRadius: 10, color: t.text, fontSize: 13,
                  outline: "none", fontFamily: "inherit",
                }}
              />
              <motion.button
                onClick={send}
                disabled={!input.trim() || loading}
                whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.93 }}
                style={{
                  width: 36, height: 36, borderRadius: 10, border: "none",
                  background: input.trim() && !loading
                    ? `linear-gradient(135deg, ${t.accent}, ${t.accent}cc)`
                    : t.inputBg,
                  cursor: input.trim() && !loading ? "pointer" : "not-allowed",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  color: input.trim() && !loading ? t.accentText : t.textMuted,
                  fontSize: 16, transition: "all 0.2s", flexShrink: 0,
                }}
              >↑</motion.button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
