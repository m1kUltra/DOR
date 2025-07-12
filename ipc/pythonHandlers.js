const path = require("path");
const { spawn } = require("child_process");

module.exports = function setupPythonHandlers(ipcMain) {
  ipcMain.handle("run-python", async (event, scriptName) => {
    return new Promise((resolve, reject) => {
      const scriptPath = path.join(__dirname, "../engine", scriptName);
      const py = spawn("python3", [scriptPath]);

      let output = "";
      py.stdout.on("data", (data) => (output += data));
      py.stderr.on("data", (data) => console.error(`Python error: ${data}`));
      py.on("close", () => resolve(output.trim()));
      py.on("error", reject);
    });
  });
};
