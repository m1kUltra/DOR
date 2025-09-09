// File: Match/Ball.jsx
export default function Ball({ ball, toPixels, pxPerMeter }) {
  const radiusM = 1;
  const { left, top } = toPixels({ x: ball.location[0], y: ball.location[1] });
 
 const z = ball.location[2] ?? 0;
  const scale = z > 1 ? z : 1;
  const baseWidth = radiusM * 2 * (1+pxPerMeter/2);
  const baseHeight = radiusM * 1.5 * (1+pxPerMeter/2);
  const width = baseWidth * scale;
  const height = baseHeight * scale;
  const zIndex = 2 + Math.round(z);

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
