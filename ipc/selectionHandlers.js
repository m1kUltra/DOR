const sqlite3 = require("sqlite3").verbose();
const path = require("path");

module.exports = function setupSelectionHandlers(ipcMain) {
  ipcMain.handle("get-full-squad", async () => {
    const dbPath =
      global.currentSavePath || path.join(__dirname, "../saves/default.db");
    const db = new sqlite3.Database(dbPath);

    return new Promise((resolve, reject) => {
      db.get(
        `
        SELECT nt.squad_json
        FROM managers m
        JOIN national_teams nt ON nt.manager_id = m.manager_id
        WHERE m.is_user = 1
        LIMIT 1
        `,
        (err, row) => {
          if (err || !row || !row.squad_json) {
            db.close();
            return resolve({
              starters: [],
              subs: [],
              res: [],
              nis: [],
            });
          }

          let parsed = {};
          let playerIds = [];
          try {
            parsed = JSON.parse(row.squad_json);
            const sel = parsed.selection || {};
            playerIds = [
              ...(sel.starters || []),
              ...(sel.subs || []),
              ...(sel.res || []),
              ...(sel.nis || []),
            ].map((p) => p.player_id);
          } catch (parseErr) {
            db.close();
            return reject(parseErr);
          }

          if (playerIds.length === 0) {
            db.close();
            return resolve({
              starters: [],
              subs: [],
              res: [],
              nis: [],
            });
          }

          const placeholders = playerIds.map(() => "?").join(",");
          db.all(
            `SELECT * FROM players WHERE player_id IN (${placeholders})`,
            playerIds,
            (err2, playerRows) => {
              db.close();
              if (err2) return reject(err2);

              const lookup = Object.fromEntries(
                playerRows.map((p) => [p.player_id, p])
              );

              const resolvePlayers = (group) =>
                (parsed.selection?.[group] || []).map((p) => ({
                  ...p,
                  ...lookup[p.player_id],
                }));

              resolve({
                starters: resolvePlayers("starters"),
                subs: resolvePlayers("subs"),
                res: resolvePlayers("res"),
                nis: resolvePlayers("nis"),
              });
            }
          );
        }
      );
    });
  });

  // FIXED save-selection handler
  ipcMain.handle("save-selection", async (event, selection) => {
    return new Promise((resolve, reject) => {
      const dbPath =
        global.currentSavePath || path.join(__dirname, "../saves/default.db");
      const db = new sqlite3.Database(dbPath);
      const squadJson = JSON.stringify({ selection });

      db.run(
        `UPDATE national_teams
         SET squad_json = ?
         WHERE manager_id = (
           SELECT manager_id FROM managers WHERE is_user = 1 LIMIT 1
         )`,
        [squadJson],
        (err) => {
          db.close();
          if (err) {
            console.error("Failed to update squad_json:", err);
            reject(err);
          } else {
            console.log(" Squad selection saved to DB.");
            resolve({ success: true });
          }
        }
      );
    });
  });
};
