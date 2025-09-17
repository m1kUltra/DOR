import argparse
import contextlib
import json
import collections
import sys
from pathlib import Path

# The match engine expects its own root directory on sys.path so that
# imports like ``utils.core.logger`` resolve correctly.
ENGINE_ROOT = Path(__file__).resolve().parent / "engine" / "matchEngine"
sys.path.append(str(ENGINE_ROOT))

from match import Match


def run_match(db_path: str, team_a: int, team_b: int, ticks: int, log_file: Path) -> None:
    """Run the match engine in headless mode and log each tick to ``log_file``.

    The Match class already emits a JSON blob per tick to stdout via
    ``dump_tick_json``. We redirect stdout to ``log_file`` so the entire match
    can be analysed later.
    """
    log_file = Path(log_file)
    with log_file.open("w", encoding="utf-8") as fh, contextlib.redirect_stdout(fh):
        match = Match(db_path, team_a_id=team_a, team_b_id=team_b)
        match.run(ticks=ticks, realtime=False)


def analyse_ticks(log_file: Path):
    """Parse the tick log and produce final score, state timeline, and player action counts."""
    actions = collections.defaultdict(collections.Counter)
    timeline = []
    prev_state = None
    last_tick = None

    with Path(log_file).open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or not line.startswith("{"):
                continue
            tick = json.loads(line)
            last_tick = tick

            state = tick.get("state")
            if state != prev_state:
                timeline.append((tick["time"], state))
                prev_state = state

            for p in tick.get("players", []):
                act = p.get("action")
                if act and act != "move":
                    actions[p["name"]][act] += 1

    final_score = last_tick["score"] if last_tick else None
    return final_score, timeline, actions


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a match headlessly and summarise stats")
    parser.add_argument("--db", default="tmp/temp.db", help="Path to database used for match setup")
    parser.add_argument("--team-a", type=int, default=2, dest="team_a", help="Team A ID")
    parser.add_argument("--team-b", type=int, default=1, dest="team_b", help="Team B ID")
    parser.add_argument("--ticks", type=int, default=6000, help="Number of ticks to simulate")
    parser.add_argument("--log", default="ticks.jsonl", help="File to write tick JSON data")
    args = parser.parse_args()

    run_match(args.db, args.team_a, args.team_b, args.ticks, args.log)
    score, timeline, actions = analyse_ticks(args.log)

    print("Scoreboard:", score)
    print("State timeline:")
    for t, state in timeline:
        print(f"  {t:.2f}s -> {state}")
    print("Player actions:")
    for player, counts in actions.items():
        print(f"  {player}:")
        for action, count in counts.items():
            print(f"    {action}: {count}")


if __name__ == "__main__":
    main()