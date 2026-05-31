import { useEffect, useState } from 'react';
import { Command, open as openShell } from '@tauri-apps/plugin-shell';
import { open } from '@tauri-apps/plugin-dialog';
import { Stage, Layer, Rect } from 'react-konva';
import { useStore } from './store';
import type { ExtractionRequest } from './types/ExtractionRequest';
import { Format } from './types/ExportRequest';
import type { ExportRequest } from './types/ExportRequest';
import { Login } from './components/Login';
import { supabase } from './supabase';
import { invoke } from '@tauri-apps/api/core';

function App() {
  const {
    sidecarPort,
    setSidecarPort,
    ipcSecret,
    setIpcSecret,
    hardwareMode,
    setHardwareMode,
    isProcessing,
    setIsProcessing,
    extractionResult,
    setExtractionResult,
    isExporting,
    setIsExporting,
    toast,
    setToast,
    hideToast,
    isAuthenticated,
    setIsAuthenticated,
    machineId,
    setMachineId
  } = useStore();

  const [exportFormats, setExportFormats] = useState({
    psd: false,
    svg: false,
    tiff: false,
    png: false,
  });
  const [tiffColorSpace, setTiffColorSpace] = useState<Format>(Format.TiffCmyk);

  useEffect(() => {
    // For Playwright Testing
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const handleMockState = (e: any) => {
      setHardwareMode(e.detail.hardwareMode);
      setSidecarPort(e.detail.sidecarPort);
      setIsProcessing(e.detail.isProcessing);
      setExtractionResult(e.detail.extractionResult);
    };
    window.addEventListener('set-mock-state', handleMockState);

    async function startSidecar() {
      const secret = await invoke<string>('get_ipc_secret');
      setIpcSecret(secret);

      const command = Command.sidecar('bin/src-core', ['--ipc-secret', secret]);

      command.stdout.on('data', line => {
        console.log(`[Sidecar Output]: ${line}`);
        if (line.includes('SIDECAR_PORT=')) {
          const port = parseInt(line.split('=')[1].trim());
          setSidecarPort(port);
        }
      });

      command.stderr.on('data', line => console.error(`[Sidecar Error]: ${line}`));

      const child = await command.spawn();

      return () => {
        child.kill();
      };
    }

    // Wrapping in try-catch because Command.sidecar throws when running in standard browser context
    try {
      startSidecar();
    } catch (e) {
      console.warn("Could not start sidecar:", e);
    }

    return () => {
      window.removeEventListener('set-mock-state', handleMockState);
    };
  }, [setSidecarPort, setHardwareMode, setIsProcessing, setExtractionResult, setIpcSecret]);

  // Boot sequence logic
  useEffect(() => {
    async function performBoot() {
      if (!sidecarPort || isAuthenticated) return;

      try {
        let hwId = machineId;
        if (!hwId) {
          hwId = await invoke<string>('get_machine_id');
          setMachineId(hwId);
        }

        const { data: { session } } = await supabase.auth.getSession();
        if (!session) return; // Need to login

        const response = await fetch(`http://127.0.0.1:${sidecarPort}/api/boot`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-IPC-Secret': ipcSecret || ''
          },
          body: JSON.stringify({
            jwt: session.access_token,
            machine_id: hwId
          })
        });

        if (response.ok) {
          setIsAuthenticated(true);
        } else {
          // Validation failed (e.g. offline cache expired and network down/invalid)
          await supabase.auth.signOut();
        }
      } catch (e) {
        console.error("Boot sequence failed:", e);
      }
    }

    performBoot();
  }, [sidecarPort, isAuthenticated, machineId, setMachineId, setIsAuthenticated, ipcSecret]);

  // Fetch hardware mode after authentication
  useEffect(() => {
    if (isAuthenticated && sidecarPort) {
        // Ping .NET for hardware status (which .NET relays from Python)
        // Note: The Python process might take a second to boot up after /api/boot or /api/license/activate
        const fetchStatus = () => {
          fetch(`http://127.0.0.1:${sidecarPort}/api/status`, {
            headers: {
              'X-IPC-Secret': ipcSecret || ''
            }
          })
            .then(res => res.json())
            .then(data => {
              if (data && data.mode) {
                setHardwareMode(data.mode);
              }
            })
            .catch(() => {
               // Retry after 1s if Python isn't fully up yet
               setTimeout(fetchStatus, 1000);
            });
        };
        fetchStatus();
    }
  }, [isAuthenticated, sidecarPort, setHardwareMode, ipcSecret]);

  const handleUpload = async () => {
    if (!sidecarPort) {
      alert("Sidecar is not ready yet!");
      return;
    }

    try {
      const selectedPath = await open({
        multiple: false,
        filters: [{
          name: 'Image',
          extensions: ['png', 'jpeg', 'jpg', 'tiff']
        }]
      });

      if (!selectedPath) return;

      setIsProcessing(true);

      const requestPayload: ExtractionRequest = {
        source_path: selectedPath as string
      };

      const response = await fetch(`http://127.0.0.1:${sidecarPort}/api/extract`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-IPC-Secret': ipcSecret || ''
        },
        body: JSON.stringify(requestPayload)
      });

      if (response.ok) {
        const data = await response.json();
        setExtractionResult(data);
        setHardwareMode(data.hardware_mode_used);
      } else {
        console.error("Extraction failed:", response.statusText);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleExport = async () => {
    if (!sidecarPort) {
      alert("Sidecar is not ready yet!");
      return;
    }

    try {
      const selectedFolder = await open({
        directory: true,
        multiple: false
      });

      if (!selectedFolder) return;

      setIsExporting(true);
      hideToast();

      const formats: Format[] = [];
      if (exportFormats.psd) formats.push(Format.Psd);
      if (exportFormats.svg) formats.push(Format.SVG);
      if (exportFormats.png) formats.push(Format.PNG);
      if (exportFormats.tiff) formats.push(tiffColorSpace);

      const requestPayload: ExportRequest = {
        destination_folder: selectedFolder as string,
        formats: formats
      };

      const response = await fetch(`http://127.0.0.1:${sidecarPort}/api/export`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-IPC-Secret': ipcSecret || ''
        },
        body: JSON.stringify(requestPayload)
      });

      if (response.ok) {
        setExtractionResult(null);
        setExportFormats({ psd: false, svg: false, tiff: false, png: false });
        setTiffColorSpace(Format.TiffCmyk);
        setToast({
          message: 'Export successful!',
          folderPath: selectedFolder as string,
          visible: true
        });
      } else {
        console.error("Export failed:", response.statusText);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsExporting(false);
    }
  };

  const handleFormatChange = (format: keyof typeof exportFormats) => {
    setExportFormats(prev => ({ ...prev, [format]: !prev[format] }));
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', backgroundColor: '#1e1e24', color: '#ffffff', position: 'relative' }}>

      {!isAuthenticated && <Login />}

      {/* Toast Notification */}
      {toast.visible && (
        <div style={{
          position: 'absolute',
          top: '20px',
          right: '20px',
          backgroundColor: '#4cc9f0',
          color: '#1e1e24',
          padding: '12px 20px',
          borderRadius: '4px',
          boxShadow: '0 4px 6px rgba(0,0,0,0.3)',
          display: 'flex',
          alignItems: 'center',
          gap: '15px',
          zIndex: 1000
        }}>
          <div>
            <strong>{toast.message}</strong>
            {toast.folderPath && (
              <div style={{ marginTop: '4px' }}>
                <a
                  href="#"
                  onClick={(e) => {
                    e.preventDefault();
                    if (toast.folderPath) openShell(toast.folderPath);
                  }}
                  style={{ color: '#005f73', textDecoration: 'underline', cursor: 'pointer', fontSize: '13px' }}
                >
                  Open Folder
                </a>
              </div>
            )}
          </div>
          <button
            onClick={hideToast}
            aria-label="Close notification"
            style={{
              background: 'transparent',
              border: 'none',
              color: '#1e1e24',
              fontSize: '16px',
              cursor: 'pointer',
              padding: '0 5px'
            }}
          >
            ✕
          </button>
        </div>
      )}

      {/* Top Toolbar */}
      <div style={{ padding: '10px 20px', borderBottom: '1px solid #333', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ margin: 0, fontSize: '18px' }}>AI Textile Layer Extraction</h2>
        {hardwareMode === 'CPU' && (
          <div role="alert" style={{ color: '#ffb703', fontSize: '14px', fontWeight: 'bold' }}>
            Hardware Acceleration Disabled: Segmentations may take 30 to 60 seconds per layer
          </div>
        )}
      </div>

      {/* Main Body */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>

        {/* Left Sidebar */}
        <div style={{ width: '260px', borderRight: '1px solid #333', padding: '20px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <button
            onClick={handleUpload}
            disabled={isProcessing || !sidecarPort}
            title={isProcessing ? 'Currently processing image...' : (!sidecarPort ? 'Waiting for sidecar connection...' : 'Upload an image')}
            aria-busy={isProcessing}
            style={{
              padding: '10px',
              backgroundColor: '#4361ee',
              color: '#fff',
              border: 'none',
              cursor: (isProcessing || !sidecarPort) ? 'not-allowed' : 'pointer',
              opacity: (isProcessing || !sidecarPort) ? 0.6 : 1,
              borderRadius: '4px',
              transition: 'opacity 0.2s, cursor 0.2s'
            }}
          >
            {isProcessing ? 'Processing...' : 'Upload Image'}
          </button>

          <div style={{ marginTop: '20px' }}>
            <h3 style={{ fontSize: '14px', color: '#aaa', margin: '0 0 10px 0' }}>Layers</h3>
            {extractionResult ? (
              Array.from({ length: extractionResult.layers_extracted }).map((_, i) => (
                <div key={i} style={{ padding: '8px', borderBottom: '1px solid #444', fontSize: '14px' }}>
                  Layer {i + 1}
                </div>
              ))
            ) : (
              <div style={{ color: '#666', fontSize: '14px' }}>No layers extracted yet.</div>
            )}
          </div>

          {/* Export Controls */}
          {extractionResult && (
            <div style={{ marginTop: 'auto', borderTop: '1px solid #333', paddingTop: '20px', display: 'flex', flexDirection: 'column', gap: '15px' }}>
              <h3 style={{ fontSize: '14px', color: '#aaa', margin: '0' }}>Export Options</h3>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '14px' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                  <input type="checkbox" checked={exportFormats.psd} onChange={() => handleFormatChange('psd')} />
                  PSD
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                  <input type="checkbox" checked={exportFormats.svg} onChange={() => handleFormatChange('svg')} />
                  SVG
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                  <input type="checkbox" checked={exportFormats.png} onChange={() => handleFormatChange('png')} />
                  PNG
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                  <input type="checkbox" checked={exportFormats.tiff} onChange={() => handleFormatChange('tiff')} />
                  TIFF
                </label>

                {exportFormats.tiff && (
                  <div style={{ marginLeft: '24px', display: 'flex', gap: '10px', fontSize: '13px' }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '4px', cursor: 'pointer' }}>
                      <input
                        type="radio"
                        name="tiffColorSpace"
                        value={Format.TiffCmyk}
                        checked={tiffColorSpace === Format.TiffCmyk}
                        onChange={() => setTiffColorSpace(Format.TiffCmyk)}
                      />
                      CMYK
                    </label>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '4px', cursor: 'pointer' }}>
                      <input
                        type="radio"
                        name="tiffColorSpace"
                        value={Format.TiffRGB}
                        checked={tiffColorSpace === Format.TiffRGB}
                        onChange={() => setTiffColorSpace(Format.TiffRGB)}
                      />
                      RGB
                    </label>
                  </div>
                )}
              </div>

              <button
                onClick={handleExport}
                disabled={isExporting || (!exportFormats.psd && !exportFormats.svg && !exportFormats.tiff && !exportFormats.png)}
                aria-busy={isExporting}
                style={{
                  padding: '10px',
                  backgroundColor: '#f72585',
                  color: '#fff',
                  border: 'none',
                  cursor: (isExporting || (!exportFormats.psd && !exportFormats.svg && !exportFormats.tiff && !exportFormats.png)) ? 'not-allowed' : 'pointer',
                  borderRadius: '4px',
                  opacity: (isExporting || (!exportFormats.psd && !exportFormats.svg && !exportFormats.tiff && !exportFormats.png)) ? 0.6 : 1
                }}
              >
                {isExporting ? 'Packaging Exports...' : 'Export'}
              </button>
            </div>
          )}
        </div>

        {/* Preview Canvas Area */}
        <div style={{ flex: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', backgroundColor: '#2b2b36' }}>
          {!extractionResult ? (
            <div style={{ color: '#666' }}>Upload an image to start extraction.</div>
          ) : (
             <Stage width={600} height={400}>
              <Layer>
                {/* Mock flat polygon shapes as per completion gate rules */}
                <Rect x={100} y={100} width={150} height={150} fill="#f72585" stroke="#fff" strokeWidth={2} />
                <Rect x={300} y={150} width={200} height={100} fill="#4cc9f0" stroke="#fff" strokeWidth={2} />
                <Rect x={150} y={250} width={100} height={100} fill="#fee440" stroke="#fff" strokeWidth={2} />
              </Layer>
            </Stage>
          )}
        </div>
      </div>

      {/* Bottom Status Bar */}
      <div role="status" aria-live="polite" style={{ padding: '10px 20px', borderTop: '1px solid #333', fontSize: '12px', display: 'flex', justifyContent: 'space-between', color: '#aaa' }}>
        <div>{isProcessing ? 'Running mock extraction...' : 'Ready'}</div>
        <div>
          {sidecarPort ? `Sidecar Connected (Port: ${sidecarPort})` : 'Waiting for Sidecar...'} | {hardwareMode} Mode
        </div>
      </div>

    </div>
  );
}

export default App;
