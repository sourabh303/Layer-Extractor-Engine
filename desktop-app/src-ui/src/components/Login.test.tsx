
import '@testing-library/jest-dom';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { Login } from './Login';
import { useStore } from '../store';
import { supabase } from '../supabase';
import { invoke } from '@tauri-apps/api/core';

vi.mock('../supabase', () => ({
  supabase: {
    auth: {
      signInWithPassword: vi.fn(),
      signUp: vi.fn(),
    },
  },
}));

vi.mock('@tauri-apps/api/core', () => ({
  invoke: vi.fn(),
}));

const mockFetch = vi.fn();
globalThis.fetch = mockFetch;

describe('Login Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useStore.setState({
      sidecarPort: null,
      ipcSecret: 'test-secret',
      isAuthenticated: false,
      machineId: null,
    });
  });

  it('renders login view by default', () => {
    render(<Login />);
    expect(screen.getByText('Welcome Back')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Email Address')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Password')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Login' })).toBeInTheDocument();
  });

  it('toggles to sign up view', () => {
    render(<Login />);
    fireEvent.click(screen.getByText('Sign up'));
    expect(screen.getByText('Start 30-Day Trial')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Start Trial' })).toBeInTheDocument();
  });

  it('disables submit button and shows waiting message when sidecarPort is missing', () => {
    render(<Login />);
    const button = screen.getByRole('button', { name: 'Login' });
    expect(button).toBeDisabled();
    expect(screen.getByText('Waiting for secure sidecar connection...')).toBeInTheDocument();
  });

  it('handles supabase authentication error', async () => {
    useStore.setState({ sidecarPort: 3000 });
    vi.mocked(supabase.auth.signInWithPassword).mockResolvedValueOnce({
      error: { message: "Invalid credentials", status: 400, name: "AuthError", code: "error", __isAuthError: true, toJSON: () => ({ name: "", message: "", status: 400, code: "" }) } as unknown as any,
      data: { user: null as unknown as any, session: null as unknown as any },
    });

    render(<Login />);
    fireEvent.change(screen.getByPlaceholderText('Email Address'), { target: { value: 'test@test.com' } });
    fireEvent.change(screen.getByPlaceholderText('Password'), { target: { value: 'password' } });
    fireEvent.click(screen.getByRole('button', { name: 'Login' }));

    await waitFor(() => {
      expect(screen.getByText('Invalid credentials')).toBeInTheDocument();
    });
  });

  it('successfully logs in and activates license', async () => {
    useStore.setState({ sidecarPort: 3000 });

    vi.mocked(invoke).mockResolvedValueOnce('mock-machine-id');
    vi.mocked(supabase.auth.signInWithPassword).mockResolvedValueOnce({
      error: null,
      data: { session: { access_token: 'mock-jwt' }, user: null },
    } as never);
    mockFetch.mockResolvedValueOnce({ ok: true });

    render(<Login />);
    fireEvent.change(screen.getByPlaceholderText('Email Address'), { target: { value: 'test@test.com' } });
    fireEvent.change(screen.getByPlaceholderText('Password'), { target: { value: 'password' } });
    fireEvent.click(screen.getByRole('button', { name: 'Login' }));

    await waitFor(() => {
      expect(invoke).toHaveBeenCalledWith('get_machine_id');
      expect(supabase.auth.signInWithPassword).toHaveBeenCalledWith({ email: 'test@test.com', password: 'password' });
      expect(mockFetch).toHaveBeenCalledWith('http://127.0.0.1:3000/api/license/activate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-IPC-Secret': 'test-secret'
        },
        body: JSON.stringify({
          jwt: 'mock-jwt',
          machine_id: 'mock-machine-id'
        })
      });
      expect(useStore.getState().isAuthenticated).toBe(true);
      expect(useStore.getState().machineId).toBe('mock-machine-id');
    });
  });

  it('successfully signs up and activates license', async () => {
    useStore.setState({ sidecarPort: 3000 });

    vi.mocked(invoke).mockResolvedValueOnce('mock-machine-id-2');
    vi.mocked(supabase.auth.signUp).mockResolvedValueOnce({
      error: null,
      data: { session: { access_token: 'mock-jwt-2' }, user: null },
    } as never);
    mockFetch.mockResolvedValueOnce({ ok: true });

    render(<Login />);

    // Switch to sign up
    fireEvent.click(screen.getByText('Sign up'));

    fireEvent.change(screen.getByPlaceholderText('Email Address'), { target: { value: 'new@test.com' } });
    fireEvent.change(screen.getByPlaceholderText('Password'), { target: { value: 'newpassword' } });
    fireEvent.click(screen.getByRole('button', { name: 'Start Trial' }));

    await waitFor(() => {
      expect(invoke).toHaveBeenCalledWith('get_machine_id');
      expect(supabase.auth.signUp).toHaveBeenCalledWith({ email: 'new@test.com', password: 'newpassword' });
      expect(mockFetch).toHaveBeenCalledWith('http://127.0.0.1:3000/api/license/activate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-IPC-Secret': 'test-secret'
        },
        body: JSON.stringify({
          jwt: 'mock-jwt-2',
          machine_id: 'mock-machine-id-2'
        })
      });
      expect(useStore.getState().isAuthenticated).toBe(true);
      expect(useStore.getState().machineId).toBe('mock-machine-id-2');
    });
  });

  it('handles missing session correctly', async () => {
    useStore.setState({ sidecarPort: 3000, machineId: 'existing-machine-id' });

    vi.mocked(supabase.auth.signInWithPassword).mockResolvedValueOnce({
      error: null,
      data: { session: null as unknown as any, user: null as unknown as any }, // No session returned
    });

    render(<Login />);
    fireEvent.change(screen.getByPlaceholderText('Email Address'), { target: { value: 'test@test.com' } });
    fireEvent.change(screen.getByPlaceholderText('Password'), { target: { value: 'password' } });
    fireEvent.click(screen.getByRole('button', { name: 'Login' }));

    await waitFor(() => {
      expect(screen.getByText('Authentication failed, no session returned.')).toBeInTheDocument();
      expect(mockFetch).not.toHaveBeenCalled();
    });
  });

  it('handles fetch failure correctly', async () => {
    useStore.setState({ sidecarPort: 3000, machineId: 'existing-machine-id' });

    vi.mocked(supabase.auth.signInWithPassword).mockResolvedValueOnce({
      error: null,
      data: { session: { access_token: 'mock-jwt' }, user: null },
    } as never);
    mockFetch.mockResolvedValueOnce({ ok: false });

    render(<Login />);
    fireEvent.change(screen.getByPlaceholderText('Email Address'), { target: { value: 'test@test.com' } });
    fireEvent.change(screen.getByPlaceholderText('Password'), { target: { value: 'password' } });
    fireEvent.click(screen.getByRole('button', { name: 'Login' }));

    await waitFor(() => {
      expect(invoke).not.toHaveBeenCalled(); // machineId already exists
      expect(mockFetch).toHaveBeenCalled();
      expect(screen.getByText('License activation or hardware binding failed.')).toBeInTheDocument();
    });
  });
});
