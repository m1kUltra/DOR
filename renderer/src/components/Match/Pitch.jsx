import Player from "./Player";
import Ball from "./Ball";
import pitchImage from "../../assets/pitch.png";

export default function Pitch({ players, ball }) {
  return (
    <div className="pitch-canvas">
      <img src={pitchImage} alt="Pitch" className="pitch-background" />
      {players.map((p) => (
        <Player key={`${p.sn}-${p.team_code}`} player={p} />
      ))}
      {ball && <Ball ball={ball} />}
    </div>
  );
}
