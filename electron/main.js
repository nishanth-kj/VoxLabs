const { app, BrowserWindow } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const http = require('http');

let mainWindow;
let apiProcess;

// Determine path to API binary
const isDev = !app.isPackaged;
const apiName = 'api-server.exe';
let apiPath;

if (isDev) {
    // In dev, we might assume the user runs the API separately, 
    // OR we can point to the one built in resources/bin
    apiPath = path.join(__dirname, 'resources', 'bin', apiName);
} else {
    // In prod, it's unpacked into resources/bin
    apiPath = path.join(process.resourcesPath, 'bin', apiName);
}

function startApi() {
    console.log(`Starting API from: ${apiPath}`);

    if (isDev) {
        console.log("In Dev mode: Skipping auto-launch of API. Please run 'uv run uvicorn main:app' manually if not using the binary.");
        // We can optionally try to spawn it if it exists
        // return;
    }

    // Spawn API process
    try {
        apiProcess = spawn(apiPath, [], {
            cwd: path.dirname(apiPath),
            detached: false,
            stdio: 'inherit' // Log to electron console
        });

        apiProcess.on('error', (err) => {
            console.error('Failed to start API:', err);
        });

        apiProcess.on('close', (code) => {
            console.log(`API process exited with code ${code}`);
        });
    } catch (e) {
        console.error("Error launching API:", e);
    }
}

// const serve = require('electron-serve');
// No longer needed for local file loading
// const loadURL = serve({ directory: path.join(process.resourcesPath, 'web') });

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        title: "VoxLabs",
        autoHideMenuBar: true, // Hide default menu
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        }
    });

    mainWindow.setMenuBarVisibility(false); // Force hide

    if (isDev) {
        // In dev, we can try to connect to the Vite dev server usually on 5173, but for now we'll stick to file loading
        // or the user can manually set it. 
        // For simplicity in this verifying flow:
        // mainWindow.loadURL('http://localhost:5173'); 
        // But since we are building:
        mainWindow.loadFile(path.join(__dirname, 'renderer-dist', 'index.html'));
    } else {
        // Load static local file in prod
        // We map 'renderer-dist' -> 'renderer' in extraResources
        const indexPath = path.join(process.resourcesPath, 'renderer', 'index.html');
        mainWindow.loadFile(indexPath);
    }
}

app.whenReady().then(() => {
    startApi();
    // Give API a moment to start? Frontend resilience handles it.
    createWindow();

    app.on('activate', function () {
        if (BrowserWindow.getAllWindows().length === 0) createWindow();
    });
});

app.on('window-all-closed', function () {
    if (process.platform !== 'darwin') app.quit();
});

app.on('will-quit', () => {
    if (apiProcess) {
        console.log("Killing API process...");
        apiProcess.kill();
    }
});
