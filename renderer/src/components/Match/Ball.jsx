export default function Ball({ ball }) {
  return (
    <div
      className="ball"
      style={{
        left: `${ball.location[0]}%`,
        top: `${ball.location[1]}%`,
      }}
    />
  );
}
