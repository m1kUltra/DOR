# matchEngine/pitch.py

from constants import (
    PITCH_LENGTH, PITCH_WIDTH,
    DEADBALL_LINE_A_X, DEADBALL_LINE_B_X,
    TOUCHLINE_TOP_Y, TOUCHLINE_BOTTOM_Y
)

class Pitch:
    def __init__(self, length=PITCH_LENGTH, width=PITCH_WIDTH):
        self.length = length
        self.width = width

    def is_in_play(self, location):
        """Checks if a (x, y, z) location is inside the playable field."""
        x, y, _ = location
        return (
            0.0 <= x <= self.length and
            0.0 <= y <= self.width
        )

    def is_out_of_bounds(self, location):
        """Checks if location is beyond deadball lines or touchlines."""
        x, y, _ = location
        return (
            x < DEADBALL_LINE_A_X or x > DEADBALL_LINE_B_X or
            y < TOUCHLINE_BOTTOM_Y or y > TOUCHLINE_TOP_Y
        )

    def is_in_dead_zone(self, location):
        """Checks if location is within legal field but outside in-play."""
        return not self.is_in_play(location) and not self.is_out_of_bounds(location)

    def clamp_position(self, location):
        """
        Ensures the location is at least inside deadball box (won't break engine).
        Could optionally clamp back into in-play bounds.
        """
        x, y, z = location
        x = min(max(x, DEADBALL_LINE_A_X), DEADBALL_LINE_B_X)
        y = min(max(y, TOUCHLINE_BOTTOM_Y), TOUCHLINE_TOP_Y)
        return (x, y, z)

    def __repr__(self):
        return f"<Pitch {self.length}m x {self.width}m>"
