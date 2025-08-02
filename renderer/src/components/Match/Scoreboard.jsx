export default function Scoreboard({ score, onPlay }) {
  return (
    <div className="scoreboard">
      <h2>🏉 Match Simulation</h2>
      <button onClick={onPlay}>▶️ Play Match</button>
      <div>Score: 🟥 Team A - {score.a} | 🟦 Team B - {score.b}</div>
    </div>
  );
}
