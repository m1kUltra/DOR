const { app, BrowserWindow, ipcMain } = require("electron");
const path = require("path");

const setupDbHandlers = require("./ipc/dbHandlers");
const setupPythonHandlers = require("./ipc/pythonHandlers");
const setupSaveHandlers = require("./ipc/saveHandlers");
const setupSelectionHandlers = require("./ipc/selectionHandlers");

function createWindow() {
  const win = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  win.webContents.openDevTools();
    // win.loadFile("renderer/dist/index.html");
  win.loadURL("http://localhost:5173");

  return win; //
}




app.whenReady().then(() => {
  const win = createWindow();

  app.on("activate", function () {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });

  // Register all IPC handlers
  setupDbHandlers(ipcMain);
  setupPythonHandlers(ipcMain, win);
  setupSaveHandlers(ipcMain);
  setupSelectionHandlers(ipcMain);
});
