import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import AuthForm from '../../app/components/AuthForm';

// Mock Supabase client
const mockSignInWithPassword = vi.fn();
const mockSignUp = vi.fn();

vi.mock('../../utils/supabase/client', () => {
  return {
    createClient: () => ({
      auth: {
        signInWithPassword: mockSignInWithPassword,
        signUp: mockSignUp,
      },
    }),
  };
});

describe('AuthForm', () => {
  const originalLocation = window.location;

  beforeEach(() => {
    vi.clearAllMocks();

    // Mock window.location.reload
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: { ...originalLocation, reload: vi.fn() },
    });
  });

  afterEach(() => {
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: originalLocation,
    });
  });

  it('renders login form by default', () => {
    render(<AuthForm />);
    expect(screen.getByRole('heading', { name: 'Sign in' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Sign in' })).toBeInTheDocument();
    expect(screen.getByLabelText('Email')).toBeInTheDocument();
    expect(screen.getByLabelText('Password')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Need an account? Create one' })).toBeInTheDocument();
  });

  it('toggles between login and sign up forms', async () => {
    const user = userEvent.setup();
    render(<AuthForm />);

    // Click toggle
    await user.click(screen.getByRole('button', { name: 'Need an account? Create one' }));

    // Should now show Sign up
    expect(screen.getByRole('heading', { name: 'Create account' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Create account' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Already have an account? Sign in' })).toBeInTheDocument();

    // Click toggle again
    await user.click(screen.getByRole('button', { name: 'Already have an account? Sign in' }));

    // Should be back to Sign in
    expect(screen.getByRole('heading', { name: 'Sign in' })).toBeInTheDocument();
  });

  it('handles successful login', async () => {
    const user = userEvent.setup();
    mockSignInWithPassword.mockResolvedValueOnce({ error: null });

    render(<AuthForm />);

    await user.type(screen.getByLabelText('Email'), 'test@example.com');
    await user.type(screen.getByLabelText('Password'), 'password123');

    await user.click(screen.getByRole('button', { name: 'Sign in' }));

    expect(mockSignInWithPassword).toHaveBeenCalledWith({
      email: 'test@example.com',
      password: 'password123',
    });

    await waitFor(() => {
      expect(screen.getByText('Logged in successfully. Reloading...')).toBeInTheDocument();
    });

    expect(window.location.reload).toHaveBeenCalledTimes(1);
  });

  it('handles successful sign up', async () => {
    const user = userEvent.setup();
    mockSignUp.mockResolvedValueOnce({ error: null });

    render(<AuthForm />);

    // Switch to sign up
    await user.click(screen.getByRole('button', { name: 'Need an account? Create one' }));

    await user.type(screen.getByLabelText('Email'), 'test@example.com');
    await user.type(screen.getByLabelText('Password'), 'password123');

    await user.click(screen.getByRole('button', { name: 'Create account' }));

    expect(mockSignUp).toHaveBeenCalledWith({
      email: 'test@example.com',
      password: 'password123',
    });

    await waitFor(() => {
      expect(screen.getByText('Sign up complete. Please check your email to verify.')).toBeInTheDocument();
    });

    expect(window.location.reload).toHaveBeenCalledTimes(1);
  });

  it('displays error message on failed login', async () => {
    const user = userEvent.setup();
    mockSignInWithPassword.mockResolvedValueOnce({
      error: { message: 'Invalid login credentials' }
    });

    render(<AuthForm />);

    await user.type(screen.getByLabelText('Email'), 'wrong@example.com');
    await user.type(screen.getByLabelText('Password'), 'wrongpass');

    await user.click(screen.getByRole('button', { name: 'Sign in' }));

    expect(mockSignInWithPassword).toHaveBeenCalledWith({
      email: 'wrong@example.com',
      password: 'wrongpass',
    });

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('Invalid login credentials');
    });

    expect(window.location.reload).not.toHaveBeenCalled();
  });

  it('disables button during loading state', async () => {
    const user = userEvent.setup();

    // Create a promise that we won't resolve immediately to simulate network delay
    let resolveLogin: any;
    const loginPromise = new Promise(resolve => {
      resolveLogin = resolve;
    });
    mockSignInWithPassword.mockReturnValueOnce(loginPromise);

    render(<AuthForm />);

    await user.type(screen.getByLabelText('Email'), 'test@example.com');
    await user.type(screen.getByLabelText('Password'), 'password123');

    // Button should be enabled initially
    const button = screen.getByRole('button', { name: 'Sign in' });
    expect(button).not.toBeDisabled();

    // Click submit
    await user.click(button);

    // Button should now be disabled and show "Working…"
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Working…' })).toBeDisabled();
    });

    // Resolve the promise to clean up
    resolveLogin({ error: null });

    // Wait for resolution so there are no unhandled pending state updates.
    await waitFor(() => {
        expect(screen.getByText('Logged in successfully. Reloading...')).toBeInTheDocument();
    });
  });
});
