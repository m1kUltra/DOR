// File: Match/Player.jsx
export default function Player({ player, toPixels, pxPerMeter }) {
  const radiusM = 0.75;
  const { left, top } = toPixels({ x: player.location[0], y: player.location[1] });
  const diameter = radiusM * 2 * pxPerMeter;

  return (
    <div
      className={`player player-${player.team_code}`}
      style={{
        position: "absolute",
        width: diameter,
        height: diameter,
        left: left - diameter / 2,
        top: top - diameter / 2,
        backgroundColor: player.team_code === "a" ? "red" : "blue",
        borderRadius: "50%",
        textAlign: "center",
        lineHeight: `${diameter}px`,
        fontSize: "0.75rem",
        color: "white",
      }}
    >
      {player.sn}
    </div>
  );
}
