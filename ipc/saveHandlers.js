const path = require("path");
const fs = require("fs");
const { exec } = require("child_process");

const savesDir = path.join(__dirname, "../saves"); // Must be here, top-level



module.exports = function setupSaveHandlers(ipcMain) {
ipcMain.on("run-save-script", (event, payload) => {
  try {
    const filePath = path.join(__dirname, "../tmp", "new_save.json");
    fs.writeFileSync(filePath, JSON.stringify(payload, null, 2));

    const saveName = payload.save_name;
    const saveDbPath = path.join(__dirname, "../saves", `${saveName}.db`);

    exec("python3 backend/create_save.py", (error, stdout, stderr) => {
      if (error) {
        console.error(error);
        event.reply("run-save-script-complete", { success: false, error: error.message });
        return;
      }
      if (stderr) console.error(stderr);
      console.log(stdout);

      global.currentSavePath = saveDbPath;
      console.log(`New save created and loaded: ${saveDbPath}`);

      // ✅ Notify renderer
      event.reply("run-save-script-complete", { success: true, savePath: saveDbPath });
    });
  } catch (err) {
    console.error("Error saving new_save.json:", err);
    event.reply("run-save-script-complete", { success: false, error: err.message });
  }
});



  ipcMain.handle("get-available-saves", async () => {
  try {
    const files = fs
      .readdirSync(savesDir)
      .filter((file) => file.endsWith(".db"))
      .map((file) => {
        const fullPath = path.join(savesDir, file);
        const stats = fs.statSync(fullPath);
        return {
          name: file.replace(/\.db$/, ""),
          path: fullPath,
          modified: stats.mtimeMs, // last modified timestamp
        };
      });

    //  Sort by modified date (newest first)
    

    return files;
  } catch (err) {
    console.error("Error reading saves folder:", err);
    return [];
  }
});

ipcMain.on("load-save", (event, savePath) => {
  try {
    const tempPath = path.join(__dirname, "../tmp", "temp.db");

    // ✅ Copy the real save into temp location
    fs.copyFileSync(savePath, tempPath);

    // ✅ Point all queries at temp
    global.currentSavePath = tempPath;

    console.log(`🗂️ Loaded save into temp: ${tempPath}`);
  } catch (err) {
    console.error("❌ Failed to load save into temp:", err);
  }
});
  const sqlite3 = require("sqlite3").verbose();

ipcMain.handle("get-manager-info", async () => {
  try {
    const dbPath = global.currentSavePath || path.join(__dirname, "../saves", "default.db");
    const db = new sqlite3.Database(dbPath);

    return new Promise((resolve, reject) => {
      db.get(
        `
        SELECT m.name as managerName,
               nt.team_name as teamName
        FROM managers m
        LEFT JOIN national_teams nt ON nt.manager_id = m.manager_id
        WHERE m.is_user = 1
        LIMIT 1
        `,
        (err, row) => {
          db.close();
          if (err) {
            console.error("Failed to load manager info:", err);
            return reject(err);
          }
          resolve(row || {});
        }
      );
    });
  } catch (err) {
    console.error("Error in get-manager-info:", err);
    return {};
  }
});
ipcMain.on("commit-temp-db", (event, saveName) => {
  const tempPath = path.join(__dirname, "../tmp/temp.db");
  const targetPath = path.join(__dirname, "../saves", `${saveName}.db`);
  fs.copyFileSync(tempPath, targetPath);
  console.log("💾 Save committed to:", targetPath);
});
};


