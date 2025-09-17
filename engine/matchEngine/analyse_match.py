"""Utilities to analyse match tick logs produced by the match engine.

Run from the repository root with::

    python -m engine.matchEngine.analyse_match path/to/ticks.jsonl

Omitting the ``path`` argument will attempt to load ``tmp/sample_ticks.jsonl``
from the repository root, allowing for a quick look at the bundled sample data
when it is available.

The command prints the final score, a state-duration timeline, and an action
summary table derived from the captured tick data.
"""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from utils.core.logger import (
    analyse_ticks as summarise_state_timeline,
)


Tick = Mapping[str, object]


def load_ticks(path: Path) -> list[Tick]:
    """Load newline separated JSON tick blobs from *path*."""
    ticks: list[Tick] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            ticks.append(json.loads(line))
    return ticks


def analyse_ticks(ticks: Iterable[Tick]) -> dict[str, Counter[str]]:
    """Aggregate player action counts from raw tick logs."""
    actions: dict[str, Counter[str]] = defaultdict(Counter)
    for tick in ticks:
        players = tick.get("players") if isinstance(tick, Mapping) else None
        if not players:
            continue
        for player in players:  # type: ignore[assignment]
            if not isinstance(player, Mapping):
                continue
            action = player.get("action")
            if not action or action == "move":
                continue
            name = player.get("name")
            sn = player.get("sn")
            team_code = player.get("team_code")
            label_parts = [
                str(sn) + str(team_code)
                if sn is not None and team_code is not None
                else None,
                name,
            ]
            label = next((part for part in label_parts if part), None)
            if label is None:
                label = str(player.get("pid", "unknown"))
            actions[label][str(action)] += 1
    return actions


def _format_score_value(value: object) -> str:
    if isinstance(value, (int, float)):
        if isinstance(value, float) and value.is_integer():
            return f"{int(value)}"
        return f"{value}"
    return str(value)


def extract_final_score(ticks: Sequence[Tick]) -> list[tuple[str, str]]:
    """Return the most recent scoreboard entries as ``(side, score)`` pairs."""

    for tick in reversed(ticks):
        if not isinstance(tick, Mapping):
            continue
        score = tick.get("score")
        if not isinstance(score, Mapping):
            continue
        entries: list[tuple[str, str]] = []
        for side, value in score.items():
            entries.append((str(side), _format_score_value(value)))
        return entries
    return []


def build_action_table(
    actions: Mapping[str, Counter[str]],
    action_names: Iterable[str],
) -> tuple[list[str], list[list[str]]]:
    """Return headers and rows representing a table of action counts."""
    action_names = list(action_names)
    headers = ["Player", *action_names]

    rows: list[list[str]] = []
    for player in sorted(actions):
        counter = actions[player]
        row = [player, *[str(counter.get(action, 0)) for action in action_names]]
        rows.append(row)
    return headers, rows


def format_table(headers: list[str], rows: list[list[str]]) -> str:
    if not headers:
        return ""

    widths = [len(h) for h in headers]
    for row in rows:
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(cell))

    def _fmt(row: list[str]) -> str:
        return " | ".join(cell.ljust(widths[idx]) for idx, cell in enumerate(row))

    sep = "-+-".join("-" * width for width in widths)
    lines = [_fmt(headers), sep]
    for row in rows:
        lines.append(_fmt(row))
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyse match tick logs")
    parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        help=(
            "Path to the newline separated tick JSON file. Defaults to "
            "tmp/sample_ticks.jsonl when omitted."
        ),
    )
    args = parser.parse_args()

    tick_path = args.path
    if tick_path is None:
        default_path = Path("tmp/sample_ticks.jsonl")
        if default_path.exists():
            print(f"No path supplied; defaulting to {default_path}")
            tick_path = default_path
        else:
            parser.error(
                "No path provided and the default tmp/sample_ticks.jsonl sample was not found."
            )

    try:
        ticks = load_ticks(tick_path)
    except FileNotFoundError:
        parser.error(f"Could not open tick log at '{tick_path}'.")
    actions = analyse_ticks(ticks)

    final_score_entries = extract_final_score(ticks)
    if final_score_entries:
        formatted_score = ", ".join(
            f"{side} {score}" for side, score in final_score_entries
        )
    else:
        formatted_score = "unavailable"
    print(f"Final score: {formatted_score}")

    print()
    print("State durations:")
    timeline = summarise_state_timeline(ticks)
    if not timeline:
        print("No state transitions recorded.")

    print()
    print("Action counts:")
    action_names = sorted({name for counts in actions.values() for name in counts})
    if "move" in action_names:
        action_names.remove("move")

    headers, rows = build_action_table(actions, action_names)
    if rows:
        print(format_table(headers, rows))
    else:
        print("No player actions recorded.")


if __name__ == "__main__":
    main()