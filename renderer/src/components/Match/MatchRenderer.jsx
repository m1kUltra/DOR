// File: renderer/src/components/MatchRenderer.jsx
import React, { useRef, useEffect, useState } from "react";
import Player from "./Player";
import Ball from "./Ball";
import pitchImage from "../../assets/pitch.png";

const FIELD_METERS = { width: 136, height: 76 }; // Deadball + padding included
const FIELD_OFFSET = { x: 18, y: 3 };            // Origin shift

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
    <div
      ref={containerRef}
      className="pitch-canvas"
      style={{ position: "relative", width: "100%", height: "100%" }}
    >
      <img
        src={pitchImage}
        alt="Rugby Pitch"
        className="pitch-background"
        style={{ width: "100%", height: "100%", objectFit: "cover", position: "absolute" }}
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
