import React, { useEffect, useState } from "react";
import "./PlayerDetails.css";

export default function PlayerDetails({ playerId, onBack }) {
  const [player, setPlayer] = useState(null);

  useEffect(() => {
    const load = async () => {
      const data = await window.api.getPlayerById(playerId);
      if (data && typeof data.attributes === "string") {
        try {
          data.attributes = JSON.parse(data.attributes);
        } catch (e) {
          console.error("Failed to parse attributes JSON", e);
        }
      }
      setPlayer(data);
    };
    load();
  }, [playerId]);

  if (!player) {
    return <div className="player-details">Loading...</div>;
  }

  const {
    firstname,
    surname,
    dob,
    height,
    weight,
    current_ability,
    personality,
    traits,
    attributes = {}
  } = player;

  // Group attributes into sections
  const technicalKeys = [
  
    "darts",
    "finishing",
    "footwork",
    "goal_kicking",
    "handling",
    "kicking",
    "kicking_power",
    "lineouts",
    "marking",
    "offloading",
    "passing",
    "scrummaging",
    "rucking",
    "technique",
  
  ];
  const mentalKeys = [
    "aggression","anticipation","bravery","composure","concentration",
    "decisions","determination","flair","leadership","off_the_ball",
    "positioning","teamwork","vision","work_rate"
  ];
  const physicalKeys = [
    "acceleration","agility","balance","jumping_reach",
    "natural_fitness","pace","stamina","strength"
  ];

  const renderAttributes = (keys) =>
    keys.map((key) => (
      <div className="attr-row" key={key}>
        <span className="attr-name">{key.replace(/_/g, " ")}</span>
        <span className="attr-value">{attributes[key] ?? "-"}</span>
      </div>
    ));

  return (
    <div className="player-details">
      <button className="back-btn" onClick={onBack}>⬅ Back</button>

      <h1 className="player-name">
        {firstname} {surname}
      </h1>

      <div className="player-info">
        <p><strong>DOB:</strong> {dob}</p>
        <p><strong>Height:</strong> {height} cm</p>
        <p><strong>Weight:</strong> {weight} kg</p>
        <p><strong>Current Ability:</strong> {current_ability}</p>
        <p><strong>Personality:</strong> {personality}</p>
        <p><strong>Traits:</strong> {traits}</p>
      </div>

      <div className="attributes-grid">
        <div className="attributes-section">
          <h3>Technical</h3>
          {renderAttributes(technicalKeys)}
        </div>
        <div className="attributes-section">
          <h3>Mental</h3>
          {renderAttributes(mentalKeys)}
        </div>
        <div className="attributes-section">
          <h3>Physical</h3>
          {renderAttributes(physicalKeys)}
        </div>
      </div>
    </div>
  );
}
