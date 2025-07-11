import React, { useState, useEffect } from "react";
import fs from "fs";
import path from "path";

export default function NewGame() {
  const [clubs, setClubs] = useState([]);
  const [nations, setNations] = useState([]);
  const [selectedClubId, setSelectedClubId] = useState(null);
  const [selectedNationId, setSelectedNationId] = useState(null);
  const [saveName, setSaveName] = useState("");
  const [status, setStatus] = useState("");

  useEffect(() => {
    window.api.getTableData("clubs").then(setClubs);
    window.api.getTableData("nations").then(setNations);
  }, []);

  const handleStart = () => {
    if (!saveName) return setStatus("⚠️ Enter a save name.");
    if (!selectedClubId && !selectedNationId) return setStatus("⚠️ Select a team.");

    const payload = {
      save_name: saveName,
      manager_name: "Mr Manage",
      club_id: selectedClubId || null,
      nation_id: selectedNationId || null,
    };

    const filePath = path.join("tmp", "new_save.json");

    try {
      fs.writeFileSync(filePath, JSON.stringify(payload, null, 2));
      window.api.runSaveScript();
      setStatus("✅ Save script launched.");
    } catch (err) {
      console.error("Error saving JSON or triggering script:", err);
      setStatus("❌ Failed to start game.");
    }
  };

  return (
    <div className="screen">
      <h2>🎮 Start New Game</h2>

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
        <label>Club:</label>
        <select onChange={(e) => setSelectedClubId(Number(e.target.value))}>
          <option value="">-- Select Club --</option>
          {clubs.map((club) => (
            <option key={club.club_id} value={club.club_id}>
              {club.name}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label>Nation:</label>
        <select onChange={(e) => setSelectedNationId(Number(e.target.value))}>
          <option value="">-- Select Nation --</option>
          {nations.map((nation) => (
            <option key={nation.nation_id} value={nation.nation_id}>
              {nation.name}
            </option>
          ))}
        </select>
      </div>

      <button onClick={handleStart}>🟢 Start Career</button>
      <p>{status}</p>
    </div>
  );
}
