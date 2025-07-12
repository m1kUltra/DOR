const path = require("path");
const sqlite3 = require("sqlite3").verbose();

const dbPath = path.join(__dirname, "../engine", "GameData.db");
const db = new sqlite3.Database(dbPath);

module.exports = function setupDbHandlers(ipcMain) {
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
      db.get(`PRAGMA table_info(${tableName})`, (err, tableInfo) => {
        if (err) return reject(err);

        const primaryKey = tableInfo?.name || "id";

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
};
