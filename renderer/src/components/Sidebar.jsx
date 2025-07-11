// src/components/Sidebar.jsx
import React from "react";
import "./Sidebar.css";

export default function Sidebar({ onNavigate }) {
  return (
    <div className="sidebar">
     
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
