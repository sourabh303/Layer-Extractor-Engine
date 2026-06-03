import { describe, it, expect, beforeEach } from 'vitest';
import { useStore } from './store';

describe('useStore', () => {
  beforeEach(() => {
    // Reset state before each test
    const initialState = useStore.getInitialState();
    useStore.setState(initialState);
  });

  it('should have correct initial state', () => {
    const state = useStore.getState();
    expect(state.hardwareMode).toBe('UNKNOWN');
    expect(state.sidecarPort).toBeNull();
    expect(state.ipcSecret).toBeNull();
    expect(state.extractionResult).toBeNull();
    expect(state.isProcessing).toBe(false);
    expect(state.isExporting).toBe(false);
    expect(state.toast).toEqual({ message: '', visible: false });
    expect(state.isAuthenticated).toBe(false);
    expect(state.machineId).toBeNull();
  });

  it('should set hardwareMode', () => {
    useStore.getState().setHardwareMode('GPU');
    expect(useStore.getState().hardwareMode).toBe('GPU');
  });

  it('should set sidecarPort', () => {
    useStore.getState().setSidecarPort(8080);
    expect(useStore.getState().sidecarPort).toBe(8080);
  });

  it('should set ipcSecret', () => {
    useStore.getState().setIpcSecret('secret123');
    expect(useStore.getState().ipcSecret).toBe('secret123');
  });

  it('should set extractionResult', () => {
    const result = {
      status: 'success',
      message: 'Done',
      source_path: '/tmp/test.png',
      layers_extracted: 3,
      hardware_mode_used: 'GPU',
    };
    useStore.getState().setExtractionResult(result);
    expect(useStore.getState().extractionResult).toEqual(result);

    // Can also be set to null
    useStore.getState().setExtractionResult(null);
    expect(useStore.getState().extractionResult).toBeNull();
  });

  it('should set isProcessing', () => {
    useStore.getState().setIsProcessing(true);
    expect(useStore.getState().isProcessing).toBe(true);
  });

  it('should set isExporting', () => {
    useStore.getState().setIsExporting(true);
    expect(useStore.getState().isExporting).toBe(true);
  });

  it('should set toast', () => {
    const toast = { message: 'Test message', visible: true, folderPath: '/tmp' };
    useStore.getState().setToast(toast);
    expect(useStore.getState().toast).toEqual(toast);
  });

  it('should hide toast', () => {
    // First set a toast
    const toast = { message: 'Test message', visible: true, folderPath: '/tmp' };
    useStore.getState().setToast(toast);

    // Then hide it
    useStore.getState().hideToast();
    expect(useStore.getState().toast.visible).toBe(false);
    expect(useStore.getState().toast.message).toBe('Test message'); // Message is preserved
    expect(useStore.getState().toast.folderPath).toBe('/tmp'); // Path is preserved
  });

  it('should set isAuthenticated', () => {
    useStore.getState().setIsAuthenticated(true);
    expect(useStore.getState().isAuthenticated).toBe(true);
  });

  it('should set machineId', () => {
    useStore.getState().setMachineId('machine-123');
    expect(useStore.getState().machineId).toBe('machine-123');
  });
});
