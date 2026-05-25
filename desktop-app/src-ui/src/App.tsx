import { useEffect } from 'react';
import { Command } from '@tauri-apps/plugin-shell';
import { open } from '@tauri-apps/plugin-dialog';
import { Stage, Layer, Rect } from 'react-konva';
import { useStore } from './store';
import type { ExtractionRequest } from './types/ExtractionRequest';

function App() {
  const {
    sidecarPort,
    setSidecarPort,
    hardwareMode,
    setHardwareMode,
    isProcessing,
    setIsProcessing,
    extractionResult,
    setExtractionResult
  } = useStore();

  useEffect(() => {
    // For Playwright Testing
    const handleMockState = (e: any) => {
      setHardwareMode(e.detail.hardwareMode);
      setSidecarPort(e.detail.sidecarPort);
      setIsProcessing(e.detail.isProcessing);
      setExtractionResult(e.detail.extractionResult);
    };
    window.addEventListener('set-mock-state', handleMockState);

    async function startSidecar() {
      const command = Command.sidecar('bin/src-core');

      command.stdout.on('data', line => {
        console.log(`[Sidecar Output]: ${line}`);
        if (line.includes('SIDECAR_PORT=')) {
          const port = parseInt(line.split('=')[1].trim());
          setSidecarPort(port);

          // Ping .NET for hardware status (which .NET relays from Python)
          fetch(`http://127.0.0.1:${port}/api/status`)
            .then(res => res.json())
            .then(data => {
              if (data && data.mode) {
                setHardwareMode(data.mode);
              }
            })
            .catch(err => console.error("Failed to fetch hardware status:", err));
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
  }, [setSidecarPort, setHardwareMode, setIsProcessing, setExtractionResult]);

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
          'Content-Type': 'application/json'
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

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', backgroundColor: '#1e1e24', color: '#ffffff' }}>

      {/* Top Toolbar */}
      <div style={{ padding: '10px 20px', borderBottom: '1px solid #333', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ margin: 0, fontSize: '18px' }}>AI Textile Layer Extraction</h2>
        {hardwareMode === 'CPU' && (
          <div style={{ color: '#ffb703', fontSize: '14px', fontWeight: 'bold' }}>
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
            style={{ padding: '10px', backgroundColor: '#4361ee', color: '#fff', border: 'none', cursor: 'pointer', borderRadius: '4px' }}
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
      <div style={{ padding: '10px 20px', borderTop: '1px solid #333', fontSize: '12px', display: 'flex', justifyContent: 'space-between', color: '#aaa' }}>
        <div>{isProcessing ? 'Running mock extraction...' : 'Ready'}</div>
        <div>
          {sidecarPort ? `Sidecar Connected (Port: ${sidecarPort})` : 'Waiting for Sidecar...'} | {hardwareMode} Mode
        </div>
      </div>

    </div>
  );
}

export default App;
