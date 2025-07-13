// src/components/TopBar.jsx
import React from "react";
import useSelectionStore from "../store/selectionStore";
import "./TopBar.css";

export default function TopBar({ onSave }) {
  const { selection } = useSelectionStore();

  const handleAdvance = () => {
    const cleanGroup = (group) =>
      group.map((p) => ({
        player_id: p.player_id,
        position: p.position,
      }));

    const payload = {
      starters: cleanGroup(selection.starters),
      subs: cleanGroup(selection.subs),
      res: cleanGroup(selection.res),
      nis: cleanGroup(selection.nis),
    };

    window.api.saveSelection(payload);
    console.log("✅ Selection saved via Advance");

    // Optional: window.api.advance();
  };

  return (
    <div className="topbar">
      <input
        className="search-bar"
        placeholder="Search players, clubs..."
        type="text"
      />
      <button className="advance-btn" onClick={handleAdvance}>
        Advance ⏭️
      </button>
      <button className="save-btn" onClick={onSave}>
        💾 Save
      </button>
    </div>
  );
}
