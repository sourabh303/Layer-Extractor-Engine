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
    <div className="max-w-[420px] mx-auto p-8 bg-gray-50 rounded-2xl shadow-sm border border-gray-100">
      <h1 className="mb-4 text-2xl font-semibold tracking-tight text-gray-900">{isLogin ? 'Sign in' : 'Create account'}</h1>
      <form onSubmit={handleSubmit} className="grid gap-3">
        <label className="grid gap-1.5 text-sm font-medium text-gray-700">
          Email
          <input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
            className="p-3 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-shadow"
          />
        </label>
        <label className="grid gap-1.5 text-sm font-medium text-gray-700">
          Password
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
            minLength={6}
            className="p-3 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-shadow"
          />
        </label>
        <button type="submit" disabled={loading} className="p-3 rounded-lg bg-blue-600 text-white font-bold hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
          {loading ? 'Working…' : isLogin ? 'Sign in' : 'Create account'}
        </button>
      </form>
      {message ? <p role="alert" className="mt-4 text-sm text-gray-800 bg-gray-100 p-3 rounded-md border border-gray-200">{message}</p> : null}
      <button
        type="button"
        onClick={() => {
          setIsLogin(!isLogin);
          setMessage('');
        }}
        className="mt-5 text-sm text-blue-600 hover:text-blue-800 focus:outline-none focus:underline font-medium w-full text-center transition-colors"
      >
        {isLogin ? 'Need an account? Create one' : 'Already have an account? Sign in'}
      </button>
    </div>
  );
}
