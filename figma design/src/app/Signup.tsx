import { useState } from "react";
import { useNavigate } from "react-router";
import { Eye, EyeOff, Package, AlertCircle, Check } from "lucide-react";

function GoogleIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
      <path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844a4.14 4.14 0 0 1-1.796 2.717v2.258h2.908C16.658 14.251 17.64 11.943 17.64 9.2z" fill="#4285F4" />
      <path d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A9 9 0 0 0 9 18z" fill="#34A853" />
      <path d="M3.964 10.71A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.71V4.958H.957A9 9 0 0 0 0 9c0 1.452.348 2.827.957 4.042l3.007-2.332z" fill="#FBBC05" />
      <path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58A9 9 0 0 0 9 0C5.482 0 2.438 2.017.957 4.958L3.964 6.29C4.672 4.163 6.656 3.58 9 3.58z" fill="#EA4335" />
    </svg>
  );
}

// ─── Password strength ───────────────────────────────────────────────────────

function strengthScore(pw: string): number {
  let s = 0;
  if (pw.length >= 8)          s++;
  if (/[A-Z]/.test(pw))        s++;
  if (/[0-9]/.test(pw))        s++;
  if (/[^A-Za-z0-9]/.test(pw)) s++;
  return s;
}

function StrengthBar({ password }: { password: string }) {
  if (!password) return null;
  const score = strengthScore(password);
  const colors = ["", "#E53935", "#DD5B00", "#1AAE39", "#0075DE"];
  const labels = ["", "Weak", "Fair", "Good", "Strong"];
  return (
    <div style={{ marginTop: 8 }}>
      <div style={{ display: "flex", gap: 4 }}>
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            style={{
              flex: 1,
              height: 3,
              borderRadius: 99,
              background: i <= score ? colors[score] : "#EDECEA",
              transition: "background 200ms ease-out",
            }}
          />
        ))}
      </div>
      {score > 0 && (
        <p style={{ fontSize: 11, color: colors[score], marginTop: 5, fontWeight: 600, fontFamily: "Inter, sans-serif" }}>
          {labels[score]}
        </p>
      )}
    </div>
  );
}

// ─── Field wrapper ───────────────────────────────────────────────────────────

function Field({ label, error, children }: { label: string; error?: string; children: React.ReactNode }) {
  return (
    <div>
      {label && (
        <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: "#31302E", marginBottom: 6, fontFamily: "Inter, sans-serif" }}>
          {label}
        </label>
      )}
      {children}
      {error && (
        <p style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 12, color: "#E53935", marginTop: 6, fontFamily: "Inter, sans-serif" }}>
          <AlertCircle size={12} /> {error}
        </p>
      )}
    </div>
  );
}

// ─── Constants ───────────────────────────────────────────────────────────────

const ROLES = [
  "Warehouse manager",
  "Procurement lead",
  "Supply chain analyst",
  "Finance / accounting",
  "Operations director",
  "Other",
];

const inputBase: React.CSSProperties = {
  width: "100%",
  border: "1px solid #E6E6E6",
  borderRadius: 10,
  padding: "10px 14px",
  fontSize: 15,
  color: "#31302E",
  background: "#fff",
  outline: "none",
  boxSizing: "border-box",
  fontFamily: "Inter, sans-serif",
  transition: "border-color 150ms ease-out, box-shadow 150ms ease-out",
};

// ─── Component ───────────────────────────────────────────────────────────────

export default function Signup() {
  const navigate = useNavigate();

  const [form, setForm] = useState({
    name: "", email: "", password: "", confirm: "", role: "", terms: false,
  });
  const [showPw, setShowPw]         = useState(false);
  const [showCf, setShowCf]         = useState(false);
  const [errors, setErrors]         = useState<Record<string, string>>({});
  const [touched, setTouched]       = useState(false);

  function set(field: string, value: string | boolean) {
    setForm((f) => ({ ...f, [field]: value }));
    if (touched) setErrors((e) => { const n = { ...e }; delete n[field]; return n; });
  }

  function validate() {
    const e: Record<string, string> = {};
    if (!form.name.trim())                                        e.name    = "Full name is required.";
    if (!form.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) e.email   = "Enter a valid work email.";
    if (!form.password || form.password.length < 8)              e.password = "Use at least 8 characters.";
    if (form.password !== form.confirm)                           e.confirm  = "Passwords don't match.";
    if (!form.role)                                               e.role     = "Please select your role.";
    if (!form.terms)                                              e.terms    = "You must accept the terms to continue.";
    return e;
  }

  function handleSubmit(ev: React.FormEvent) {
    ev.preventDefault();
    setTouched(true);
    const e = validate();
    setErrors(e);
  }

  function borderFor(f: string) { return touched && errors[f] ? "#E53935" : "#E6E6E6"; }
  function shadowFor(f: string): string | undefined { return touched && errors[f] ? "0 0 0 3px #FFEBEE" : undefined; }

  function focusStyle(f: string) {
    return (e: React.FocusEvent<HTMLInputElement | HTMLSelectElement>) => {
      e.currentTarget.style.borderColor = "#0075DE";
      if (!errors[f]) e.currentTarget.style.boxShadow = "0 0 0 3px #D9E8FF";
    };
  }
  function blurStyle(f: string) {
    return (e: React.FocusEvent<HTMLInputElement | HTMLSelectElement>) => {
      e.currentTarget.style.borderColor = borderFor(f);
      e.currentTarget.style.boxShadow = shadowFor(f) ?? "none";
    };
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#F6F5F4",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "24px 24px 40px",
        fontFamily: "Inter, sans-serif",
      }}
    >
      {/* Home link */}
      <button
        onClick={() => navigate("/")}
        style={{
          position: "fixed",
          top: 24,
          left: 28,
          display: "flex",
          alignItems: "center",
          gap: 6,
          background: "none",
          border: "none",
          cursor: "pointer",
          fontSize: 13,
          color: "#615D59",
          fontFamily: "Inter, sans-serif",
          transition: "color 150ms",
        }}
        onMouseEnter={(e) => (e.currentTarget.style.color = "#000")}
        onMouseLeave={(e) => (e.currentTarget.style.color = "#615D59")}
      >
        <Package size={14} color="#0075DE" strokeWidth={2.5} />
        SmartStock AI
      </button>

      {/* Card */}
      <div
        style={{
          background: "#fff",
          border: "1px solid #E6E6E6",
          borderRadius: 16,
          padding: 40,
          width: "100%",
          maxWidth: 480,
          boxShadow: "0 2px 20px rgba(0,0,0,0.06)",
        }}
      >
        {/* Wordmark */}
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", marginBottom: 28 }}>
          <div
            style={{
              width: 40,
              height: 40,
              borderRadius: 12,
              background: "#0075DE",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              marginBottom: 14,
            }}
          >
            <Package size={20} color="#fff" strokeWidth={2.5} />
          </div>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: "#000", letterSpacing: "-0.3px", marginBottom: 8 }}>
            Create your account
          </h1>
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 6,
              background: "#E8F5E9",
              color: "#1AAE39",
              borderRadius: 999,
              padding: "4px 12px",
              fontSize: 12,
              fontWeight: 600,
            }}
          >
            <Check size={12} strokeWidth={3} />
            14-day free trial · No credit card required
          </div>
        </div>

        <form onSubmit={handleSubmit} noValidate style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {/* Full name */}
          <Field label="Full name" error={touched ? errors.name : undefined}>
            <input
              type="text"
              value={form.name}
              placeholder="Alex Johnson"
              onChange={(e) => set("name", e.target.value)}
              style={{ ...inputBase, borderColor: borderFor("name"), boxShadow: shadowFor("name") }}
              onFocus={focusStyle("name")}
              onBlur={blurStyle("name")}
            />
          </Field>

          {/* Work email */}
          <Field label="Work email" error={touched ? errors.email : undefined}>
            <input
              type="email"
              value={form.email}
              placeholder="you@company.com"
              onChange={(e) => set("email", e.target.value)}
              style={{ ...inputBase, borderColor: borderFor("email"), boxShadow: shadowFor("email") }}
              onFocus={focusStyle("email")}
              onBlur={blurStyle("email")}
            />
          </Field>

          {/* Password */}
          <Field label="Password" error={touched ? errors.password : undefined}>
            <div style={{ position: "relative" }}>
              <input
                type={showPw ? "text" : "password"}
                value={form.password}
                placeholder="Min. 8 characters"
                onChange={(e) => set("password", e.target.value)}
                style={{ ...inputBase, paddingRight: 44, borderColor: borderFor("password"), boxShadow: shadowFor("password") }}
                onFocus={focusStyle("password")}
                onBlur={blurStyle("password")}
              />
              <button
                type="button"
                onClick={() => setShowPw((v) => !v)}
                style={{ position: "absolute", right: 12, top: "50%", transform: "translateY(-50%)", background: "none", border: "none", cursor: "pointer", color: "#615D59", display: "flex", padding: 2 }}
              >
                {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
            <StrengthBar password={form.password} />
          </Field>

          {/* Confirm */}
          <Field label="Confirm password" error={touched ? errors.confirm : undefined}>
            <div style={{ position: "relative" }}>
              <input
                type={showCf ? "text" : "password"}
                value={form.confirm}
                placeholder="Repeat password"
                onChange={(e) => set("confirm", e.target.value)}
                style={{ ...inputBase, paddingRight: 44, borderColor: borderFor("confirm"), boxShadow: shadowFor("confirm") }}
                onFocus={focusStyle("confirm")}
                onBlur={blurStyle("confirm")}
              />
              <button
                type="button"
                onClick={() => setShowCf((v) => !v)}
                style={{ position: "absolute", right: 12, top: "50%", transform: "translateY(-50%)", background: "none", border: "none", cursor: "pointer", color: "#615D59", display: "flex", padding: 2 }}
              >
                {showCf ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </Field>

          {/* Role */}
          <Field label="Your role" error={touched ? errors.role : undefined}>
            <select
              value={form.role}
              onChange={(e) => set("role", e.target.value)}
              style={{
                ...inputBase,
                appearance: "none",
                cursor: "pointer",
                borderColor: borderFor("role"),
                boxShadow: shadowFor("role"),
                backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%23615D59' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E")`,
                backgroundRepeat: "no-repeat",
                backgroundPosition: "right 12px center",
                paddingRight: 40,
              }}
              onFocus={focusStyle("role")}
              onBlur={blurStyle("role")}
            >
              <option value="">Select your role…</option>
              {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
            </select>
          </Field>

          {/* Terms */}
          <div>
            <label
              style={{ display: "flex", alignItems: "flex-start", gap: 10, cursor: "pointer" }}
            >
              <div
                onClick={() => set("terms", !form.terms)}
                style={{
                  width: 18,
                  height: 18,
                  borderRadius: 5,
                  border: `1.5px solid ${touched && errors.terms ? "#E53935" : form.terms ? "#0075DE" : "#C9C7C4"}`,
                  background: form.terms ? "#0075DE" : "#fff",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  flexShrink: 0,
                  marginTop: 1,
                  cursor: "pointer",
                  transition: "background 150ms, border-color 150ms",
                }}
              >
                {form.terms && <Check size={11} color="#fff" strokeWidth={3} />}
              </div>
              <span style={{ fontSize: 13, color: "#615D59", lineHeight: 1.55 }}>
                I agree to the{" "}
                <a href="#" style={{ color: "#0075DE", textDecoration: "none", fontWeight: 500 }}>Terms of service</a>
                {" "}and{" "}
                <a href="#" style={{ color: "#0075DE", textDecoration: "none", fontWeight: 500 }}>Privacy policy</a>
              </span>
            </label>
            {touched && errors.terms && (
              <p style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 12, color: "#E53935", marginTop: 6, fontFamily: "Inter, sans-serif" }}>
                <AlertCircle size={12} /> {errors.terms}
              </p>
            )}
          </div>

          {/* Submit */}
          <button
            type="submit"
            style={{
              width: "100%",
              background: "#0075DE",
              color: "#fff",
              border: "none",
              borderRadius: 999,
              padding: "12px",
              fontSize: 15,
              fontWeight: 600,
              cursor: "pointer",
              fontFamily: "Inter, sans-serif",
              marginTop: 6,
              transition: "background 150ms, transform 100ms",
            }}
            onMouseEnter={(e) => (e.currentTarget.style.background = "#4A9EF5")}
            onMouseLeave={(e) => (e.currentTarget.style.background = "#0075DE")}
            onMouseDown={(e) => (e.currentTarget.style.transform = "scale(0.97)")}
            onMouseUp={(e) => (e.currentTarget.style.transform = "scale(1)")}
          >
            Create account
          </button>
        </form>

        {/* Divider */}
        <div style={{ display: "flex", alignItems: "center", gap: 12, margin: "20px 0" }}>
          <div style={{ flex: 1, height: 1, background: "#E6E6E6" }} />
          <span style={{ fontSize: 12, color: "#615D59" }}>or</span>
          <div style={{ flex: 1, height: 1, background: "#E6E6E6" }} />
        </div>

        {/* Google */}
        <button
          style={{
            width: "100%",
            background: "#fff",
            color: "#31302E",
            border: "1px solid #E6E6E6",
            borderRadius: 999,
            padding: "10px 16px",
            fontSize: 14,
            fontWeight: 600,
            cursor: "pointer",
            fontFamily: "Inter, sans-serif",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 10,
            transition: "background 150ms",
          }}
          onMouseEnter={(e) => (e.currentTarget.style.background = "#F6F5F4")}
          onMouseLeave={(e) => (e.currentTarget.style.background = "#fff")}
        >
          <GoogleIcon />
          Continue with Google
        </button>

        {/* Footer */}
        <p style={{ textAlign: "center", fontSize: 13, color: "#615D59", marginTop: 24 }}>
          Already have an account?{" "}
          <button
            onClick={() => navigate("/login")}
            style={{
              color: "#0075DE",
              fontWeight: 600,
              background: "none",
              border: "none",
              cursor: "pointer",
              fontSize: 13,
              fontFamily: "Inter, sans-serif",
              padding: 0,
            }}
          >
            Log in
          </button>
        </p>
      </div>
    </div>
  );
}
