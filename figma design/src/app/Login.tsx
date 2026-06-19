import { useState } from "react";
import { useNavigate } from "react-router";
import { Eye, EyeOff, Package, AlertCircle } from "lucide-react";

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

const inputStyle: React.CSSProperties = {
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

function Field({
  label,
  error,
  children,
}: {
  label: string;
  error?: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label
        style={{
          display: "block",
          fontSize: 13,
          fontWeight: 600,
          color: "#31302E",
          marginBottom: 6,
          fontFamily: "Inter, sans-serif",
        }}
      >
        {label}
      </label>
      {children}
      {error && (
        <p
          style={{
            display: "flex",
            alignItems: "center",
            gap: 5,
            fontSize: 12,
            color: "#E53935",
            marginTop: 6,
            fontFamily: "Inter, sans-serif",
          }}
        >
          <AlertCircle size={12} />
          {error}
        </p>
      )}
    </div>
  );
}

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw]     = useState(false);
  const [errors, setErrors]     = useState<{ email?: string; password?: string }>({});
  const [touched, setTouched]   = useState(false);

  function validate() {
    const e: typeof errors = {};
    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) e.email = "Enter a valid email address.";
    if (!password || password.length < 6) e.password = "Password must be at least 6 characters.";
    return e;
  }

  function handleSubmit(ev: React.FormEvent) {
    ev.preventDefault();
    setTouched(true);
    const e = validate();
    setErrors(e);
    if (!Object.keys(e).length) {
      // success — navigate to dashboard
    }
  }

  function borderFor(field: "email" | "password") {
    return touched && errors[field] ? "#E53935" : "#E6E6E6";
  }
  function shadowFor(field: "email" | "password") {
    return touched && errors[field] ? "0 0 0 3px #FFEBEE" : undefined;
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
        padding: 24,
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
          maxWidth: 440,
          boxShadow: "0 2px 20px rgba(0,0,0,0.06)",
        }}
      >
        {/* Wordmark */}
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", marginBottom: 32 }}>
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
          <h1 style={{ fontSize: 22, fontWeight: 700, color: "#000", letterSpacing: "-0.3px", marginBottom: 4 }}>
            Welcome back
          </h1>
          <p style={{ fontSize: 14, color: "#615D59" }}>Sign in to your SmartStock account</p>
        </div>

        <form onSubmit={handleSubmit} noValidate style={{ display: "flex", flexDirection: "column", gap: 18 }}>
          {/* Email */}
          <Field label="Email" error={touched ? errors.email : undefined}>
            <input
              type="email"
              value={email}
              placeholder="you@company.com"
              onChange={(e) => { setEmail(e.target.value); if (touched) setErrors((prev) => ({ ...prev, email: undefined })); }}
              style={{ ...inputStyle, borderColor: borderFor("email"), boxShadow: shadowFor("email") }}
              onFocus={(e) => { e.currentTarget.style.borderColor = "#0075DE"; if (!errors.email) e.currentTarget.style.boxShadow = "0 0 0 3px #D9E8FF"; }}
              onBlur={(e) => { e.currentTarget.style.borderColor = borderFor("email"); e.currentTarget.style.boxShadow = shadowFor("email") ?? "none"; }}
            />
          </Field>

          {/* Password */}
          <Field label="" error={touched ? errors.password : undefined}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
              <label style={{ fontSize: 13, fontWeight: 600, color: "#31302E", fontFamily: "Inter, sans-serif" }}>Password</label>
              <a
                href="#"
                style={{ fontSize: 13, color: "#0075DE", textDecoration: "none", fontWeight: 500 }}
                onMouseEnter={(e) => (e.currentTarget.style.textDecoration = "underline")}
                onMouseLeave={(e) => (e.currentTarget.style.textDecoration = "none")}
              >
                Forgot password?
              </a>
            </div>
            <div style={{ position: "relative" }}>
              <input
                type={showPw ? "text" : "password"}
                value={password}
                placeholder="••••••••"
                onChange={(e) => { setPassword(e.target.value); if (touched) setErrors((prev) => ({ ...prev, password: undefined })); }}
                style={{ ...inputStyle, paddingRight: 44, borderColor: borderFor("password"), boxShadow: shadowFor("password") }}
                onFocus={(e) => { e.currentTarget.style.borderColor = "#0075DE"; if (!errors.password) e.currentTarget.style.boxShadow = "0 0 0 3px #D9E8FF"; }}
                onBlur={(e) => { e.currentTarget.style.borderColor = borderFor("password"); e.currentTarget.style.boxShadow = shadowFor("password") ?? "none"; }}
              />
              <button
                type="button"
                onClick={() => setShowPw((v) => !v)}
                style={{
                  position: "absolute",
                  right: 12,
                  top: "50%",
                  transform: "translateY(-50%)",
                  background: "none",
                  border: "none",
                  cursor: "pointer",
                  color: "#615D59",
                  display: "flex",
                  alignItems: "center",
                  padding: 2,
                }}
              >
                {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </Field>

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
            Sign in
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
          Don't have an account?{" "}
          <button
            onClick={() => navigate("/signup")}
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
            Sign up
          </button>
        </p>
      </div>
    </div>
  );
}
