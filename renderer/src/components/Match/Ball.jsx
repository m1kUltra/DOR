// File: Match/Ball.jsx
export default function Ball({ ball, toPixels, pxPerMeter }) {
  const radiusM = 0.5;
  const { left, top } = toPixels({ x: ball.location[0], y: ball.location[1] });
  const width = radiusM * 2 * pxPerMeter;
  const height = radiusM * 1.5 * pxPerMeter;

  return (
    <div
      className="ball"
      style={{
        position: "absolute",
        width,
        height,
        left: left - width / 2,
        top: top - height / 2,
        backgroundColor: "black",
        borderRadius: "50%",
        zIndex: 2,
      }}
    />
  );
}
