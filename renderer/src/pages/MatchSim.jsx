import React, { useEffect, useState } from "react";
import MatchRenderer from "../components/Match/MatchRenderer";
import MatchLog from "../components/Match/Matchlog";
import Scoreboard from "../components/Match/Scoreboard";
import "./MatchSim.css";

export default function MatchSim() {
  const [players, setPlayers] = useState([]);
  const [ball, setBall] = useState(null);
  const [score, setScore] = useState({ a: 0, b: 0 });
  const [matchLog, setMatchLog] = useState("🟢 Click Play to start the match...");

  // ✅ VALID
  useEffect(() => {
    console.log("🟢 Listening for match ticks...");
    window.api.onMatchTick((data) => {
      console.log("✅ Match tick received:", data);
      setPlayers(data.players || []);
      setBall(data.ball || null);
      setMatchLog((prev) => `[TICK ${data.tick}] ${data.state}\n${prev}`);
    });
  }, []);

  const runMatch = async () => {
    setMatchLog("🟢 Running match engine...");
    try {
      const output = await window.api.runPython("matchEngine/match.py");
      console.log("🏁 Match engine complete:", output);
    } catch (error) {
      setMatchLog(`❌ Error: ${error.message}`);
    }
  };

  return (
    <div className="match-sim-screen">
      <Scoreboard score={score} onPlay={runMatch} />
      <div className="field-wrapper">
        <MatchRenderer players={players} ball={ball} />
      </div>
      <MatchLog log={matchLog} />
    </div>
  );
}
