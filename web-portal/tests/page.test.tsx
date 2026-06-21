import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import Page from '../app/page';

// Mock cookies and createClient
vi.mock('next/headers', () => ({
  cookies: vi.fn(() => ({
    getAll: vi.fn(),
    setAll: vi.fn(),
  })),
}));

const mockGetSession = vi.fn();
const mockFrom = vi.fn();

vi.mock('../utils/supabase/server', () => ({
  createClient: vi.fn(() => ({
    auth: {
      getSession: mockGetSession,
    },
    from: mockFrom,
  })),
}));

// Mock child components
vi.mock('../app/components/AuthForm', () => ({
  default: () => <div data-testid="auth-form">Auth Form</div>,
}));

vi.mock('../app/components/SignOutButton', () => ({
  default: () => <div data-testid="sign-out-button">Sign Out</div>,
}));

describe('Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders landing page when not authenticated', async () => {
    mockGetSession.mockResolvedValue({ data: { session: null } });

    // Page is an async component, so we need to await it
    const jsx = await Page();
    render(jsx);

    expect(screen.getByText('Welcome to the Web Portal')).toBeInTheDocument();
    expect(screen.getByText('Sign in or create an account to view your portal content.')).toBeInTheDocument();
    expect(screen.getByTestId('auth-form')).toBeInTheDocument();
  });

  it('renders dashboard with todos when authenticated', async () => {
    const mockUser = { email: 'test@example.com' };
    mockGetSession.mockResolvedValue({ data: { session: { user: mockUser } } });

    const mockTodos = [
      { id: '1', name: 'Buy milk' },
      { id: '2', name: 'Walk the dog' },
    ];
    mockFrom.mockReturnValue({
      select: vi.fn().mockResolvedValue({ data: mockTodos, error: null }),
    });

    const jsx = await Page();
    render(jsx);

    expect(screen.getByText('Portal Dashboard')).toBeInTheDocument();
    expect(screen.getByText(`Signed in as ${mockUser.email}`)).toBeInTheDocument();
    expect(screen.getByTestId('sign-out-button')).toBeInTheDocument();

    expect(screen.getByText('Todo list')).toBeInTheDocument();
    expect(screen.getByText('Buy milk')).toBeInTheDocument();
    expect(screen.getByText('Walk the dog')).toBeInTheDocument();
  });

  it('renders dashboard with error when fetching todos fails', async () => {
    const mockUser = { email: 'test@example.com' };
    mockGetSession.mockResolvedValue({ data: { session: { user: mockUser } } });

    const mockError = { message: 'Database error' };
    mockFrom.mockReturnValue({
      select: vi.fn().mockResolvedValue({ data: null, error: mockError }),
    });

    const jsx = await Page();
    render(jsx);

    expect(screen.getByText('Portal Dashboard')).toBeInTheDocument();
    expect(screen.getByText(`Unable to load todos: ${mockError.message}`)).toBeInTheDocument();
  });

  it('renders dashboard with no todos message when array is empty', async () => {
    const mockUser = { email: 'test@example.com' };
    mockGetSession.mockResolvedValue({ data: { session: { user: mockUser } } });

    mockFrom.mockReturnValue({
      select: vi.fn().mockResolvedValue({ data: [], error: null }),
    });

    const jsx = await Page();
    render(jsx);

    expect(screen.getByText('Portal Dashboard')).toBeInTheDocument();
    expect(screen.getByText('No todo items found.')).toBeInTheDocument();
  });
});
