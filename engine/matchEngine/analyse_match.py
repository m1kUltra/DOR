"""Utilities to analyse match tick logs produced by the match engine."""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable, Mapping


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
        "path", type=Path, help="Path to the newline separated tick JSON file"
    )
    args = parser.parse_args()

    ticks = load_ticks(args.path)
    actions = analyse_ticks(ticks)

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
