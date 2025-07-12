// src/components/Sidebar.jsx
import React, { useEffect, useState } from "react";
import "./Sidebar.css";

export default function Sidebar({ onNavigate }) {
  const [managerName, setManagerName] = useState("");
  const [teamName, setTeamName] = useState("");

  useEffect(() => {
    window.api.getManagerInfo?.().then((info) => {
      if (info) {
        setManagerName(info.managerName || "");
        setTeamName(info.teamName || "");
      }
    });
  }, []);

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        {managerName && <div className="manager">Manager: {managerName}</div>}
        {teamName && <div className="team">Team: {teamName}</div>}
      </div>

      <button onClick={() => onNavigate("dashboard")}>🏠 Dashboard</button>
      <button onClick={() => onNavigate("squad")}>👥 Squad</button>
      <button onClick={() => onNavigate("fixtures")}>📅 Fixtures</button>
      <button onClick={() => onNavigate("match")}>🎮 Match</button>
      <button onClick={() => onNavigate("tactics")}>🧠 Tactics</button>
      <button onClick={() => onNavigate("transfers")}>🧲 Recruitment</button>
      <button onClick={() => onNavigate("editor")}>📂 DB Editor</button>
    </div>
  );
}
