// src/components/TopBar.jsx
import React from "react";
import "./TopBar.css";


export default function TopBar({ onSave }) {
  return (
    <div className="topbar">
      <input
        className="search-bar"
        placeholder="Search players, clubs..."
        type="text"
      />
      <button className="advance-btn">Advance ⏭️</button>
      <button className="save-btn" onClick={onSave}>💾 Save</button>
    </div>
  );
}
