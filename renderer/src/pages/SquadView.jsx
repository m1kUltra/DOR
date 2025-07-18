import React, { useEffect, useState } from "react";
import { DndContext, useDraggable, useDroppable } from "@dnd-kit/core";
import useSelectionStore from "../store/selectionStore";
import "./SquadView.css";

export default function SquadView() {
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
            isSelected={isSelected}
            onClick={() => handleClick(player.player_id, group, index)}
            onDoubleClick={() => handleDoubleClick(player.player_id)}
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

function DraggablePlayer({ player, squadNumber, isSelected, onClick, onDoubleClick }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useDraggable({ id: player.player_id });

  const style = {
    transform: transform ? `translate3d(${transform.x}px, ${transform.y}px, 0)` : undefined,
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div
      ref={setNodeRef}
      {...attributes}
      {...listeners}
      style={style}
      className={`player-tile${isSelected ? " selected" : ""}`}
      onClick={onClick}
      onDoubleClick={onDoubleClick}
    >
      <div className="player-header">
        {squadNumber && <span className="squad-number">{squadNumber}</span>}
        <span className="player-name">{player.name}</span>
        <span className="player-ability">{player.current_ability ?? "-"}</span>
      </div>
    </div>
  );
}
