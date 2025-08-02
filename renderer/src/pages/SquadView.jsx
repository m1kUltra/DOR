import React, { useEffect, useState } from "react";
import { DndContext, useDraggable, useDroppable } from "@dnd-kit/core";
import useSelectionStore from "../store/selectionStore";
import "./SquadView.css";

export default function SquadView({ onSelectPlayer }) {
  const { selection, setSelection, movePlayer } = useSelectionStore();
  const [selectedPlayerId, setSelectedPlayerId] = useState(null);

  useEffect(() => {
    const loadSquad = async () => {
      const data = await window.api.getFullSquad?.();
      setSelection(data);
    };
    loadSquad();
  }, [setSelection]);

  const findPlayerGroup = (playerId) => {
    for (const group of ["starters", "subs", "res", "nis"]) {
      const index = selection[group].findIndex((p) => p?.player_id === playerId);
      if (index !== -1) return { group, index };
    }
    return {};
  };
  


  const handleClick = (playerId, group, index) => {
    if (selectedPlayerId === null) {
      setSelectedPlayerId(playerId);
    } else if (selectedPlayerId === playerId) {
      setSelectedPlayerId(null);
    } else {
      moveSelectedPlayerTo(group, index);
    }
  };

  const moveSelectedPlayerTo = (targetGroup, targetIndex) => {
    const { group: fromGroup } = findPlayerGroup(selectedPlayerId);
    if (!fromGroup) return;
    movePlayer(selectedPlayerId, fromGroup, targetGroup, targetIndex);
    setSelectedPlayerId(null);
  };

  const handleDoubleClick = (playerId) => {
    const { group: fromGroup } = findPlayerGroup(playerId);
    if (!fromGroup || fromGroup === "nis") return;
    // append to NIS
    movePlayer(playerId, fromGroup, "nis", selection.nis.length);
    setSelectedPlayerId(null);
  };

  const handleDragEnd = (event) => {
    const { active, over } = event;
    if (!over) return;
    const draggedId = active.id;
    const overData = over.data.current;
    if (!overData || !overData.group) return;
    const { group: fromGroup } = findPlayerGroup(draggedId);
    if (!fromGroup) return;
    movePlayer(draggedId, fromGroup, overData.group, overData.index);
  };

  const renderBox = (player, group, index) => {
  const isSelected = player?.player_id === selectedPlayerId;
  const squadNumber =
    group === "starters" ? index + 1 :
    group === "subs" ? index + 16 :
    "";

  const id = player?.player_id || `${group}-${index}`;
  return (
    <DroppableSlot key={id} id={id} group={group} index={index}>
      {player ? (
        <DraggablePlayer
          player={player}
          squadNumber={squadNumber}
          group={group} // ✅ added
          isSelected={isSelected}
          onClick={() => handleClick(player.player_id, group, index)}
          onDoubleClick={() => handleDoubleClick(player.player_id)}
          onSelectPlayer={onSelectPlayer} //
        />
      ) : (
        <div className="player-tile empty">(empty)</div>
      )}
    </DroppableSlot>
  );
};


  const renderColumn = (label, group, size = null, fixed = false, minSlots = 0) => {
    const players = selection[group];
    let boxes = [];

    if (fixed) {
      boxes = Array.from({ length: size }, (_, i) => players[i] || null);
    } else {
      boxes = Array.from(
        { length: Math.max(players.length, minSlots) },
        (_, i) => players[i] || null
      );
    }

    // 👉 Add the substitutes class if group === "subs"
    const extraClass = group === "subs" ? " substitutes" : "";

    return (
      <div className={`squad-column${extraClass}`} key={group}>
        <h3>{label}</h3>
        {boxes.map((p, i) => renderBox(p, group, i))}
      </div>
    );
  };

  return (
    <div className="squad-view-wrapper">
      <DndContext onDragEnd={handleDragEnd}>
        <div className="squad-scroll-container">
          <div className="squad-view-grid">
            {renderColumn("Starters", "starters", 15, true)}
            <div className="squad-column-group">
              {renderColumn("Substitutes", "subs", 8, true)}
              {renderColumn("Reserves", "res", null, false, 6)}
            </div>
            {renderColumn("Not In Squad", "nis", null, false, 6)}
          </div>
        </div>
      </DndContext>
      <div className="tactics-panel">
        <h4>Tactics View</h4>
        <p>(Coming Soon)</p>
      </div>
    </div>
  );
}

function DroppableSlot({ id, group, index, children }) {
  const { setNodeRef, isOver } = useDroppable({
    id,
    data: { group, index },
  });

  return (
    <div ref={setNodeRef} className={`slot-wrapper${isOver ? " over" : ""}`}>
      {children}
    </div>
  );
}



function DraggablePlayer({ player, squadNumber, group, isSelected, onClick, onDoubleClick, onSelectPlayer }) {

  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useDraggable({ id: player.player_id });

  const style = {
    transform: transform ? `translate3d(${transform.x}px, ${transform.y}px, 0)` : undefined,
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  // ✅ Override the displayed number for reserves/nis
  let displayNumber = squadNumber;
  if (group === "res" || group === "nis") {
    displayNumber = "R";
  }

  // ✅ Compute abilityDisplay
  let abilityDisplay = "-";
  if (player.current_ability !== undefined && player.current_ability !== null) {
    const parts = String(player.current_ability).split(".");
    abilityDisplay = parts[0];
  }

  // ✅ Map of valid codes
  const positionMap = {
    1: ["lp"], 2: ["hk"], 3: ["tp"],
    4: ["sr"], 5: ["sr"], 6: ["br"],
    7: ["br"], 8: ["br"], 9: ["sh"],
    10: ["fh"], 11: ["wg"], 12: ["ct"],
    13: ["ct"], 14: ["wg"], 15: ["fb"],
    16: ["hk"], 17: ["lp"], 18: ["tp"],
  };

  const displayName = player.firstname
    ? `${player.firstname} ${player.surname}`
    : player.name ?? "";

  // ✅ Build posCodes array
  let posCodes = [];
  if (typeof player.position === "string") {
    posCodes = player.position
      .split(",")
      .map(e => e.trim())
      .filter(e => {
        const [code, val] = e.split(":");
        return parseInt(val, 10) > 3;
      })
      .map(e => e.split(":")[0]);
  }

  // ✅ Highlight logic
  let highlightClass = "";
  if (squadNumber && squadNumber >= 1 && squadNumber <= 18) {
    const allowedCodes = positionMap[squadNumber] || [];
    let matchedValue = 0;

    if (typeof player.position === "string" && player.position.includes(":")) {
      player.position.split(",").forEach(entry => {
        const [rawCode, rawVal] = entry.split(":");
        const code = rawCode.trim();
        const val = parseInt(rawVal, 10);

        if (allowedCodes.includes(code) && !isNaN(val) && val > matchedValue) {
          matchedValue = val;
        }
      });
    }

    if (matchedValue === 5) {
      highlightClass = "";
    } else if (matchedValue === 4) {
      highlightClass = "highlight-green";
    } else if (matchedValue === 3) {
      highlightClass = "highlight-yellow";
    } else if (matchedValue === 2) {
      highlightClass = "highlight-orange";
    } else {
      highlightClass = "highlight-red";
    }
  }

  const tileClass = `player-tile${isSelected ? " selected" : ""} ${highlightClass}`;

  return (
    <div
      ref={setNodeRef}
      {...attributes}
      style={style}
      className={tileClass}
      onClick={onClick}
      onDoubleClick={onDoubleClick}
    >
      <div className="player-header">
        {displayNumber && (
          <div className="squad-number" {...listeners}>
            {displayNumber}
          </div>
        )}

        <span
          className="player-name"
          onClick={(e) => {
            e.stopPropagation();
            e.preventDefault();
            onSelectPlayer(player.player_id); // passed from GameShell
          }}
          onMouseDown={(e) => e.stopPropagation()}
        >
          {displayName}
        </span>

        {posCodes.length > 0 && (
          <span className="player-position">{posCodes.join(", ")}</span>
        )}

        <span className="player-ability">{abilityDisplay}</span>
      </div>
    </div>
  );
}
