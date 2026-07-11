/**
 * Electron Preload Script
 * Exposes IPC bridges to the renderer via contextBridge.
 * nodeIntegration is false — all Node access goes through this bridge only.
 */
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  /** Kill and respawn the backend process, wait for it to be ready. */
  restartBackend: () => ipcRenderer.invoke('restart-backend'),

  /** Open a native file picker; resolves to the selected path or null if cancelled. */
  openFileDialog: () => ipcRenderer.invoke('open-file-dialog'),

  /** Open a native save dialog; resolves to the destination path or null if cancelled. */
  saveFileDialog: (defaultName) => ipcRenderer.invoke('save-file-dialog', defaultName),

  /** Open the system print dialog for the given HTML string. */
  printReceipt: (html) => ipcRenderer.invoke('print-receipt', html),

  /** Return the packaged app version string. */
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),
});
