'use client';

import { useState } from 'react';
import { createClient } from '../../utils/supabase/client';

export default function AuthForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLogin, setIsLogin] = useState(true);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setMessage('');
    setLoading(true);

    const supabase = createClient();
    const payload = { email, password };
    const action = isLogin ? supabase.auth.signInWithPassword : supabase.auth.signUp;

    const { error } = await action(payload);
    setLoading(false);

    if (error) {
      setMessage(error.message);
      return;
    }

    setMessage(isLogin ? 'Logged in successfully. Reloading...' : 'Sign up complete. Please check your email to verify.');
    window.location.reload();
  };

  return (
    <div style={{ maxWidth: 420, margin: '0 auto', padding: '32px', background: '#f7f7f7', borderRadius: 16 }}>
      <h1 style={{ marginBottom: 16 }}>{isLogin ? 'Sign in' : 'Create account'}</h1>
      <form onSubmit={handleSubmit} style={{ display: 'grid', gap: 12 }}>
        <label style={{ display: 'grid', gap: 6 }}>
          Email
          <input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
            style={{ padding: 12, borderRadius: 8, border: '1px solid #ccc' }}
          />
        </label>
        <label style={{ display: 'grid', gap: 6 }}>
          Password
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
            minLength={6}
            style={{ padding: 12, borderRadius: 8, border: '1px solid #ccc' }}
          />
        </label>
        <button type="submit" disabled={loading} style={{ padding: 12, borderRadius: 8, border: 'none', background: '#0b69ff', color: '#fff', fontWeight: 'bold' }}>
          {loading ? 'Working…' : isLogin ? 'Sign in' : 'Create account'}
        </button>
      </form>
      {message ? <p style={{ marginTop: 16, color: '#333' }}>{message}</p> : null}
      <button
        type="button"
        onClick={() => {
          setIsLogin(!isLogin);
          setMessage('');
        }}
        style={{ marginTop: 20, background: 'none', border: 'none', color: '#0b69ff', cursor: 'pointer' }}
      >
        {isLogin ? 'Need an account? Create one' : 'Already have an account? Sign in'}
      </button>
    </div>
  );
}
