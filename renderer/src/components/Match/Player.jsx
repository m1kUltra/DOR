export default function Player({ player }) {
  const { location, team_code, sn } = player;
  return (
    <div
      className={`player player-${team_code}`}
      style={{
        left: `${location[0]}%`,
        top: `${location[1]}%`,
      }}
    >
      {sn}
    </div>
  );
}
