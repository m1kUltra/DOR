// preload.js
const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("api", {
  runPython: (scriptName) => ipcRenderer.invoke("run-python", scriptName),

  getTables: () => ipcRenderer.invoke("get-tables"),
  getTableData: (tableName) => ipcRenderer.invoke("get-table-data", tableName),
  updateRow: (table, row) => ipcRenderer.invoke("update-row", table, row),
  runSaveScript: (payload) => ipcRenderer.send("run-save-script", payload),
  getAvailableSaves: () => ipcRenderer.invoke("get-available-saves"),
  loadSave: (savePath) => ipcRenderer.send("load-save", savePath),
  getManagerInfo: () => ipcRenderer.invoke("get-manager-info"),

  
});