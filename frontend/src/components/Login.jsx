import { useMsal } from "@azure/msal-react";
import { loginRequest } from "../authConfig";
import { Activity } from "lucide-react";

export default function Login() {
  const { instance } = useMsal();

  const handleLogin = () => {
    instance.loginRedirect(loginRequest).catch((e) => {
      console.error(e);
    });
  };

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      backgroundColor: 'var(--bg-color)',
      color: 'var(--text-primary)',
      padding: '20px'
    }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        marginBottom: '40px'
      }}>
        <Activity size={40} color="var(--brand-primary)" />
        <span style={{ fontSize: '28px', fontWeight: 'bold' }}>CloudPulse</span>
      </div>

      <div style={{
        backgroundColor: 'var(--panel-bg)',
        border: '1px solid var(--border-color)',
        borderRadius: '12px',
        padding: '40px',
        textAlign: 'center',
        maxWidth: '400px',
        width: '100%',
        boxShadow: '0 8px 24px rgba(0,0,0,0.1)'
      }}>
        <h2 style={{ marginBottom: '16px', fontSize: '24px' }}>Welcome Back</h2>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '32px' }}>
          Sign in to access your multi-cloud dashboard and insights.
        </p>

        <button 
          onClick={handleLogin}
          style={{
            backgroundColor: '#0078D4', // Microsoft Blue
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            padding: '12px 24px',
            fontSize: '16px',
            fontWeight: '600',
            cursor: 'pointer',
            width: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '12px',
            transition: 'background-color 0.2s'
          }}
          onMouseOver={(e) => e.target.style.backgroundColor = '#005A9E'}
          onMouseOut={(e) => e.target.style.backgroundColor = '#0078D4'}
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 21 21">
            <path fill="#f35325" d="M0 0h10v10H0z"/>
            <path fill="#81bc06" d="M11 0h10v10H11z"/>
            <path fill="#05a6f0" d="M0 11h10v10H0z"/>
            <path fill="#ffba08" d="M11 11h10v10H11z"/>
          </svg>
          Sign in with Microsoft
        </button>
      </div>
      
      <p style={{ marginTop: '32px', color: 'var(--text-secondary)', fontSize: '14px' }}>
        Secure enterprise access via Microsoft Entra ID
      </p>
    </div>
  );
}
