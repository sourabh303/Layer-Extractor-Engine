import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';
import os from 'os';

// Determine the Tauri target triple based on current OS
let targetTriple = '';
const platform = os.platform();
const arch = os.arch();

if (platform === 'linux' && arch === 'x64') {
    targetTriple = 'x86_64-unknown-linux-gnu';
} else if (platform === 'win32' && arch === 'x64') {
    targetTriple = 'x86_64-pc-windows-msvc';
} else if (platform === 'darwin' && arch === 'x64') {
    targetTriple = 'x86_64-apple-darwin';
} else if (platform === 'darwin' && arch === 'arm64') {
    targetTriple = 'aarch64-apple-darwin';
} else {
    console.error(`Unsupported platform/arch: ${platform}/${arch}`);
    process.exit(1);
}

const coreDir = path.resolve(process.cwd(), '../src-core');
const tauriBinDir = path.resolve(process.cwd(), 'src-tauri/bin');

console.log(`Building .NET Sidecar for target triple: ${targetTriple}...`);

// Ensure tauri bin directory exists
if (!fs.existsSync(tauriBinDir)) {
    fs.mkdirSync(tauriBinDir, { recursive: true });
}

// Publish the .NET Orchestrator
try {
    execSync('dotnet publish -c Release', { cwd: coreDir, stdio: 'inherit' });
} catch (error) {
    console.error('Failed to publish .NET project:', error.message);
    process.exit(1);
}

// Locate the built executable
const executableName = platform === 'win32' ? 'src-core.exe' : 'src-core';
const sourcePath = path.join(coreDir, `bin/Release/net8.0/publish/${executableName}`);
const destPath = path.join(tauriBinDir, `src-core-${targetTriple}${platform === 'win32' ? '.exe' : ''}`);

if (!fs.existsSync(sourcePath)) {
    console.error(`Could not find built executable at: ${sourcePath}`);
    process.exit(1);
}

// Copy and rename
fs.copyFileSync(sourcePath, destPath);

// Make executable on unix
if (platform !== 'win32') {
    fs.chmodSync(destPath, '755');
}

console.log(`Sidecar successfully built and copied to: ${destPath}`);
