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
  extractionResult: ExtractionMetadata | null;
  isProcessing: boolean;
  isExporting: boolean;
  toast: ToastState;
  setHardwareMode: (mode: string) => void;
  setSidecarPort: (port: number) => void;
  setExtractionResult: (result: ExtractionMetadata | null) => void;
  setIsProcessing: (processing: boolean) => void;
  setIsExporting: (exporting: boolean) => void;
  setToast: (toast: ToastState) => void;
  hideToast: () => void;
}

export const useStore = create<AppState>((set) => ({
  hardwareMode: 'UNKNOWN',
  sidecarPort: null,
  extractionResult: null,
  isProcessing: false,
  isExporting: false,
  toast: { message: '', visible: false },
  setHardwareMode: (mode) => set({ hardwareMode: mode }),
  setSidecarPort: (port) => set({ sidecarPort: port }),
  setExtractionResult: (result) => set({ extractionResult: result }),
  setIsProcessing: (processing) => set({ isProcessing: processing }),
  setIsExporting: (exporting) => set({ isExporting: exporting }),
  setToast: (toast) => set({ toast }),
  hideToast: () => set((state) => ({ toast: { ...state.toast, visible: false } })),
}));
