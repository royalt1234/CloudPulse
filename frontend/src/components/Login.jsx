import { useMsal } from "@azure/msal-react";
import { loginRequest } from "../authConfig";
import { Sun, Moon } from "lucide-react";

export default function Login({ theme, onThemeToggle }) {
  const { instance } = useMsal();

  const handleLogin = () => {
    instance.loginRedirect(loginRequest).catch((e) => {
      console.error(e);
    });
  };

  return (
    <div className="login-container">
      {/* Floating background glows */}
      <div className="login-glow-1" />
      <div className="login-glow-2" />

      {/* Top right theme toggle */}
      <button 
        className="login-theme-toggle" 
        onClick={onThemeToggle}
        title={theme === 'dark' ? "Switch to Light Mode" : "Switch to Dark Mode"}
      >
        {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
      </button>

      {/* Brand logo & Sign-in card */}
      <div className="login-card">
        <div className="login-brand">
          <svg className="header-logo" viewBox="0 0 34 34" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ width: 42, height: 42 }}>
            <circle cx="17" cy="17" r="17" fill="url(#grad_login)"/>
            <path d="M10 20l4-8 3 5 2-3 5 6" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <defs>
              <linearGradient id="grad_login" x1="0" y1="0" x2="34" y2="34" gradientUnits="userSpaceOnUse">
                <stop stopColor="#60a5fa"/>
                <stop offset="1" stopColor="#a78bfa"/>
              </linearGradient>
            </defs>
          </svg>
          <span>Cloud<span>Pulse</span></span>
        </div>

        <h2 className="login-title">Welcome Back</h2>
        <p className="login-subtitle">
          Sign in to access your unified multi-cloud insights and observability dashboard.
        </p>

        <button onClick={handleLogin} className="login-button">
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 21 21">
            <path fill="#f35325" d="M0 0h10v10H0z"/>
            <path fill="#81bc06" d="M11 0h10v10H11z"/>
            <path fill="#05a6f0" d="M0 11h10v10H0z"/>
            <path fill="#ffba08" d="M11 11h10v10H11z"/>
          </svg>
          Sign in with Microsoft
        </button>
      </div>
      
      <p className="login-footer">
        Secure enterprise access via Microsoft Entra ID
      </p>
    </div>
  );
}
