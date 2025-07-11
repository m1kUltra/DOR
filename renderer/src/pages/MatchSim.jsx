// src/pages/MatchSim.jsx
import React, { useState } from "react";
import "./MatchSim.css";

export default function MatchSim() {
  const [matchLog, setMatchLog] = useState("🟢 Click Play to start the match...");

  const runMatch = async () => {
    setMatchLog("🟢 Running match engine...");
    try {
      const output = await window.api.runPython("match_engine.py");
      setMatchLog(`🏁 Match Engine Output:\n\n${output}`);
    } catch (error) {
      setMatchLog(`❌ Error: ${error.message}`);
      console.error("Error running match simulation:", error);
    }
  };

  return (
    <div className="screen">
      <h2>🏉 Match Simulation</h2>
      <button onClick={runMatch}>▶️ Play Match</button>
      <pre className="match-log">{matchLog}</pre>
    </div>
  );
}
