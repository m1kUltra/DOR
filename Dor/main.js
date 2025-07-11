const { app, BrowserWindow, ipcMain } = require("electron");
const path = require("path");
const { spawn } = require("child_process");

function createWindow() {
  const win = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true, // ✅ required for contextBridge to work
      nodeIntegration: false, // ✅ keeps renderer sandboxed
    },
  });

  win.webContents.openDevTools(); // optional debug
  win.loadURL("http://localhost:5173"); // during dev
  // win.loadFile("renderer/dist/index.html"); // when packaged
}

app.whenReady().then(() => {
  createWindow();

  app.on("activate", function () {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

// ✅ SAFELY run any Python script in the engine folder
ipcMain.handle("run-python", async (event, scriptName) => {
  return new Promise((resolve, reject) => {
    const scriptPath = path.join(__dirname, "engine", scriptName); // ✅ safer than using a string

    const py = spawn("python3", [scriptPath]);

    let output = "";
    py.stdout.on("data", (data) => (output += data));
    py.stderr.on("data", (data) => console.error(`Python error: ${data}`));
    py.on("close", () => resolve(output.trim()));
    py.on("error", reject);
  });
});
const sqlite3 = require("sqlite3").verbose();


const dbPath = path.join(__dirname, "engine", "GameData.db"); // ✅ Use uploaded DB
const db = new sqlite3.Database(dbPath);



ipcMain.handle("get-tables", async () => {
  return new Promise((resolve, reject) => {
    db.all(
      "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;",
      (err, rows) => {
        if (err) reject(err);
        else resolve(rows.map((row) => row.name));
      }
    );
  });
});

ipcMain.handle("get-table-data", async (_, tableName) => {
  return new Promise((resolve, reject) => {
    db.all(`SELECT * FROM ${tableName} LIMIT 100;`, (err, rows) => {
      if (err) reject(err);
      else resolve(rows);
    });
  });
});
ipcMain.handle("update-row", async (_, tableName, updatedRow) => {
  return new Promise((resolve, reject) => {
    // First: look up the actual primary key for this table
    db.get(`PRAGMA table_info(${tableName})`, (err, tableInfo) => {
      if (err) return reject(err);

      const primaryKey = tableInfo?.name || "id"; // fallback to "id" if unknown

      if (!updatedRow.hasOwnProperty(primaryKey)) {
        return reject(new Error(`Primary key '${primaryKey}' not found in row.`));
      }

      const keys = Object.keys(updatedRow).filter((key) => key !== primaryKey);
      const values = keys.map((k) => updatedRow[k]);
      const setClause = keys.map((k) => `${k} = ?`).join(", ");

      const sql = `UPDATE ${tableName} SET ${setClause} WHERE ${primaryKey} = ?`;
      db.run(sql, [...values, updatedRow[primaryKey]], function (err) {
        if (err) reject(err);
        else resolve({ success: true });
      });
    });
  });
});
