import { create } from 'zustand';

export interface ExtractionMetadata {
  status: string;
  message: string;
  source_path: string;
  layers_extracted: number;
  hardware_mode_used: string;
}

interface AppState {
  hardwareMode: string;
  sidecarPort: number | null;
  extractionResult: ExtractionMetadata | null;
  isProcessing: boolean;
  setHardwareMode: (mode: string) => void;
  setSidecarPort: (port: number) => void;
  setExtractionResult: (result: ExtractionMetadata | null) => void;
  setIsProcessing: (processing: boolean) => void;
}

export const useStore = create<AppState>((set) => ({
  hardwareMode: 'UNKNOWN',
  sidecarPort: null,
  extractionResult: null,
  isProcessing: false,
  setHardwareMode: (mode) => set({ hardwareMode: mode }),
  setSidecarPort: (port) => set({ sidecarPort: port }),
  setExtractionResult: (result) => set({ extractionResult: result }),
  setIsProcessing: (processing) => set({ isProcessing: processing }),
}));
