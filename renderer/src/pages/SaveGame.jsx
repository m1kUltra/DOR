import React, { useState, useEffect } from "react";
import "./newgame.css";
import "./savegame.css"; // 👉 create this CSS file if needed

export default function SaveGame({ onReturn }) {
  const [saveName, setSaveName] = useState("");
  const [availableSaves, setAvailableSaves] = useState([]);
  const [status, setStatus] = useState("");
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    window.api.getAvailableSaves().then(setAvailableSaves);
  }, []);

  const handleCommit = () => {
    if (!saveName) return setStatus("Enter a save name.");
    window.api.commitTempDb(saveName);
    setStatus(`✅ Game saved as ${saveName}.db`);
    setSaveSuccess(true);
  };

  const handleOverwrite = (path) => {
  const existingName = path.split("/").pop().replace(/\.db$/, "");

  const confirmed = window.confirm(
    `Are you sure you want to overwrite "${existingName}.db"? This cannot be undone.`
  );

  if (!confirmed) return;

  window.api.commitTempDb(existingName);
  setStatus(`♻️ Overwrote ${existingName}.db`);
  setSaveSuccess(true);
};


  return (
    <div className="screen">
      {/* Top-right back button */}
      <button className="top-right-back" onClick={onReturn}>⏪ Back to Game</button>

      <h2>💾 Save Game</h2>

      <div>
        <label>New Save Name:</label>
        <input
          type="text"
          value={saveName}
          onChange={(e) => setSaveName(e.target.value)}
          placeholder="e.g. Midseason Backup"
        />
      </div>

      <button onClick={handleCommit}>Save as New</button>

      <hr />

      <h3>Overwrite Existing Save</h3>
      <div>
        <select onChange={(e) => handleOverwrite(e.target.value)}>
          <option value="">-- Select Save File --</option>
          {availableSaves.map((save) => (
            <option key={save.path} value={save.path}>
              {save.name} ({new Date(save.modified).toLocaleString()})
            </option>
          ))}
        </select>
      </div>

      <p>{status}</p>

      {/* Optional footer button */}
      {!saveSuccess && <button onClick={onReturn}>🔙 Back</button>}

      {/* Central popup */}
      {saveSuccess && (
        <div className="save-popup">
          <h2>✅ Save Successful!</h2>
          <p>{status}</p>
          <button onClick={onReturn}>Back to Game</button>
        </div>
      )}
    </div>
  );
}
