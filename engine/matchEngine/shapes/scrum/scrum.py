"""Scrum shape generator.

This module builds a purpose-built 3-4-1 scrum layout using the
specification provided in the project brief.  The layout is expressed in a
field-centric coordinate system where +x is towards Team A and -x towards
Team B.  Coordinates are returned for both packs with optional scrum-halves
and hooks to extend the backline later.

The implementation mirrors the business logic for scrums contained in
``utils.mental.formations`` but focuses purely on shape generation without
player objects or match context.
"""

from __future__ import annotations

from typing import Dict, Tuple, Optional

Vec2 = Tuple[float, float]
ScrumLayout = Dict[str, Dict[int, Vec2]]



def generate_scrum_shape(
    r: float = 1.0,
    gap: float = 0.3,
    row_depth: float = 2.15,
    *,
    flanker_bind_forward: float = 0.20,
    flanker_y: float = 3.40,
    back_offset: float = 2.0,
    include_scrum_halves: bool = False,
    sh_y_offsets: Tuple[float, float] = (-4.20, -5.60),
   backline_positions: Optional[Dict[str, Dict[int, Vec2]]] = None,
) -> ScrumLayout:
    """Create a scrum layout for both teams.

    Parameters
    ----------
    r: float
        Radius of each player node in metres.
    gap: float
        Edge-to-edge tunnel width between opposing front rows.
    row_depth: float
        Centre-to-centre distance between adjacent rows of forwards.
    flanker_bind_forward: float
        Amount flankers bind ahead of locks (metres).
    flanker_y: float
        Lateral offset of flankers from scrum centre.
    back_offset: float
        Additional depth from locks to No.8.
    include_scrum_halves: bool
        Whether to include scrum-halves in the layout.
    sh_y_offsets: tuple of two floats
        Y positions for Team A and Team B scrum-halves respectively.
    backline_positions: optional mapping
        External positions to merge for backs.  Keys are "team_a"/"team_b" and
        values are mapping of role name -> (x, y).

    Returns
    -------
    dict
        ``{"team_a": {...}, "team_b": {...}}`` mapping role names to
        coordinates.
    """

    # Base geometric quantities derived from inputs
    lateral = 2.0 * r
    front_x = (2.0 * r + gap) / 2.0
    lock_x = front_x + row_depth
    flanker_x = front_x + row_depth - flanker_bind_forward
    no8_x = lock_x + back_offset

    layout: ScrumLayout = {"team_a": {}, "team_b": {}}

    # Team A (positive x, pushing left)
    a = layout["team_b"]
    a.update(
        {
      1: (front_x, +lateral),
            2: (front_x, 0.0),
            3: (front_x, -lateral),
            4: (lock_x, +1.0),
            5: (lock_x, -1.0),
            6: (flanker_x, +flanker_y),
            7: (flanker_x, -flanker_y),
            8: (no8_x, 0.0),}
    )
    if include_scrum_halves:
        a[9] = (0.0, sh_y_offsets[0])

    # Team B (mirror along x-axis)
    b = layout["team_b"]
    b.update(
        {
            1: (-front_x, -lateral),
            2: (-front_x, 0.0),
            3: (-front_x, +lateral),
            4: (-lock_x, +1.0),
            5: (-lock_x, -1.0),
            6: (-flanker_x, +flanker_y),
            7: (-flanker_x, -flanker_y),
            8: (-no8_x, 0.0),
        }
    )
    if include_scrum_halves:
        b[9] = (0.0, sh_y_offsets[1])

    # Merge externally supplied backline positions
    if backline_positions:
        for team_key in ("team_a", "team_b"):
            extra = backline_positions.get(team_key)
            if extra:
                layout[team_key].update(extra)

    return layout