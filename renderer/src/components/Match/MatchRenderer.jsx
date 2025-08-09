// File: MatchRenderer.jsx
import React, { useRef, useEffect, useState } from "react";
import Player from "./Player";
import Ball from "./Ball";
import pitchImage from "../../assets/pitch.png";
import "./MatchRenderer.css";

const FIELD_METERS = { width: 136, height: 76 }; // Total field incl. padding
const FIELD_OFFSET = { x: 18, y: 3 };            // Origin shift to match true (0,0)

export default function MatchRenderer({ players, ball }) {
  const containerRef = useRef();
  const [dimensions, setDimensions] = useState({ width: 1, height: 1 });

  useEffect(() => {
    const updateSize = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.offsetWidth,
          height: containerRef.current.offsetHeight,
        });
      }
    };
    updateSize();
    window.addEventListener("resize", updateSize);
    return () => window.removeEventListener("resize", updateSize);
  }, []);

  const pxPerMeterX = dimensions.width / FIELD_METERS.width;
  const pxPerMeterY = dimensions.height / FIELD_METERS.height;

  const toPixels = ({ x, y }) => {
    const pxX = (x + FIELD_OFFSET.x) * pxPerMeterX;
    const pxY = (FIELD_METERS.height - (y + FIELD_OFFSET.y)) * pxPerMeterY;
    return { left: pxX, top: pxY };
  };

  return (
    <div ref={containerRef} className="pitch-canvas">
      <img src={pitchImage} alt="Rugby Pitch" className="pitch-background" />
          {/* ✅ TEST HARDCODED PLAYER — REMOVE THIS AFTER DEBUGGING */}
    <Player
      player={{
        sn: 99,
        name: "Debug Player",
        team_code: "a",
        action: "press",
        location: [50, 35, 0],  // mid-pitch
      }}
      toPixels={toPixels}
      pxPerMeter={pxPerMeterX}
    />

      {players.map((p) => (
        <Player
          key={`${p.sn}-${p.team_code}`}
          player={p}
          toPixels={toPixels}
          pxPerMeter={pxPerMeterX}
        />
      ))}
      {ball && <Ball ball={ball} toPixels={toPixels} pxPerMeter={pxPerMeterX} />}
    </div>
  );
}
