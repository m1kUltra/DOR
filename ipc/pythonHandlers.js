const path = require("path");
const { spawn } = require("child_process");

module.exports = function setupPythonHandlers(ipcMain, win) {
  // Match engine live runner — sends ticks to frontend
  ipcMain.handle("run-python", async () => {
    return new Promise((resolve, reject) => {
      const matchPath = path.join(__dirname, "../engine/matchEngine/match.py");
      const python = spawn("python3", [matchPath]);

      let output = "";

      python.stdout.on("data", (data) => {
        const lines = data.toString().split("\n").filter(Boolean);
        lines.forEach((line) => {
          try {
            const parsed = JSON.parse(line);
            win.webContents.send("match-tick", parsed); // 👈 sends each tick to frontend
          } catch (err) {
            console.warn("Non-JSON line from Python:", line);
          }
          output += line + "\n";
        });
      });

      python.stderr.on("data", (data) => {
        console.error("[Python error]", data.toString());
      });

      python.on("close", (code) => {
        console.log(`Python process exited with code ${code}`);
        resolve(output.trim());
      });

      python.on("error", reject);
    });
  });
};
