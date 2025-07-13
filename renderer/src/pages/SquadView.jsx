import React, { useEffect } from "react";
import useSelectionStore from "../store/selectionStore";

export default function SquadView() {
  const { selection, setSelection, movePlayer, updatePosition } = useSelectionStore();

  useEffect(() => {
    const loadSquad = async () => {
      const data = await window.api.getFullSquad?.();
      setSelection(data);
    };
    loadSquad();
  }, []);

  const handleMove = (playerId, from, to) => {
    movePlayer(playerId, from, to);
  };

  const handlePositionChange = (playerId, pos) => {
    const parsed = parseInt(pos);
    if (!isNaN(parsed)) updatePosition(playerId, parsed);
  };

  const renderList = (label, key) => (
    <div style={{ flex: 1, minWidth: "300px" }}>
      <h3>{label}</h3>
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Ability</th>
            <th>Pos</th>
            <th>Move</th>
          </tr>
        </thead>
        <tbody>
          {selection[key]?.map((player) => (
            <tr key={player.player_id}>
              <td>{player.name || `#${player.player_id}`}</td>
              <td>{player.current_ability ?? "-"}</td>
              <td>
                <input
                  type="number"
                  value={player.position}
                  onChange={(e) => handlePositionChange(player.player_id, e.target.value)}
                  style={{ width: "3em" }}
                />
              </td>
              <td>
                {["starters", "subs", "res", "nis"]
                  .filter((k) => k !== key)
                  .map((k) => (
                    <button
                      key={k}
                      onClick={() => handleMove(player.player_id, key, k)}
                      style={{ marginRight: "4px" }}
                    >
                      ➡ {k}
                    </button>
                  ))}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );

  return (
    <div className="screen">
      <h2>Squad View</h2>
      <div style={{ display: "flex", flexWrap: "wrap", gap: "2rem" }}>
        {renderList("Starters", "starters")}
        {renderList("Substitutes", "subs")}
        {renderList("Reserves", "res")}
        {renderList("Not In Squad", "nis")}
      </div>
    </div>
  );
}
