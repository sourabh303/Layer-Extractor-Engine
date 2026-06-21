import React, { useState } from 'react';
import { supabase } from '../supabase';
import { useStore } from '../store';
import { invoke } from '@tauri-apps/api/core';

export const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLogin, setIsLogin] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const { sidecarPort, ipcSecret, setIsAuthenticated, machineId, setMachineId } = useStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      let hwId = machineId;
      if (!hwId) {
        hwId = await invoke<string>('get_machine_id');
        setMachineId(hwId);
      }

      let authResult;
      if (isLogin) {
        authResult = await supabase.auth.signInWithPassword({ email, password });
      } else {
        authResult = await supabase.auth.signUp({ email, password });
      }

      if (authResult.error) {
        throw new Error(authResult.error.message);
      }

      const session = authResult.data.session;
      if (!session) {
        throw new Error('Authentication failed, no session returned.');
      }

      if (!sidecarPort) {
        throw new Error('Sidecar orchestrator is not ready yet.');
      }

      const response = await fetch(`http://127.0.0.1:${sidecarPort}/api/license/activate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-IPC-Secret': ipcSecret || ''
        },
        body: JSON.stringify({
          jwt: session.access_token,
          machine_id: hwId
        })
      });

      if (!response.ok) {
        throw new Error('License activation or hardware binding failed.');
      }

      setIsAuthenticated(true);

    } catch (err: unknown) {
        if (err instanceof Error) {
            setError(err.message);
        } else {
            setError('An unknown error occurred');
        }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
      backgroundColor: '#1e1e24', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 9999
    }}>
      <div style={{
        backgroundColor: '#2b2b36', padding: '40px', borderRadius: '8px', width: '350px',
        boxShadow: '0 10px 25px rgba(0,0,0,0.5)', display: 'flex', flexDirection: 'column', gap: '20px'
      }}>
        <h2 style={{ margin: 0, textAlign: 'center', color: '#fff', fontSize: '24px' }}>
          {isLogin ? 'Welcome Back' : 'Start 30-Day Trial'}
        </h2>

        {error && <div role="alert" style={{ color: '#f72585', fontSize: '14px', textAlign: 'center', padding: '10px', backgroundColor: 'rgba(247, 37, 133, 0.1)', borderRadius: '4px' }}>{error}</div>}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
            <label htmlFor="email" style={{ fontSize: '14px', color: '#ccc' }}>Email Address</label>
            <input
              id="email"
              type="email"
              placeholder="Email Address"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
              disabled={loading}
              style={{ padding: '12px', borderRadius: '4px', border: '1px solid #444', backgroundColor: '#1e1e24', color: '#fff', fontSize: '14px', opacity: loading ? 0.7 : 1 }}
            />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
            <label htmlFor="password" style={{ fontSize: '14px', color: '#ccc' }}>Password</label>
            <input
              id="password"
              type="password"
              placeholder="Password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
              disabled={loading}
              style={{ padding: '12px', borderRadius: '4px', border: '1px solid #444', backgroundColor: '#1e1e24', color: '#fff', fontSize: '14px', opacity: loading ? 0.7 : 1 }}
            />
          </div>

          <button
            type="submit"
            disabled={loading || !sidecarPort}
            aria-busy={loading}
            style={{
              padding: '12px', backgroundColor: '#4361ee', color: '#fff', border: 'none', borderRadius: '4px',
              fontSize: '16px', fontWeight: 'bold', cursor: (loading || !sidecarPort) ? 'not-allowed' : 'pointer',
              opacity: (loading || !sidecarPort) ? 0.7 : 1, marginTop: '10px'
            }}
          >
            {loading ? 'Authenticating...' : (isLogin ? 'Login' : 'Start Trial')}
          </button>
        </form>

        <div style={{ textAlign: 'center', fontSize: '14px', color: '#aaa', marginTop: '10px' }}>
          {isLogin ? "Don't have an account? " : "Already have an account? "}
          <button
            type="button"
            onClick={() => { setIsLogin(!isLogin); setError(''); }}
            style={{ background: 'none', border: 'none', color: '#4cc9f0', cursor: 'pointer', textDecoration: 'underline', padding: 0 }}
          >
            {isLogin ? 'Sign up' : 'Log in'}
          </button>
        </div>

        {!sidecarPort && (
          <div style={{ textAlign: 'center', fontSize: '12px', color: '#ffb703', marginTop: '10px' }}>
            Waiting for secure sidecar connection...
          </div>
        )}
      </div>
    </div>
  );
};
