// src/components/TopBar.jsx
import React from "react";
import "./TopBar.css";

export default function TopBar() {
  return (
    <div className="topbar">
      <input
        className="search-bar"
        placeholder="Search players, clubs..."
        type="text"
      />
      <button className="advance-btn">Advance ⏭️</button>
    </div>
  );
}
