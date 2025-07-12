import React, { useState, useEffect } from "react";
import "./newgame.css";
export default function NewGame({ onLaunchGame }) {
  const [nations, setNations] = useState([]);
  const [selectedNationId, setSelectedNationId] = useState(null);
  const [saveName, setSaveName] = useState("");
  const [managerName, setManagerName] = useState("");
  const [status, setStatus] = useState("");
  const [saveReady, setSaveReady] = useState(false);
  const [availableSaves, setAvailableSaves] = useState([]);

  useEffect(() => {
    window.api.getTableData("national_teams").then(setNations);
    window.api.getAvailableSaves().then(setAvailableSaves);
  }, []);

  const handleStart = () => {
  if (!saveName) return setStatus("Enter a save name.");
  if (!managerName) return setStatus("Enter a manager name.");
  if (!selectedNationId) return setStatus("Select a team.");

  const payload = {
    save_name: saveName,
    manager_name: managerName,
    nation_id: selectedNationId,
  };

  try {
    window.api.runSaveScript(payload); // still triggers Python script
    const newSavePath = `saves/${saveName}.db`;
    window.api.loadSave(newSavePath);  // set the new DB as active
    setStatus("Save script launched.");
    setSaveReady(true);
  } catch (err) {
    console.error("Error starting save:", err);
    setStatus("Failed to start game.");
  }
};

  const handleLoadSave = (savePath) => {
    window.api.loadSave(savePath);
    onLaunchGame();
  };

  const handleLoadMostRecent = () => {
    if (availableSaves.length === 0) return;
    const sorted = [...availableSaves].sort((a, b) => b.modified - a.modified);
    handleLoadSave(sorted[0].path);
  };

  return (
    <div className="screen">
      <h2>Start New Game</h2>

      <div>
        <label>Save Name:</label>
        <input
          type="text"
          value={saveName}
          onChange={(e) => setSaveName(e.target.value)}
          placeholder="e.g. My Career"
        />
      </div>

      <div>
        <label>Manager Name:</label>
        <input
          type="text"
          value={managerName}
          onChange={(e) => setManagerName(e.target.value)}
          placeholder="e.g. Alex Ferguson"
        />
      </div>

      <div>
        <label>Nation:</label>
        <select onChange={(e) => setSelectedNationId(Number(e.target.value))}>
          <option value="">-- Select Nation --</option>
          {nations.map((nation) => (
            <option key={nation.nation_team_id} value={nation.nation_team_id}>
              {nation.team_name}
            </option>
          ))}
        </select>
      </div>

      <button
        onClick={() => {
          if (saveReady) {
            onLaunchGame();
          } else {
            handleStart();
          }
        }}
      >
        {saveReady ? "Confirm and Enter Game" : "Start Career"}
      </button>

      <p>{status}</p>

      <hr />

      <h3>Continue Game</h3>
      <button onClick={handleLoadMostRecent}>Load Most Recent Save</button>

      <div>
        <label>All Saves:</label>
        <select onChange={(e) => handleLoadSave(e.target.value)}>
          <option value="">-- Select Save File --</option>
          {availableSaves.map((save) => (
            <option key={save.path} value={save.path}>
              {save.name} ({new Date(save.modified).toLocaleString()})
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
