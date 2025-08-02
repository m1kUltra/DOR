import React, { useEffect, useState } from "react";
import "./MatchSim.css";
import Pitch from "../components/Match/Pitch";
import Scoreboard from "../components/Match/Scoreboard";
import MatchLog from "../components/Match/Matchlog";

import pitchImage from "../assets/pitch.png";

export default function MatchSim() {
  const [players, setPlayers] = useState([]);
  const [ball, setBall] = useState(null);
  const [score, setScore] = useState({ a: 0, b: 0 });
  const [matchLog, setMatchLog] = useState("🟢 Click Play to start the match...");

  useEffect(() => {
    window.api.onMatchTick((data) => {
      setPlayers(data.players || []);
      setBall(data.ball || null);
      setMatchLog((prev) => `[TICK ${data.tick}] ${data.state}\n${prev}`);
    });
  }, []);

  const runMatch = async () => {
    setMatchLog("🟢 Running match engine...");
    try {
      const output = await window.api.runPython("matchEngine/match.py");
      console.log("Match engine complete:", output);
    } catch (error) {
      setMatchLog(`❌ Error: ${error.message}`);
    }
  };

  const teamA = players.filter((p) => p.team_code === "a");
  const teamB = players.filter((p) => p.team_code === "b");

  return (
    <div className="match-sim-screen">
      <div className="scoreboard">
        <h2>🏉 Match Simulation</h2>
        <button className="play-button" onClick={runMatch}>▶️ Play Match</button>
        <div className="score-text">Score: 🟥 Team A - {score.a} | 🟦 Team B - {score.b}</div>
      </div>

      <div className="field-wrapper">
        <div className="team-column">
          {teamA.map((p) => (
            <div key={p.sn}>{p.sn}. {p.name}</div>
          ))}
        </div>

        <div className="pitch-canvas">
  <img src={pitchImage} alt="Rugby Pitch" className="pitch-background" />
  {players.map((p) => (
    <div
      key={p.sn + p.team_code}
      className={`player player-${p.team_code}`}
      style={{
        left: `${p.location[0]}%`,
        top: `${p.location[1]}%`,
      }}
    >
      {p.sn}
    </div>
  ))}
  {ball && (
    <div
      className="ball"
      style={{
        left: `${ball.location[0]}%`,
        top: `${ball.location[1]}%`,
      }}
    />
  )}
</div>

        <div className="team-column">
          {teamB.map((p) => (
            <div key={p.sn}>{p.sn}. {p.name}</div>
          ))}
        </div>
      </div>

      <pre className="match-log">{matchLog}</pre>
    </div>
  );
}
