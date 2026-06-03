import { describe, it, expect, beforeEach } from 'vitest';
import { useStore, type ExtractionMetadata } from './store';

describe('useStore', () => {
  beforeEach(() => {
    // Reset store state before each test
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

  it('should update hardwareMode', () => {
    useStore.getState().setHardwareMode('CPU');
    expect(useStore.getState().hardwareMode).toBe('CPU');
  });

  it('should update sidecarPort', () => {
    useStore.getState().setSidecarPort(8080);
    expect(useStore.getState().sidecarPort).toBe(8080);
  });

  it('should update ipcSecret', () => {
    useStore.getState().setIpcSecret('secret123');
    expect(useStore.getState().ipcSecret).toBe('secret123');
  });

  it('should update extractionResult', () => {
    const result: ExtractionMetadata = {
      status: 'success',
      message: 'Extraction complete',
      source_path: '/path/to/source',
      layers_extracted: 3,
      hardware_mode_used: 'GPU',
    };
    useStore.getState().setExtractionResult(result);
    expect(useStore.getState().extractionResult).toEqual(result);
  });

  it('should update isProcessing', () => {
    useStore.getState().setIsProcessing(true);
    expect(useStore.getState().isProcessing).toBe(true);
  });

  it('should update isExporting', () => {
    useStore.getState().setIsExporting(true);
    expect(useStore.getState().isExporting).toBe(true);
  });

  it('should update toast', () => {
    const toastData = { message: 'Hello', visible: true, folderPath: '/test' };
    useStore.getState().setToast(toastData);
    expect(useStore.getState().toast).toEqual(toastData);
  });

  it('should hide toast', () => {
    useStore.getState().setToast({ message: 'Hello', visible: true });
    useStore.getState().hideToast();
    expect(useStore.getState().toast.visible).toBe(false);
    expect(useStore.getState().toast.message).toBe('Hello'); // Message should persist, just visible changed
  });

  it('should update isAuthenticated', () => {
    useStore.getState().setIsAuthenticated(true);
    expect(useStore.getState().isAuthenticated).toBe(true);
  });

  it('should update machineId', () => {
    useStore.getState().setMachineId('machine-123');
    expect(useStore.getState().machineId).toBe('machine-123');
  });
});
