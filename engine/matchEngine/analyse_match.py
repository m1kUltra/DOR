import argparse
import collections
import contextlib
import csv
import json
import sys
from pathlib import Path

# The match engine expects its own root directory on sys.path so that
# imports like ``utils.core.logger`` resolve correctly.
ENGINE_ROOT = Path(__file__).resolve().parent / "engine" / "matchEngine"
sys.path.append(str(ENGINE_ROOT))

from match import Match
from utils.core import logger as match_logger


@contextlib.contextmanager
def _patch_player_actions():
    """Temporarily expose ``player.current_action`` via the logger output."""

    original_serialize = match_logger.serialize_tick

    def patched_serialize(match):
        blob = original_serialize(match)
        players = getattr(match, "players", [])
        players_by_code = {
            f"{getattr(p, 'sn', '?')}{getattr(p, 'team_code', '')}": p for p in players
        }
        for entry in blob.get("players", []):
            sn = entry.get("sn")
            team_code = entry.get("team_code")
            if sn is None or team_code is None:
                continue
            code = f"{sn}{team_code}"
            player = players_by_code.get(code)
            if player is None:
                continue
            action = getattr(player, "current_action", None)
            if action is None:
                action = getattr(player, "action", None)
            entry["action"] = action
        return blob

    match_logger.serialize_tick = patched_serialize
    try:
        yield
    finally:
        match_logger.serialize_tick = original_serialize


def run_match(db_path: str, team_a: int, team_b: int, ticks: int, log_file: Path) -> None:
    """Run the match engine in headless mode and log each tick to ``log_file``.

    The Match class already emits a JSON blob per tick to stdout via
    ``dump_tick_json``. We redirect stdout to ``log_file`` so the entire match
    can be analysed later.
    """
    log_file = Path(log_file)
    with (
        log_file.open("w", encoding="utf-8") as fh,
        contextlib.redirect_stdout(fh),
        _patch_player_actions(),
    ):
        match = Match(db_path, team_a_id=team_a, team_b_id=team_b)
        match.run(ticks=ticks, realtime=False)


def _normalise_action_label(raw_action):
    if raw_action is None:
        return "idle"
    action = str(raw_action).strip()
    return action or "idle"


def _format_player_label(summary):
    name = summary.get("name") or "<unknown>"
    code = summary.get("code")
    return f"{name} [{code}]" if code else name


def _close_action_segment(summary, action, start_time, end_time):
    duration = max(0.0, end_time - start_time)
    summary["events"].append(
        {"action": action, "start": start_time, "end": end_time, "duration": duration}
    )
    summary["counts"][action] += 1
    summary["durations"][action] += duration


def analyse_ticks(log_file: Path):
    """Parse the tick log and return score, state durations, and player timelines."""

    player_summaries: dict[str, dict] = {}
    player_track: dict[str, dict[str, float | str | None]] = {}

    state_segments: list[tuple[float, str | None, float]] = []
    current_state: str | None = None
    state_start: float | None = None

    last_tick = None
    last_tick_time = 0.0
    tick_interval = 0.0
    with Path(log_file).open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or not line.startswith("{"):
                continue

            tick = json.loads(line)
            last_tick = tick

            raw_time = tick.get("time")
            current_time = float(raw_time) if raw_time is not None else last_tick_time
            if tick_interval == 0.0 and current_time > 0.0:
                tick_interval = current_time
            elif current_time > last_tick_time:
                tick_interval = current_time - last_tick_time
            last_tick_time = current_time

            state_label = tick.get("state")
            state_label = "<unknown>" if state_label is None else str(state_label)
            if current_state is None:
                current_state = state_label
                state_start = current_time
            elif state_label != current_state:
                start_time = state_start if state_start is not None else 0.0
                state_segments.append((start_time, current_state, max(0.0, current_time - start_time)))
                current_state = state_label
                state_start = current_time

            for entry in tick.get("players", []):
                name = entry.get("name")
                sn = entry.get("sn")
                team_code = entry.get("team_code")
                if sn is None or team_code is None:
                    continue

                code = f"{sn}{team_code}"
                action = _normalise_action_label(entry.get("action"))

                summary = player_summaries.setdefault(
                    code,
                    {
                        "code": code,
                        "name": name or code,
                        "counts": collections.Counter(),
                        "durations": collections.defaultdict(float),
                        "events": [],
                    },
                )
                if name and summary["name"] != name:
                    summary["name"] = name

                track = player_track.setdefault(code, {"last_action": None, "start": None})
                last_action = track["last_action"]
                start_time = track["start"]

                if last_action is None:
                    track["last_action"] = action
                    initial_start = current_time if tick_interval == 0.0 else max(0.0, current_time - tick_interval)
                    track["start"] = initial_start
                    continue

                if action != last_action:
                    segment_start = start_time if start_time is not None else current_time
                    _close_action_segment(summary, last_action, segment_start, current_time)
                    track["last_action"] = action
                    track["start"] = current_time

    final_score = last_tick["score"] if last_tick else None

    final_time = last_tick_time

    if current_state is not None:
        start_time = state_start if state_start is not None else 0.0
        state_segments.append((start_time, current_state, max(0.0, final_time - start_time)))

    state_durations = state_segments

    for code, track in player_track.items():
        last_action = track.get("last_action")
        start_time = track.get("start")
        if last_action is None or start_time is None:
            continue
        summary = player_summaries.get(code)
        if summary is None:
            continue
        _close_action_segment(summary, last_action, start_time, final_time)

    return final_score, state_durations, player_summaries


def build_action_table(player_summaries, metric: str = "counts"):
    """Return printable lines plus CSV-ready data for the requested metric."""

    if not player_summaries:
        return ["  (no player actions recorded)"], ["Player"], []

    if metric not in {"counts", "durations"}:
        raise ValueError(f"Unsupported metric '{metric}'")

    rows_by_player = {}
    for code in sorted(player_summaries):
        summary = player_summaries[code]
        label = _format_player_label(summary)
        rows_by_player[label] = summary[metric]

    actions = sorted({action for data in rows_by_player.values() for action in data})
    header = ["Player", *actions]

    display_rows = []
    csv_rows = []
    for label in sorted(rows_by_player):
        data = rows_by_player[label]
        display_row = [label]
        csv_row = [label]
        for action in actions:
            raw_value = data.get(action, 0)
            if metric == "counts":
                csv_value = int(raw_value)
                display_value = str(csv_value)
            else:
                csv_value = float(raw_value)
                display_value = f"{csv_value:.2f}"
            display_row.append(display_value)
            csv_row.append(csv_value)
        display_rows.append(display_row)
        csv_rows.append(csv_row)

    col_widths = [len(column) for column in header]
    for row in display_rows:
        for idx, value in enumerate(row):
            col_widths[idx] = max(col_widths[idx], len(value))

    def fmt(values):
        return "  " + " | ".join(
            value.ljust(col_widths[idx]) for idx, value in enumerate(values)
        )

    lines = [fmt(header)]
    lines.append("  " + "-+-".join("-" * width for width in col_widths))
    for row in display_rows:
        lines.append(fmt(row))

    return lines, header, csv_rows


def write_action_table_csv(path: Path, header, rows):
    """Persist the player action table to ``path`` as CSV."""
    with Path(path).open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        for row in rows:
            writer.writerow(row)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a match headlessly and summarise stats")
    parser.add_argument("--db", default="tmp/temp.db", help="Path to database used for match setup")
    parser.add_argument("--team-a", type=int, default=2, dest="team_a", help="Team A ID")
    parser.add_argument("--team-b", type=int, default=1, dest="team_b", help="Team B ID")
    parser.add_argument("--ticks", type=int, default=6000, help="Number of ticks to simulate")
    parser.add_argument("--log", default="ticks.jsonl", help="File to write tick JSON data")
    parser.add_argument(
        "--actions-table",
        default="player_actions.csv",
        help="Path to write player action counts as CSV",
    )
    parser.add_argument(
        "--action-durations-table",
        default=None,
        help="Optional path to write per-player action durations as CSV",
    )
    args = parser.parse_args()

    run_match(args.db, args.team_a, args.team_b, args.ticks, args.log)
    score, state_durations, player_summaries = analyse_ticks(args.log)

    print("Scoreboard:", score)
    print("State timeline:")
    for start, state, duration in state_durations:
        print(f"  {start:.2f}s -> {state} ({duration:.2f}s)")

    print("Player action counts (segments):")
    count_lines, count_header, count_rows = build_action_table(player_summaries, metric="counts")
    for line in count_lines:
        print(line)
    if count_rows and args.actions_table:
        write_action_table_csv(args.actions_table, count_header, count_rows)
        print(f"Action count table written to {args.actions_table}")

    print("Player action durations (seconds):")
    duration_lines, duration_header, duration_rows = build_action_table(player_summaries, metric="durations")
    for line in duration_lines:
        print(line)
    if duration_rows and args.action_durations_table:
        write_action_table_csv(args.action_durations_table, duration_header, duration_rows)
        print(f"Action duration table written to {args.action_durations_table}")

    print("Player action timeline:")
    if not player_summaries:
        print("  (no player actions recorded)")
    else:
        for code in sorted(player_summaries):
            summary = player_summaries[code]
            label = _format_player_label(summary)
            print(f"  {label}:")
            events = summary["events"]
            if not events:
                print("    (no action changes recorded)")
                continue
            for event in events:
                start = event["start"]
                end = event["end"]
                duration = event["duration"]
                action = event["action"]
                print(f"    {start:.2f}s - {end:.2f}s ({duration:.2f}s): {action}")


if __name__ == "__main__":
    main()
