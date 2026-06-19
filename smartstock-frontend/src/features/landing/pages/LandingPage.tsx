import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
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
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { useAuthStore } from '../../../store/authStore';
import { getAvatarColor } from '../../../shared/utils/avatar';
import ThemeToggle from '../../../shared/components/ThemeToggle';

function getInitials(name: string): string {
  return name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
}

const forecastData = [
  { month: 'Jan', actual: 420, forecast: 440 },
  { month: 'Feb', actual: 380, forecast: 395 },
  { month: 'Mar', actual: 510, forecast: 490 },
  { month: 'Apr', actual: 470, forecast: 480 },
  { month: 'May', actual: 540, forecast: 555 },
  { month: 'Jun', forecast: 620 },
  { month: 'Jul', forecast: 670 },
];

type BadgeVariant = 'ai' | 'warning' | 'success' | 'danger';

function Badge({ children, variant = 'ai', small }: { children: React.ReactNode; variant?: BadgeVariant; small?: boolean }) {
  const classes: Record<BadgeVariant, string> = {
    ai: 'bg-purple-50 text-purple-800 dark:bg-purple-900/40 dark:text-purple-300',
    warning: 'bg-orange-50 text-orange-800 dark:bg-orange-900/40 dark:text-orange-300',
    success: 'bg-green-50 text-green-700 dark:bg-green-900/40 dark:text-green-300',
    danger: 'bg-red-50 text-red-700 dark:bg-red-900/40 dark:text-red-300',
  };
  return (
    <span className={`inline-flex items-center gap-1 whitespace-nowrap rounded-full px-2.5 py-0.5 font-semibold ${small ? 'text-[10px]' : 'text-eyebrow'} ${classes[variant]}`}>
      {children}
    </span>
  );
}

function Nav() {
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const fn = () => setScrolled(window.scrollY > 4);
    window.addEventListener('scroll', fn);
    return () => window.removeEventListener('scroll', fn);
  }, []);

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 h-16 flex items-center justify-between px-6 md:px-10 transition-all duration-150 bg-canvas ${
        scrolled ? 'border-b border-hairline shadow-sm' : 'border-b border-transparent'
      }`}
    >
      <Link to="/" className="flex items-center gap-2 cursor-pointer">
        <img src="/smart-32.png" alt="SmartStock AI" className="w-8 h-8 shrink-0" />
        <span className="text-card-title font-bold text-ink tracking-tight">SmartStock AI</span>
      </Link>

      <div className="hidden md:flex items-center gap-8">
        {['Features', 'How it works', 'Pricing', 'Blog'].map((l) => (
          <a
            key={l}
            href="#"
            className="text-body font-medium text-ink-muted hover:text-ink transition-colors"
          >
            {l}
          </a>
        ))}
      </div>

      <div className="flex items-center gap-2.5">
        <ThemeToggle />
        {user ? (
          <div className="flex items-center gap-2">
            <Link
              to="/dashboard"
              className="text-caption font-medium text-ink-muted hover:text-ink transition-colors"
            >
              Dashboard
            </Link>
            <div className="flex items-center gap-1.5 rounded-md px-1.5 py-0.5 hover:bg-canvas-soft transition-colors">
              <div
                className={`w-6 h-6 rounded-full ${getAvatarColor(user.name)} flex items-center justify-center text-white text-[10px] font-medium`}
              >
                {getInitials(user.name)}
              </div>
              <span className="hidden sm:inline text-caption font-medium text-ink-muted">
                {user.name}
              </span>
            </div>
          </div>
        ) : (
          <>
            <button
              onClick={() => navigate('/login')}
              className="text-caption font-semibold text-ink-secondary hover:text-ink border border-hairline rounded-full px-4 py-1.5 hover:bg-canvas-soft transition-colors"
            >
              Log in
            </button>
            <button
              onClick={() => navigate('/register')}
              className="text-caption font-semibold text-white bg-brand-600 hover:bg-brand-500 rounded-full px-4 py-1.5 transition-colors"
            >
              Get started
            </button>
          </>
        )}
      </div>
    </nav>
  );
}

function DashboardMockup() {
  return (
    <div className="relative bg-canvas border border-hairline rounded-2xl shadow-elevated p-6 w-full max-w-[680px] mx-auto">
      <div className="absolute -top-3.5 right-7 z-2">
        <Badge variant="ai">✦ AI Generated</Badge>
      </div>
      <div className="absolute bottom-[72px] left-8 z-2">
        <Badge variant="warning" small>⚠ Low stock</Badge>
      </div>

      <div className="flex items-start justify-between mb-4">
        <div>
          <p className="text-caption text-ink-muted font-medium mb-0.5">Demand forecast · next 90 days</p>
          <p className="text-section-heading font-bold text-ink tracking-tight">Inventory outlook</p>
        </div>
        <Badge variant="ai">Prophet AI</Badge>
      </div>

      <div className="h-[176px] mb-5">
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
            <XAxis dataKey="month" tick={{ fontSize: 11, fill: '#615D59' }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 11, fill: '#615D59' }} axisLine={false} tickLine={false} />
            <Tooltip
              contentStyle={{
                border: '1px solid #E6E6E6',
                borderRadius: 8,
                fontSize: 12,
                boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
              }}
            />
            <Area type="monotone" dataKey="actual" stroke="#0075DE" strokeWidth={2} fill="url(#gActual)" dot={false} name="Actual" connectNulls={false} />
            <Area type="monotone" dataKey="forecast" stroke="#B39DDB" strokeWidth={2} strokeDasharray="5 3" fill="url(#gForecast)" dot={false} name="Forecast" />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
        {[
          { label: 'Total SKUs', value: '4,821', delta: '+12', up: true, Icon: Package },
          { label: 'In stock', value: '94.3%', delta: '+2.1%', up: true, Icon: CheckCircle },
          { label: 'Pending POs', value: '17', delta: '−3', up: false, Icon: FileText },
          { label: 'Stockout risk', value: '8 SKUs', delta: '−5', up: true, Icon: AlertTriangle },
        ].map(({ label, value, delta, up, Icon }) => (
          <div key={label} className="bg-canvas-soft border border-hairline rounded-[10px] p-3">
            <div className="flex items-center justify-between mb-2">
              <Icon size={13} className="text-ink-muted" strokeWidth={1.8} />
              <span className={`text-[10px] font-bold ${up ? 'text-green-600' : 'text-red-600'}`}>{delta}</span>
            </div>
            <p className="text-card-title font-bold text-ink leading-none mb-1">{value}</p>
            <p className="text-[10px] text-ink-muted">{label}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function Hero() {
  const navigate = useNavigate();
  return (
    <section className="pt-28 pb-20 px-6 md:px-10 text-center flex flex-col items-center">
      <Badge variant="ai">✦ AI-Powered Inventory Platform</Badge>

      <h1 className="text-[clamp(34px,4.8vw,52px)] font-bold text-ink tracking-tight leading-[1.1] mt-5 max-w-[700px]">
        Proactive demand planning —<br />
        know what you need before you run out.
      </h1>

      <p className="text-body text-ink-muted leading-relaxed max-w-[520px] mt-5">
        SmartStock AI combines real-time inventory tracking with AI demand forecasting — so your warehouse never runs dry.
      </p>

      <div className="flex gap-3 mt-8 flex-wrap justify-center">
        <button
          onClick={() => navigate('/register')}
          className="font-semibold text-white bg-brand-600 hover:bg-brand-500 rounded-full px-6 py-2.5 text-body transition-colors"
        >
          Start for free
        </button>
        <button className="font-semibold text-ink-secondary border border-hairline hover:bg-canvas-soft rounded-full px-6 py-2.5 text-body inline-flex items-center gap-1.5 transition-colors">
          See how it works <ChevronRight size={14} strokeWidth={2} />
        </button>
      </div>

      <div className="mt-14 w-full max-w-[720px]">
        <DashboardMockup />
      </div>
    </section>
  );
}

function Problem() {
  return (
    <section className="py-16 px-6 md:px-10">
      <div className="max-w-[880px] mx-auto">
        <p className="text-eyebrow font-bold text-ink-muted tracking-widest uppercase mb-3.5">
          The cost of reactive inventory
        </p>
        <h2 className="text-3xl font-bold text-ink tracking-tight mb-10">
          Inventory mistakes are expensive.
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div className="bg-[#FFF8F0] dark:bg-[#3D2E1A] border border-[#FFD9A8] dark:border-[#5C4520] rounded-2xl p-8">
            <div className="flex items-center gap-2 mb-5">
              <div className="w-9 h-9 rounded-[10px] bg-[#FFF3E0] dark:bg-[#4A3318] flex items-center justify-center">
                <TrendingUp size={18} className="text-[#DD5B00]" />
              </div>
              <Badge variant="warning">Overstock</Badge>
            </div>
            <p className="text-5xl font-bold text-[#DD5B00] tracking-tight leading-none mb-3">15–25%</p>
            <p className="text-body text-ink-secondary leading-relaxed">
              of annual revenue tied up in overstocked goods sitting idle in your warehouse — eroding margins.
            </p>
          </div>

          <div className="bg-[#FFF5F5] dark:bg-[#3D1A1A] border border-[#FFBDBD] dark:border-[#5C2020] rounded-2xl p-8">
            <div className="flex items-center gap-2 mb-5">
              <div className="w-9 h-9 rounded-[10px] bg-red-50 dark:bg-[#4A1818] flex items-center justify-center">
                <TrendingDown size={18} className="text-[#E53935]" />
              </div>
              <Badge variant="danger">Stockouts</Badge>
            </div>
            <p className="text-5xl font-bold text-[#E53935] tracking-tight leading-none mb-3">4–8%</p>
            <p className="text-body text-ink-secondary leading-relaxed">
              of annual revenue lost from stockouts — missed sales, cancelled orders, and damaged supplier trust.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}

function HowItWorks() {
  const steps = [
    { num: '01', title: 'Track', body: 'Real-time visibility across every SKU, supplier relationship, and warehouse location. One living source of truth for your entire operation.', Icon: Package, ai: false },
    { num: '02', title: 'Forecast', body: 'Prophet AI analyzes historical demand, seasonal patterns, and supplier lead times — flagging future stockouts weeks before they happen.', Icon: Brain, ai: true },
    { num: '03', title: 'Act', body: 'Purchase orders are drafted automatically and queued for human review. One click to approve and dispatch — or edit first.', Icon: CheckCircle, ai: false },
  ];

  return (
    <section className="py-16 px-6 md:px-10 bg-canvas border-y border-hairline">
      <div className="max-w-[880px] mx-auto">
        <p className="text-eyebrow font-bold text-ink-muted tracking-widest uppercase mb-3.5">
          How it works
        </p>
        <h2 className="text-3xl font-bold text-ink tracking-tight mb-12">
          From raw data to approved purchase orders.
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
          {steps.map(({ num, title, body, Icon, ai }, i) => (
            <div key={num} className="relative">
              {i < steps.length - 1 && (
                <div className="hidden md:block absolute top-[18px] -right-6 text-hairline">
                  <ArrowRight size={16} />
                </div>
              )}
              <div className="flex items-center gap-2.5 mb-4">
                <span className="text-eyebrow font-bold text-ink-muted tracking-wider">{num}</span>
                <div className={`w-[38px] h-[38px] rounded-[10px] flex items-center justify-center ${ai ? 'bg-purple-50 dark:bg-purple-900/40' : 'bg-brand-50 dark:bg-brand-950/60'}`}>
                  <Icon size={18} className={ai ? 'text-purple-800 dark:text-purple-300' : 'text-brand-600'} strokeWidth={1.8} />
                </div>
                {ai && <Badge variant="ai">AI</Badge>}
              </div>
              <h3 className="text-section-heading font-bold text-ink mb-2.5">{title}</h3>
              <p className="text-body text-ink-muted leading-relaxed">{body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Features() {
  const cards = [
    { Icon: BarChart3, title: 'Demand forecasting', body: 'Prophet-powered models predict demand weeks ahead, factoring in seasonality, promotions, and lead times.', variant: 'ai' as BadgeVariant, label: 'AI-Powered' },
    { Icon: MessageSquare, title: 'Ask in plain English', body: 'Natural language queries over your inventory. "Which SKUs will run out before Friday?" — answered instantly.', variant: 'ai' as BadgeVariant, label: 'AI-Powered' },
    { Icon: FileText, title: 'Invoice OCR scanning', body: 'Upload or photograph supplier invoices. SmartStock extracts items, quantities, and prices in seconds.', variant: null, label: null },
    { Icon: Zap, title: 'Autonomous PO drafting', body: 'Purchase orders are drafted from forecast data. Review, edit if needed, and approve — all in one screen.', variant: 'ai' as BadgeVariant, label: 'AI-Powered' },
    { Icon: ShieldCheck, title: 'Role-based access', body: 'Granular RBAC keeps warehouse staff, buyers, and finance teams in their lanes with a full audit trail.', variant: null, label: null },
    { Icon: Mic, title: 'Voice commands', body: 'Powered by OpenAI Whisper. Warehouse staff can query and update inventory hands-free on the floor.', variant: 'ai' as BadgeVariant, label: 'AI-Powered' },
  ];

  return (
    <section className="py-16 px-6 md:px-10">
      <div className="max-w-[880px] mx-auto">
        <p className="text-eyebrow font-bold text-ink-muted tracking-widest uppercase mb-3.5">
          Features
        </p>
        <h2 className="text-3xl font-bold text-ink tracking-tight mb-10">
          Everything your warehouse team needs.
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {cards.map(({ Icon, title, body, variant, label }) => (
            <div
              key={title}
              className="group bg-canvas border border-hairline rounded-[14px] p-6 shadow-soft hover:shadow-elevated hover:-translate-y-0.5 transition-all cursor-default"
            >
              <div className="flex items-start justify-between mb-4">
                <div className={`w-10 h-10 rounded-[10px] flex items-center justify-center shrink-0 ${variant ? 'bg-purple-50 dark:bg-purple-900/40' : 'bg-brand-50 dark:bg-brand-950/60'}`}>
                  <Icon size={18} className={variant ? 'text-purple-800 dark:text-purple-300' : 'text-brand-600'} strokeWidth={1.8} />
                </div>
                {variant && <Badge variant={variant}>{label}</Badge>}
              </div>
              <h3 className="text-card-title font-bold text-ink mb-2">{title}</h3>
              <p className="text-[13px] text-ink-muted leading-relaxed">{body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function KpiStrip() {
  const kpis = [
    { stat: '−30%', label: 'reduction in stockouts', sub: 'Average across customers in year one' },
    { stat: '≥60%', label: 'POs auto-approved', sub: 'Human review always available on the rest' },
    { stat: '−15%', label: 'carrying costs', sub: 'Less capital tied up in surplus stock' },
  ];

  return (
    <section className="py-16 px-6 md:px-10 bg-canvas border-y border-hairline">
      <div className="max-w-[880px] mx-auto grid grid-cols-1 md:grid-cols-3 gap-8">
        {kpis.map(({ stat, label, sub }) => (
          <div key={stat}>
            <p className="text-5xl font-bold text-brand-600 tracking-tight leading-none mb-2.5">{stat}</p>
            <p className="text-section-heading font-bold text-ink mb-1.5">{label}</p>
            <p className="text-[13px] text-ink-muted">{sub}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function CtaBanner() {
  const navigate = useNavigate();
  return (
    <section className="py-16 px-6 md:px-10">
      <div className="max-w-[880px] mx-auto bg-brand-600 rounded-[20px] px-12 py-14 text-center">
        <h2 className="text-3xl font-bold text-white tracking-tight mb-3">
          Ready to make your inventory proactive?
        </h2>
        <p className="text-body text-white/78 mb-8">
          Join hundreds of warehouse teams that stopped reacting and started planning.
        </p>
        <div className="flex gap-3 justify-center flex-wrap">
          <button
            onClick={() => navigate('/register')}
            className="font-bold text-brand-600 bg-white hover:bg-brand-50 rounded-full px-6 py-2.5 text-body transition-colors"
          >
            Get started free
          </button>
          <button className="font-semibold text-white border border-white/38 rounded-full px-6 py-2.5 text-body hover:bg-white/10 transition-colors">
            Book a demo
          </button>
        </div>
      </div>
    </section>
  );
}

function Footer() {
  const cols = [
    { heading: 'Product', links: ['Features', 'Integrations', 'Changelog', 'Pricing', 'Roadmap'] },
    { heading: 'Company', links: ['About us', 'Blog', 'Careers', 'Press', 'Contact'] },
    { heading: 'Legal', links: ['Privacy policy', 'Terms of service', 'Cookie policy', 'DPA'] },
  ];

  return (
    <footer className="border-t border-hairline bg-canvas-soft py-14 px-6 md:px-10">
      <div className="max-w-[880px] mx-auto">
        <div className="grid grid-cols-2 md:grid-cols-[2fr_1fr_1fr_1fr] gap-10 mb-12">
          <div>
            <div className="flex items-center gap-2 mb-3.5">
              <img src="/smart-24.png" alt="SmartStock AI" className="w-7 h-7 shrink-0" />
              <span className="text-card-title font-bold text-ink">SmartStock AI</span>
            </div>
            <p className="text-[13px] text-ink-muted leading-relaxed max-w-[220px]">
              Proactive demand planning — know what you need before you run out.
            </p>
          </div>

          {cols.map(({ heading, links }) => (
            <div key={heading}>
              <p className="text-eyebrow font-bold text-ink tracking-widest uppercase mb-4">
                {heading}
              </p>
              <ul className="space-y-2.5">
                {links.map((l) => (
                  <li key={l}>
                    <a href="#" className="text-[13px] text-ink-muted hover:text-ink transition-colors no-underline">
                      {l}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="border-t border-hairline pt-6">
          <p className="text-caption text-ink-muted">© {new Date().getFullYear()} SmartStock AI, Inc. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
}

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-canvas-soft text-ink-secondary">
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
