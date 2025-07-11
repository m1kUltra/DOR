// preload.js
const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("api", {
  runPython: (scriptName) => ipcRenderer.invoke("run-python", scriptName),

  getTables: () => ipcRenderer.invoke("get-tables"),
  getTableData: (tableName) => ipcRenderer.invoke("get-table-data", tableName),
  updateRow: (table, row) => ipcRenderer.invoke("update-row", table, row),
});