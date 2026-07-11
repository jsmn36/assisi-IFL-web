/**
 * Electron Main Process
 * Manages application window, backend subprocess, splash screen, and IPC
 */
const { app, BrowserWindow, ipcMain, dialog, shell, Menu } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');

const isDev = process.env.NODE_ENV === 'development';
const BACKEND_PORT = 8000;
const BACKEND_READY_TIMEOUT_MS = 30_000;
const BACKEND_POLL_INTERVAL_MS = 500;

let mainWindow = null;
let splashWindow = null;
let backendProcess = null;

// ── Window state persistence (simple file-based) ──────────────────────────────
const stateFile = path.join(app.getPath('userData'), 'window-state.json');

function loadWindowState() {
  try {
    if (fs.existsSync(stateFile)) {
      return JSON.parse(fs.readFileSync(stateFile, 'utf8'));
    }
  } catch {}
  return { width: 1280, height: 800, x: undefined, y: undefined };
}

function saveWindowState(win) {
  try {
    const bounds = win.getBounds();
    fs.writeFileSync(stateFile, JSON.stringify(bounds));
  } catch {}
}

// ── Backend health check ───────────────────────────────────────────────────────
function waitForBackend(timeoutMs) {
  return new Promise((resolve, reject) => {
    const deadline = Date.now() + timeoutMs;
    function check() {
      http.get(`http://127.0.0.1:${BACKEND_PORT}/health`, (res) => {
        if (res.statusCode === 200) return resolve();
        if (Date.now() < deadline) return setTimeout(check, BACKEND_POLL_INTERVAL_MS);
        reject(new Error('Backend did not become ready in time'));
      }).on('error', () => {
        if (Date.now() < deadline) return setTimeout(check, BACKEND_POLL_INTERVAL_MS);
        reject(new Error('Backend did not become ready in time'));
      });
    }
    check();
  });
}

// ── Backend subprocess ────────────────────────────────────────────────────────
function spawnBackend() {
  if (backendProcess) return;

  let backendCmd, backendArgs, backendCwd;

  if (isDev) {
    // Dev: run uvicorn directly from backend source
    backendCmd = process.platform === 'win32' ? 'python' : 'python3';
    backendArgs = ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', String(BACKEND_PORT)];
    backendCwd = path.join(__dirname, '..', 'backend');
  } else {
    // Production: PyInstaller-built binary
    const binaryName = process.platform === 'win32' ? 'backend-server.exe' : 'backend-server';
    const binaryPath = path.join(process.resourcesPath, 'backend', binaryName);
    backendCmd = binaryPath;
    backendArgs = [];
    backendCwd = path.join(process.resourcesPath, 'backend');
  }

  backendProcess = spawn(backendCmd, backendArgs, {
    cwd: backendCwd,
    env: { ...process.env },
    stdio: isDev ? 'inherit' : 'pipe',
  });

  backendProcess.on('error', (err) => {
    console.error('[Backend] spawn error:', err);
  });

  backendProcess.on('exit', (code) => {
    console.log(`[Backend] exited with code ${code}`);
    backendProcess = null;
  });
}

function killBackend() {
  if (backendProcess) {
    backendProcess.kill();
    backendProcess = null;
  }
}

// ── Splash window ─────────────────────────────────────────────────────────────
function createSplashWindow() {
  splashWindow = new BrowserWindow({
    width: 400,
    height: 300,
    frame: false,
    transparent: true,
    resizable: false,
    alwaysOnTop: true,
    webPreferences: { nodeIntegration: false, contextIsolation: true },
  });
  splashWindow.loadFile(path.join(__dirname, 'splash.html'));
}

// ── Main window ───────────────────────────────────────────────────────────────
function createMainWindow() {
  const state = loadWindowState();

  mainWindow = new BrowserWindow({
    width: state.width || 1280,
    height: state.height || 800,
    x: state.x,
    y: state.y,
    show: false,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      webSecurity: true,
      preload: path.join(__dirname, 'preload.js'),
    },
  });

  if (isDev) {
    mainWindow.loadURL('http://localhost:3000');
  } else {
    mainWindow.loadFile(path.join(__dirname, '..', 'frontend', 'dist', 'index.html'));
  }

  mainWindow.once('ready-to-show', () => {
    if (splashWindow && !splashWindow.isDestroyed()) {
      splashWindow.close();
      splashWindow = null;
    }
    mainWindow.show();
    if (isDev) mainWindow.webContents.openDevTools();
  });

  mainWindow.on('close', () => saveWindowState(mainWindow));
  mainWindow.on('closed', () => { mainWindow = null; });
}

// ── Application menu ──────────────────────────────────────────────────────────
function buildMenu() {
  const template = [
    {
      label: 'File',
      submenu: [{ role: 'quit' }],
    },
    {
      label: 'Edit',
      submenu: [
        { role: 'undo' }, { role: 'redo' }, { type: 'separator' },
        { role: 'cut' }, { role: 'copy' }, { role: 'paste' },
      ],
    },
    ...(isDev ? [{
      label: 'View',
      submenu: [
        { label: 'Developer Tools', accelerator: 'F12', click: () => mainWindow?.webContents.toggleDevTools() },
        { role: 'reload' },
      ],
    }] : []),
    {
      label: 'Help',
      submenu: [{
        label: 'About Assisi Social',
        click: () => dialog.showMessageBox(mainWindow, {
          type: 'info',
          title: 'About Assisi Social',
          message: 'Assisi Social',
          detail: `Version: ${app.getVersion()}\nElectron: ${process.versions.electron}\nNode: ${process.versions.node}`,
        }),
      }],
    },
  ];
  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

// ── IPC handlers ──────────────────────────────────────────────────────────────
ipcMain.handle('restart-backend', async () => {
  killBackend();
  spawnBackend();
  try {
    await waitForBackend(BACKEND_READY_TIMEOUT_MS);
    return { success: true };
  } catch (err) {
    return { success: false, error: err.message };
  }
});

ipcMain.handle('open-file-dialog', async () => {
  const result = await dialog.showOpenDialog(mainWindow, { properties: ['openFile'] });
  return result.canceled ? null : result.filePaths[0];
});

ipcMain.handle('save-file-dialog', async (_, defaultName) => {
  const result = await dialog.showSaveDialog(mainWindow, { defaultPath: defaultName });
  return result.canceled ? null : result.filePath;
});

ipcMain.handle('print-receipt', async (_, html) => {
  const win = new BrowserWindow({ show: false, webPreferences: { nodeIntegration: false, contextIsolation: true } });
  await win.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(html)}`);
  win.webContents.print({}, (success) => { win.close(); });
});

ipcMain.handle('get-app-version', () => app.getVersion());

// ── App lifecycle ─────────────────────────────────────────────────────────────
app.whenReady().then(async () => {
  buildMenu();
  createSplashWindow();
  spawnBackend();

  try {
    await waitForBackend(BACKEND_READY_TIMEOUT_MS);
  } catch (err) {
    dialog.showErrorBox('Backend Error', `Failed to start backend service:\n${err.message}`);
    app.quit();
    return;
  }

  createMainWindow();
});

app.on('window-all-closed', () => {
  killBackend();
  if (process.platform !== 'darwin') app.quit();
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createMainWindow();
});

app.on('before-quit', () => killBackend());
