// src/components/Match/TeamColumn.jsx

import React from "react";

export default function TeamColumn({ team }) {
  return (
    <div className="team-column">
      {team.map((p) => (
        <div key={`${p.sn}-${p.name}`}>{p.sn}. {p.name}</div>
      ))}
    </div>
  );
}
