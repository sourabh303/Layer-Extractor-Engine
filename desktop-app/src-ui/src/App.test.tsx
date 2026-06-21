import React from 'react';
import '@testing-library/jest-dom';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import App from './App';
import { useStore } from './store';

// Mock Tauri modules
vi.mock('@tauri-apps/api/core', () => ({
  invoke: vi.fn((cmd) => {
    if (cmd === 'get_ipc_secret') return Promise.resolve('test-secret');
    if (cmd === 'get_machine_id') return Promise.resolve('test-machine-id');
    return Promise.resolve();
  }),
}));

vi.mock('@tauri-apps/plugin-shell', () => {
  const onDataMock = vi.fn();
  return {
    Command: {
      sidecar: vi.fn(() => ({
        stdout: { on: onDataMock },
        stderr: { on: onDataMock },
        spawn: vi.fn(() => Promise.resolve({ kill: vi.fn() })),
      })),
    },
    open: vi.fn(() => Promise.resolve()),
  };
});

vi.mock('@tauri-apps/plugin-dialog', () => ({
  open: vi.fn(() => Promise.resolve('/test/path/image.png')),
}));

// Mock React Konva
vi.mock('react-konva', () => ({
  Stage: ({ children }: { children: React.ReactNode }) => <div data-testid="konva-stage">{children}</div>,
  Layer: ({ children }: { children: React.ReactNode }) => <div data-testid="konva-layer">{children}</div>,
  Rect: () => <div data-testid="konva-rect" />,
}));

// Mock Supabase
vi.mock('./supabase', () => ({
  supabase: {
    auth: {
      getSession: vi.fn(() => Promise.resolve({ data: { session: null } })),
      signOut: vi.fn(() => Promise.resolve()),
    },
  },
}));

// Mock Login Component
vi.mock('./components/Login', () => ({
  Login: () => <div data-testid="login-component">Login Screen</div>,
}));

// Mock global fetch
const mockFetch = vi.fn();
globalThis.fetch = mockFetch as never;

describe('App Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useStore.setState({
      hardwareMode: 'UNKNOWN',
      sidecarPort: null,
      ipcSecret: null,
      extractionResult: null,
      isProcessing: false,
      isExporting: false,
      toast: { message: '', visible: false },
      isAuthenticated: false,
      machineId: null,
    });
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ mode: 'CPU' }),
    });
  });

  it('renders Login screen when not authenticated', () => {
    render(<App />);
    expect(screen.getByTestId('login-component')).toBeInTheDocument();
  });

  it('renders main interface when authenticated', () => {
    useStore.setState({ isAuthenticated: true, sidecarPort: 8080 });
    render(<App />);

    expect(screen.queryByTestId('login-component')).not.toBeInTheDocument();
    expect(screen.getByText('AI Textile Layer Extraction')).toBeInTheDocument();
    expect(screen.getByText('Upload Image')).toBeInTheDocument();
    expect(screen.getByText('No Image Uploaded')).toBeInTheDocument();
    expect(screen.getByText(/Sidecar Connected/)).toBeInTheDocument();
  });

  it('shows warning when Hardware Mode is CPU', () => {
    useStore.setState({ isAuthenticated: true, sidecarPort: 8080, hardwareMode: 'CPU' });
    render(<App />);
    expect(screen.getByText(/Hardware Acceleration Disabled/)).toBeInTheDocument();
  });

  it('handles Upload Image action successfully', async () => {
    useStore.setState({ isAuthenticated: true, sidecarPort: 8080, ipcSecret: 'secret' });

    mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({ mode: "CPU" }) }); mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        layers_extracted: 3,
        hardware_mode_used: 'GPU',
        status: 'success',
        message: 'done',
        source_path: '/test/path/image.png'
      }),
    });

    render(<App />);

    const uploadBtn = screen.getByText('Upload Image');
    fireEvent.click(uploadBtn);

    await waitFor(() => {
      expect(screen.getByText('Layer 1')).toBeInTheDocument();
      expect(screen.getByText('Layer 2')).toBeInTheDocument();
      expect(screen.getByText('Layer 3')).toBeInTheDocument();
      expect(screen.getByTestId('konva-stage')).toBeInTheDocument();
    });
  });

  it('handles Export action successfully', async () => {
    useStore.setState({
      isAuthenticated: true,
      sidecarPort: 8080,
      ipcSecret: 'secret',
      extractionResult: {
        layers_extracted: 1,
        hardware_mode_used: 'GPU',
        status: 'success',
        message: 'done',
        source_path: '/test/path/image.png'
      }
    });

    mockFetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({ mode: "CPU" }) }); mockFetch.mockResolvedValueOnce({
      ok: true,
      statusText: 'OK'
    });

    render(<App />);

    // Select export format
    const psdCheckbox = screen.getByLabelText('PSD');
    fireEvent.click(psdCheckbox);

    const exportBtn = screen.getByText('Export');
    expect(exportBtn).not.toBeDisabled();

    fireEvent.click(exportBtn);

    await waitFor(() => {
      expect(screen.getByText('Export successful!')).toBeInTheDocument();
    });
  });

  it('shows and hides toast notification', async () => {
    useStore.setState({ isAuthenticated: true, toast: { message: 'Test Notification', visible: true } });
    render(<App />);

    expect(screen.getByText('Test Notification')).toBeInTheDocument();

    const closeBtn = screen.getByLabelText('Close notification');
    fireEvent.click(closeBtn);

    await waitFor(() => {
      expect(useStore.getState().toast.visible).toBe(false);
    });
  });
});
