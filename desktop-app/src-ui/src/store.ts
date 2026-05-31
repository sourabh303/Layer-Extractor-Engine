import { create } from 'zustand';

export interface ExtractionMetadata {
  status: string;
  message: string;
  source_path: string;
  layers_extracted: number;
  hardware_mode_used: string;
}

export interface ToastState {
  message: string;
  folderPath?: string;
  visible: boolean;
}

interface AppState {
  hardwareMode: string;
  sidecarPort: number | null;
  ipcSecret: string | null;
  extractionResult: ExtractionMetadata | null;
  isProcessing: boolean;
  isExporting: boolean;
  toast: ToastState;
  isAuthenticated: boolean;
  machineId: string | null;
  setHardwareMode: (mode: string) => void;
  setIpcSecret: (secret: string) => void;
  setSidecarPort: (port: number) => void;
  setIsAuthenticated: (auth: boolean) => void;
  setMachineId: (id: string) => void;
  setExtractionResult: (result: ExtractionMetadata | null) => void;
  setIsProcessing: (processing: boolean) => void;
  setIsExporting: (exporting: boolean) => void;
  setToast: (toast: ToastState) => void;
  hideToast: () => void;
}

export const useStore = create<AppState>((set) => ({
  hardwareMode: 'UNKNOWN',
  sidecarPort: null,
  ipcSecret: null,
  extractionResult: null,
  isProcessing: false,
  isExporting: false,
  toast: { message: '', visible: false },
  isAuthenticated: false,
  machineId: null,
  setHardwareMode: (mode) => set({ hardwareMode: mode }),
  setSidecarPort: (port) => set({ sidecarPort: port }),
  setIpcSecret: (secret) => set({ ipcSecret: secret }),
  setExtractionResult: (result) => set({ extractionResult: result }),
  setIsProcessing: (processing) => set({ isProcessing: processing }),
  setIsExporting: (exporting) => set({ isExporting: exporting }),
  setToast: (toast) => set({ toast }),
  hideToast: () => set((state) => ({ toast: { ...state.toast, visible: false } })),
  setIsAuthenticated: (auth) => set({ isAuthenticated: auth }),
  setMachineId: (id) => set({ machineId: id }),
}));
