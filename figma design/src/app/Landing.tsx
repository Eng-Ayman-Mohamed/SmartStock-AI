import { useState, useEffect } from "react";
import { useNavigate } from "react-router";
import {
  BarChart3,
  Brain,
  FileText,
  MessageSquare,
  ShieldCheck,
  Mic,
  TrendingUp,
  TrendingDown,
  Package,
  AlertTriangle,
  CheckCircle,
  ChevronRight,
  Zap,
  ArrowRight,
} from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

// ─── Data ────────────────────────────────────────────────────────────────────

const forecastData = [
  { month: "Jan", actual: 420, forecast: 440 },
  { month: "Feb", actual: 380, forecast: 395 },
  { month: "Mar", actual: 510, forecast: 490 },
  { month: "Apr", actual: 470, forecast: 480 },
  { month: "May", actual: 540, forecast: 555 },
  { month: "Jun", forecast: 620 },
  { month: "Jul", forecast: 670 },
];

// ─── Shared primitives ────────────────────────────────────────────────────────

type BadgeVariant = "ai" | "warning" | "success" | "danger";

function Badge({ children, variant = "ai" }: { children: React.ReactNode; variant?: BadgeVariant }) {
  const map: Record<BadgeVariant, { bg: string; color: string }> = {
    ai:      { bg: "#F3E5F5", color: "#391C57" },
    warning: { bg: "#FFF3E0", color: "#E65100" },
    success: { bg: "#E8F5E9", color: "#1AAE39" },
    danger:  { bg: "#FFEBEE", color: "#E53935" },
  };
  const { bg, color } = map[variant];
  return (
    <span
      style={{
        background: bg,
        color,
        fontSize: 11,
        fontWeight: 600,
        borderRadius: 999,
        padding: "3px 10px",
        display: "inline-flex",
        alignItems: "center",
        gap: 4,
        whiteSpace: "nowrap",
        letterSpacing: "0.01em",
      }}
    >
      {children}
    </span>
  );
}

function PillBtn({
  children,
  primary,
  onClick,
  small,
  white,
}: {
  children: React.ReactNode;
  primary?: boolean;
  onClick?: () => void;
  small?: boolean;
  white?: boolean;
}) {
  const [pressed, setPressed] = useState(false);
  const base = small ? "7px 18px" : "11px 24px";
  const fs = small ? 14 : 15;

  if (white) {
    return (
      <button
        onClick={onClick}
        onMouseDown={() => setPressed(true)}
        onMouseUp={() => setPressed(false)}
        onMouseLeave={() => setPressed(false)}
        style={{
          background: "#fff",
          color: "#0075DE",
          border: "none",
          borderRadius: 999,
          padding: base,
          fontSize: fs,
          fontWeight: 700,
          cursor: "pointer",
          fontFamily: "Inter, sans-serif",
          transform: pressed ? "scale(0.93)" : "scale(1)",
          transition: "transform 100ms ease-out, background 150ms ease-out",
        }}
        onMouseEnter={(e) => (e.currentTarget.style.background = "#e6f0ff")}
        onMouseLeave={(e) => { e.currentTarget.style.background = "#fff"; setPressed(false); }}
      >
        {children}
      </button>
    );
  }

  if (primary) {
    return (
      <button
        onClick={onClick}
        onMouseDown={() => setPressed(true)}
        onMouseUp={() => setPressed(false)}
        onMouseLeave={() => setPressed(false)}
        style={{
          background: "#0075DE",
          color: "#fff",
          border: "none",
          borderRadius: 999,
          padding: base,
          fontSize: fs,
          fontWeight: 600,
          cursor: "pointer",
          fontFamily: "Inter, sans-serif",
          transform: pressed ? "scale(0.93)" : "scale(1)",
          transition: "transform 100ms ease-out, background 150ms ease-out",
        }}
        onMouseEnter={(e) => (e.currentTarget.style.background = "#4A9EF5")}
        onMouseLeave={(e) => { e.currentTarget.style.background = "#0075DE"; setPressed(false); }}
      >
        {children}
      </button>
    );
  }

  return (
    <button
      onClick={onClick}
      onMouseDown={() => setPressed(true)}
      onMouseUp={() => setPressed(false)}
      onMouseLeave={() => setPressed(false)}
      style={{
        background: "#fff",
        color: "#31302E",
        border: "1px solid #E6E6E6",
        borderRadius: 999,
        padding: base,
        fontSize: fs,
        fontWeight: 600,
        cursor: "pointer",
        fontFamily: "Inter, sans-serif",
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        transform: pressed ? "scale(0.93)" : "scale(1)",
        transition: "transform 100ms ease-out, background 150ms ease-out",
      }}
      onMouseEnter={(e) => (e.currentTarget.style.background = "#EEF5FF")}
      onMouseLeave={(e) => { e.currentTarget.style.background = "#fff"; setPressed(false); }}
    >
      {children}
    </button>
  );
}

// ─── Nav ─────────────────────────────────────────────────────────────────────

function Nav() {
  const navigate = useNavigate();
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const fn = () => setScrolled(window.scrollY > 4);
    window.addEventListener("scroll", fn);
    return () => window.removeEventListener("scroll", fn);
  }, []);

  return (
    <nav
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        zIndex: 50,
        height: 64,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "0 40px",
        background: "#F6F5F4",
        borderBottom: scrolled ? "1px solid #E6E6E6" : "1px solid transparent",
        boxShadow: scrolled ? "0 1px 8px rgba(0,0,0,0.04)" : "none",
        transition: "border-color 150ms, box-shadow 150ms",
      }}
    >
      {/* Logo */}
      <div
        style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer" }}
        onClick={() => navigate("/")}
      >
        <div
          style={{
            width: 32,
            height: 32,
            borderRadius: 9,
            background: "#0075DE",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
          }}
        >
          <Package size={16} color="#fff" strokeWidth={2.5} />
        </div>
        <span style={{ fontWeight: 700, fontSize: 15, color: "#000", letterSpacing: "-0.2px" }}>
          SmartStock AI
        </span>
      </div>

      {/* Center links */}
      <div style={{ display: "flex", alignItems: "center", gap: 32 }}>
        {["Features", "How it works", "Pricing", "Blog"].map((l) => (
          <a
            key={l}
            href="#"
            style={{
              fontSize: 14,
              color: "#615D59",
              fontWeight: 500,
              textDecoration: "none",
              transition: "color 150ms",
            }}
            onMouseEnter={(e) => (e.currentTarget.style.color = "#000")}
            onMouseLeave={(e) => (e.currentTarget.style.color = "#615D59")}
          >
            {l}
          </a>
        ))}
      </div>

      {/* Right CTAs */}
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <PillBtn small onClick={() => navigate("/login")}>Log in</PillBtn>
        <PillBtn small primary onClick={() => navigate("/signup")}>Get started</PillBtn>
      </div>
    </nav>
  );
}

// ─── Dashboard mockup ─────────────────────────────────────────────────────────

function DashboardMockup() {
  return (
    <div
      style={{
        position: "relative",
        background: "#fff",
        border: "1px solid #E6E6E6",
        borderRadius: 18,
        boxShadow: "0 4px 32px rgba(0,0,0,0.07), 0 1px 4px rgba(0,0,0,0.04)",
        padding: 24,
        width: "100%",
        maxWidth: 680,
        margin: "0 auto",
      }}
    >
      {/* Floating badges */}
      <div style={{ position: "absolute", top: -14, right: 28, zIndex: 2 }}>
        <Badge variant="ai">✦ AI Generated</Badge>
      </div>
      <div style={{ position: "absolute", bottom: 72, left: -20, zIndex: 2 }}>
        <Badge variant="warning">⚠ Low stock · SKU-4821</Badge>
      </div>

      {/* Header row */}
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 16 }}>
        <div>
          <p style={{ fontSize: 11, color: "#615D59", marginBottom: 3, fontWeight: 500 }}>Demand forecast · next 90 days</p>
          <p style={{ fontSize: 17, fontWeight: 700, color: "#000", letterSpacing: "-0.2px" }}>Inventory outlook</p>
        </div>
        <Badge variant="ai">Prophet AI</Badge>
      </div>

      {/* Chart */}
      <div style={{ height: 176, marginBottom: 20 }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={forecastData} margin={{ top: 4, right: 4, left: -28, bottom: 0 }}>
            <defs>
              <linearGradient id="gActual" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#0075DE" stopOpacity={0.12} />
                <stop offset="100%" stopColor="#0075DE" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="gForecast" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#B39DDB" stopOpacity={0.18} />
                <stop offset="100%" stopColor="#B39DDB" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#F0EEEC" vertical={false} />
            <XAxis dataKey="month" tick={{ fontSize: 11, fill: "#615D59" }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 11, fill: "#615D59" }} axisLine={false} tickLine={false} />
            <Tooltip
              contentStyle={{
                border: "1px solid #E6E6E6",
                borderRadius: 8,
                fontSize: 12,
                boxShadow: "0 2px 8px rgba(0,0,0,0.06)",
                fontFamily: "Inter, sans-serif",
              }}
            />
            <Area
              type="monotone"
              dataKey="actual"
              stroke="#0075DE"
              strokeWidth={2}
              fill="url(#gActual)"
              dot={false}
              name="Actual"
              connectNulls={false}
            />
            <Area
              type="monotone"
              dataKey="forecast"
              stroke="#B39DDB"
              strokeWidth={2}
              strokeDasharray="5 3"
              fill="url(#gForecast)"
              dot={false}
              name="Forecast"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Stat row */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 10 }}>
        {[
          { label: "Total SKUs",    value: "4,821",  delta: "+12",   up: true,  Icon: Package },
          { label: "In stock",      value: "94.3%",  delta: "+2.1%", up: true,  Icon: CheckCircle },
          { label: "Pending POs",   value: "17",     delta: "−3",    up: false, Icon: FileText },
          { label: "Stockout risk", value: "8 SKUs", delta: "−5",    up: true,  Icon: AlertTriangle },
        ].map(({ label, value, delta, up, Icon }) => (
          <div
            key={label}
            style={{
              background: "#F6F5F4",
              border: "1px solid #EDECEA",
              borderRadius: 10,
              padding: "12px 12px 10px",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
              <Icon size={13} color="#615D59" strokeWidth={1.8} />
              <span style={{ fontSize: 10, fontWeight: 700, color: up ? "#1AAE39" : "#E53935" }}>{delta}</span>
            </div>
            <p style={{ fontSize: 15, fontWeight: 700, color: "#000", lineHeight: 1, marginBottom: 3 }}>{value}</p>
            <p style={{ fontSize: 10, color: "#615D59" }}>{label}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Hero ─────────────────────────────────────────────────────────────────────

function Hero() {
  const navigate = useNavigate();
  return (
    <section
      style={{
        paddingTop: 112,
        paddingBottom: 80,
        paddingLeft: 40,
        paddingRight: 40,
        textAlign: "center",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
      }}
    >
      <Badge variant="ai">✦ AI-Powered Inventory Platform</Badge>

      <h1
        style={{
          fontSize: "clamp(34px, 4.8vw, 52px)",
          fontWeight: 700,
          color: "#000",
          letterSpacing: "-0.5px",
          lineHeight: 1.1,
          marginTop: 20,
          marginBottom: 0,
          maxWidth: 700,
        }}
      >
        Proactive demand planning —<br />
        know what you need before you run out.
      </h1>

      <p
        style={{
          fontSize: 16,
          color: "#615D59",
          lineHeight: 1.75,
          maxWidth: 520,
          marginTop: 20,
          marginBottom: 0,
        }}
      >
        SmartStock AI combines real-time inventory tracking with AI demand forecasting — so your warehouse never runs dry.
      </p>

      <div style={{ display: "flex", gap: 12, marginTop: 32, flexWrap: "wrap", justifyContent: "center" }}>
        <PillBtn primary onClick={() => navigate("/signup")}>Start for free</PillBtn>
        <PillBtn onClick={() => {}}>
          See how it works <ChevronRight size={14} strokeWidth={2} />
        </PillBtn>
      </div>

      <div style={{ marginTop: 56, width: "100%", maxWidth: 720 }}>
        <DashboardMockup />
      </div>
    </section>
  );
}

// ─── Problem ──────────────────────────────────────────────────────────────────

function Problem() {
  return (
    <section style={{ padding: "72px 40px" }}>
      <div style={{ maxWidth: 880, margin: "0 auto" }}>
        <p style={{ fontSize: 11, fontWeight: 700, color: "#615D59", letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 14 }}>
          The cost of reactive inventory
        </p>
        <h2 style={{ fontSize: 32, fontWeight: 700, color: "#000", letterSpacing: "-0.3px", marginBottom: 40 }}>
          Inventory mistakes are expensive.
        </h2>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
          {/* Overstock */}
          <div
            style={{
              background: "#FFF8F0",
              border: "1px solid #FFD9A8",
              borderRadius: 16,
              padding: 32,
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 20 }}>
              <div style={{ width: 36, height: 36, borderRadius: 10, background: "#FFF3E0", display: "flex", alignItems: "center", justifyContent: "center" }}>
                <TrendingUp size={18} color="#DD5B00" />
              </div>
              <Badge variant="warning">Overstock</Badge>
            </div>
            <p style={{ fontSize: 52, fontWeight: 700, color: "#DD5B00", letterSpacing: "-2px", lineHeight: 1, marginBottom: 12 }}>
              15–25%
            </p>
            <p style={{ fontSize: 15, color: "#31302E", lineHeight: 1.65 }}>
              of annual revenue tied up in overstocked goods sitting idle in your warehouse — eroding margins.
            </p>
          </div>

          {/* Stockouts */}
          <div
            style={{
              background: "#FFF5F5",
              border: "1px solid #FFBDBD",
              borderRadius: 16,
              padding: 32,
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 20 }}>
              <div style={{ width: 36, height: 36, borderRadius: 10, background: "#FFEBEE", display: "flex", alignItems: "center", justifyContent: "center" }}>
                <TrendingDown size={18} color="#E53935" />
              </div>
              <Badge variant="danger">Stockouts</Badge>
            </div>
            <p style={{ fontSize: 52, fontWeight: 700, color: "#E53935", letterSpacing: "-2px", lineHeight: 1, marginBottom: 12 }}>
              4–8%
            </p>
            <p style={{ fontSize: 15, color: "#31302E", lineHeight: 1.65 }}>
              of annual revenue lost from stockouts — missed sales, cancelled orders, and damaged supplier trust.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}

// ─── How it works ─────────────────────────────────────────────────────────────

function HowItWorks() {
  const steps = [
    {
      num: "01",
      title: "Track",
      body: "Real-time visibility across every SKU, supplier relationship, and warehouse location. One living source of truth for your entire operation.",
      Icon: Package,
      ai: false,
    },
    {
      num: "02",
      title: "Forecast",
      body: "Prophet AI analyzes historical demand, seasonal patterns, and supplier lead times — flagging future stockouts weeks before they happen.",
      Icon: Brain,
      ai: true,
    },
    {
      num: "03",
      title: "Act",
      body: "Purchase orders are drafted automatically and queued for human review. One click to approve and dispatch — or edit first.",
      Icon: CheckCircle,
      ai: false,
    },
  ];

  return (
    <section
      style={{
        padding: "72px 40px",
        background: "#fff",
        borderTop: "1px solid #E6E6E6",
        borderBottom: "1px solid #E6E6E6",
      }}
    >
      <div style={{ maxWidth: 880, margin: "0 auto" }}>
        <p style={{ fontSize: 11, fontWeight: 700, color: "#615D59", letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 14 }}>
          How it works
        </p>
        <h2 style={{ fontSize: 32, fontWeight: 700, color: "#000", letterSpacing: "-0.3px", marginBottom: 48 }}>
          From raw data to approved purchase orders.
        </h2>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 40 }}>
          {steps.map(({ num, title, body, Icon, ai }, i) => (
            <div key={num} style={{ position: "relative" }}>
              {i < steps.length - 1 && (
                <div
                  style={{
                    position: "absolute",
                    top: 18,
                    right: -24,
                    color: "#E6E6E6",
                  }}
                >
                  <ArrowRight size={16} />
                </div>
              )}
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 16 }}>
                <span style={{ fontSize: 11, fontWeight: 700, color: "#615D59", letterSpacing: "0.05em" }}>{num}</span>
                <div
                  style={{
                    width: 38,
                    height: 38,
                    borderRadius: 10,
                    background: ai ? "#F3E5F5" : "#EEF5FF",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                >
                  <Icon size={18} color={ai ? "#391C57" : "#0075DE"} strokeWidth={1.8} />
                </div>
                {ai && <Badge variant="ai">AI</Badge>}
              </div>
              <h3 style={{ fontSize: 18, fontWeight: 700, color: "#000", marginBottom: 10 }}>{title}</h3>
              <p style={{ fontSize: 14, color: "#615D59", lineHeight: 1.7 }}>{body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─── Features ─────────────────────────────────────────────────────────────────

function Features() {
  const cards = [
    {
      Icon: BarChart3,
      title: "Demand forecasting",
      body: "Prophet-powered models predict demand weeks ahead, factoring in seasonality, promotions, and lead times.",
      badge: "AI-Powered",
    },
    {
      Icon: MessageSquare,
      title: "Ask in plain English",
      body: "Natural language queries over your inventory. \"Which SKUs will run out before Friday?\" — answered instantly.",
      badge: "AI-Powered",
    },
    {
      Icon: FileText,
      title: "Invoice OCR scanning",
      body: "Upload or photograph supplier invoices. SmartStock extracts items, quantities, and prices in seconds.",
      badge: null,
    },
    {
      Icon: Zap,
      title: "Autonomous PO drafting",
      body: "Purchase orders are drafted from forecast data. Review, edit if needed, and approve — all in one screen.",
      badge: "AI-Powered",
    },
    {
      Icon: ShieldCheck,
      title: "Role-based access",
      body: "Granular RBAC keeps warehouse staff, buyers, and finance teams in their lanes with a full audit trail.",
      badge: null,
    },
    {
      Icon: Mic,
      title: "Voice commands",
      body: "Powered by OpenAI Whisper. Warehouse staff can query and update inventory hands-free on the floor.",
      badge: "AI-Powered",
    },
  ];

  return (
    <section style={{ padding: "72px 40px" }}>
      <div style={{ maxWidth: 880, margin: "0 auto" }}>
        <p style={{ fontSize: 11, fontWeight: 700, color: "#615D59", letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 14 }}>
          Features
        </p>
        <h2 style={{ fontSize: 32, fontWeight: 700, color: "#000", letterSpacing: "-0.3px", marginBottom: 40 }}>
          Everything your warehouse team needs.
        </h2>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 16 }}>
          {cards.map(({ Icon, title, body, badge }) => (
            <div
              key={title}
              style={{
                background: "#fff",
                border: "1px solid #E6E6E6",
                borderRadius: 14,
                padding: 24,
                boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
                transition: "box-shadow 150ms, transform 150ms",
                cursor: "default",
              }}
              onMouseEnter={(e) => {
                (e.currentTarget as HTMLDivElement).style.boxShadow = "0 4px 16px rgba(0,0,0,0.07)";
                (e.currentTarget as HTMLDivElement).style.transform = "translateY(-2px)";
              }}
              onMouseLeave={(e) => {
                (e.currentTarget as HTMLDivElement).style.boxShadow = "0 1px 3px rgba(0,0,0,0.04)";
                (e.currentTarget as HTMLDivElement).style.transform = "translateY(0)";
              }}
            >
              <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 16 }}>
                <div
                  style={{
                    width: 40,
                    height: 40,
                    borderRadius: 10,
                    background: badge ? "#F3E5F5" : "#EEF5FF",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    flexShrink: 0,
                  }}
                >
                  <Icon size={18} color={badge ? "#391C57" : "#0075DE"} strokeWidth={1.8} />
                </div>
                {badge && <Badge variant="ai">{badge}</Badge>}
              </div>
              <h3 style={{ fontSize: 16, fontWeight: 700, color: "#000", marginBottom: 8 }}>{title}</h3>
              <p style={{ fontSize: 13, color: "#615D59", lineHeight: 1.68 }}>{body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ─── KPI strip ────────────────────────────────────────────────────────────────

function KpiStrip() {
  const kpis = [
    { stat: "−30%",  label: "reduction in stockouts",  sub: "Average across customers in year one" },
    { stat: "≥60%",  label: "POs auto-approved",       sub: "Human review always available on the rest" },
    { stat: "−15%",  label: "carrying costs",          sub: "Less capital tied up in surplus stock" },
  ];

  return (
    <section
      style={{
        padding: "72px 40px",
        background: "#fff",
        borderTop: "1px solid #E6E6E6",
        borderBottom: "1px solid #E6E6E6",
      }}
    >
      <div
        style={{
          maxWidth: 880,
          margin: "0 auto",
          display: "grid",
          gridTemplateColumns: "repeat(3,1fr)",
          gap: 32,
        }}
      >
        {kpis.map(({ stat, label, sub }) => (
          <div key={stat}>
            <p
              style={{
                fontSize: 52,
                fontWeight: 700,
                color: "#0075DE",
                letterSpacing: "-2px",
                lineHeight: 1,
                marginBottom: 10,
              }}
            >
              {stat}
            </p>
            <p style={{ fontSize: 17, fontWeight: 700, color: "#000", marginBottom: 6 }}>{label}</p>
            <p style={{ fontSize: 13, color: "#615D59" }}>{sub}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

// ─── CTA banner ───────────────────────────────────────────────────────────────

function CtaBanner() {
  const navigate = useNavigate();
  return (
    <section style={{ padding: "64px 40px" }}>
      <div
        style={{
          maxWidth: 880,
          margin: "0 auto",
          background: "#0075DE",
          borderRadius: 20,
          padding: "56px 48px",
          textAlign: "center",
        }}
      >
        <h2
          style={{
            fontSize: 32,
            fontWeight: 700,
            color: "#fff",
            letterSpacing: "-0.3px",
            marginBottom: 12,
          }}
        >
          Ready to make your inventory proactive?
        </h2>
        <p style={{ fontSize: 15, color: "rgba(255,255,255,0.78)", marginBottom: 32 }}>
          Join hundreds of warehouse teams that stopped reacting and started planning.
        </p>
        <div style={{ display: "flex", gap: 12, justifyContent: "center", flexWrap: "wrap" }}>
          <PillBtn white onClick={() => navigate("/signup")}>Get started free</PillBtn>
          <button
            style={{
              background: "transparent",
              color: "#fff",
              border: "1px solid rgba(255,255,255,0.38)",
              borderRadius: 999,
              padding: "11px 24px",
              fontSize: 15,
              fontWeight: 600,
              cursor: "pointer",
              fontFamily: "Inter, sans-serif",
              transition: "background 150ms",
            }}
            onMouseEnter={(e) => ((e.currentTarget as HTMLButtonElement).style.background = "rgba(255,255,255,0.1)")}
            onMouseLeave={(e) => ((e.currentTarget as HTMLButtonElement).style.background = "transparent")}
          >
            Book a demo
          </button>
        </div>
      </div>
    </section>
  );
}

// ─── Footer ───────────────────────────────────────────────────────────────────

function Footer() {
  const cols = [
    { heading: "Product",  links: ["Features", "Integrations", "Changelog", "Pricing", "Roadmap"] },
    { heading: "Company",  links: ["About us", "Blog", "Careers", "Press", "Contact"] },
    { heading: "Legal",    links: ["Privacy policy", "Terms of service", "Cookie policy", "DPA"] },
  ];

  return (
    <footer style={{ borderTop: "1px solid #E6E6E6", padding: "56px 40px 40px", background: "#F6F5F4" }}>
      <div style={{ maxWidth: 880, margin: "0 auto" }}>
        <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr 1fr 1fr", gap: 40, marginBottom: 48 }}>
          {/* Brand */}
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 14 }}>
              <div style={{ width: 28, height: 28, borderRadius: 8, background: "#0075DE", display: "flex", alignItems: "center", justifyContent: "center" }}>
                <Package size={13} color="#fff" strokeWidth={2.5} />
              </div>
              <span style={{ fontWeight: 700, fontSize: 14, color: "#000" }}>SmartStock AI</span>
            </div>
            <p style={{ fontSize: 13, color: "#615D59", lineHeight: 1.7, maxWidth: 220 }}>
              Proactive demand planning — know what you need before you run out.
            </p>
          </div>

          {cols.map(({ heading, links }) => (
            <div key={heading}>
              <p style={{ fontSize: 11, fontWeight: 700, color: "#000", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 16 }}>
                {heading}
              </p>
              <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: 11 }}>
                {links.map((l) => (
                  <li key={l}>
                    <a
                      href="#"
                      style={{ fontSize: 13, color: "#615D59", textDecoration: "none", transition: "color 150ms" }}
                      onMouseEnter={(e) => (e.currentTarget.style.color = "#000")}
                      onMouseLeave={(e) => (e.currentTarget.style.color = "#615D59")}
                    >
                      {l}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div style={{ borderTop: "1px solid #E6E6E6", paddingTop: 24 }}>
          <p style={{ fontSize: 12, color: "#615D59" }}>© 2026 SmartStock AI, Inc. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function Landing() {
  return (
    <div style={{ fontFamily: "Inter, sans-serif", background: "#F6F5F4", minHeight: "100vh" }}>
      <Nav />
      <main>
        <Hero />
        <Problem />
        <HowItWorks />
        <Features />
        <KpiStrip />
        <CtaBanner />
      </main>
      <Footer />
    </div>
  );
}
