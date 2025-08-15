// File: renderer/src/components/Match/Player.jsx
import React from "react";

function polarToCartesian(cx, cy, r, angleDeg) {
  // World: 0° = +x (right), 90° = +y (up). Screen y is downward, so use -sin.
  const rad = (Math.PI / 180) * angleDeg;
  return {
    x: cx + r * Math.cos(rad),
    y: cy - r * Math.sin(rad),
  };
}

function arcPath(cx, cy, r, startDeg, endDeg) {
  const start = polarToCartesian(cx, cy, r, startDeg);
  const end = polarToCartesian(cx, cy, r, endDeg);
  const largeArcFlag = Math.abs(endDeg - startDeg) > 180 ? 1 : 0;
  const sweepFlag = 1; // draw in the positive-angle (clockwise on screen) direction
  return `M ${start.x} ${start.y} A ${r} ${r} 0 ${largeArcFlag} ${sweepFlag} ${end.x} ${end.y}`;
}

export default function Player({ player, toPixels, pxPerMeter }) {
  const radiusM = 1; // visual radius in meters
  const { left, top } = toPixels({ x: player.location[0], y: player.location[1] });
  const diameter = radiusM * 2 * pxPerMeter;
  const r = diameter / 2;

  // Orientation in degrees; accept both `orientation` and `orientation_deg`
  const facing =
    ((player.orientation ?? player.orientation_deg ?? 90) % 360 + 360) % 360;

  const segLen = 24;  // arc length in degrees for each tiny mark
  const offset = 30;  // ± degrees from facing
  const ringStroke = Math.max(2, Math.round(diameter * 0.08)); // arc thickness
  const ringR = r - ringStroke / 2; // sit arcs just inside the edge

  const a1Start = facing - offset - segLen / 2;
  const a1End   = facing - offset + segLen / 2;
  const a2Start = facing + offset - segLen / 2;
  const a2End   = facing + offset + segLen / 2;

  const fillColor = player.team_code === "a" ? "#d62828" : "#003f88";
  const textSize = Math.max(10, Math.round(diameter * 0.38));

  return (
    <div
      className={`player player-${player.team_code}`}
      style={{
        position: "absolute",
        width: diameter,
        height: diameter,
        left: left - r,
        top: top - r,
        zIndex: 1,
        pointerEvents: "none",
        // no background here; we draw with SVG
      }}
    >
      <svg
        width={diameter}
        height={diameter}
        viewBox={`0 0 ${diameter} ${diameter}`}
        style={{ display: "block" }}
      >
        {/* Base circle */}
        <circle cx={r} cy={r} r={r} fill={fillColor} />

        {/* Two tiny arc “semi-circles” at facing ± 30° */}
        <path
          d={arcPath(r, r, ringR, a1Start, a1End)}
          stroke="#fff"
          strokeWidth={ringStroke}
          strokeLinecap="round"
          fill="none"
        />
        <path
          d={arcPath(r, r, ringR, a2Start, a2End)}
          stroke="#fff"
          strokeWidth={ringStroke}
          strokeLinecap="round"
          fill="none"
        />

        {/* Squad number */}
        <text
          x={r}
          y={r}
          textAnchor="middle"
          dominantBaseline="central"
          fill="#fff"
          fontWeight="700"
          fontSize={textSize}
          style={{ userSelect: "none" }}
        >
          {player.sn}
        </text>
      </svg>
    </div>
  );
}
