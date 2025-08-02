# matchEngine/ball.py

class Ball:
    def __init__(self, location=(0.0, 0.0, 0.0), holder=None):
        """
        location: (x, y, z) coordinates in meters
        holder: string like '15a' representing sn + team_code, or None if loose
        """
        self.location = location
        self.holder = holder  # e.g. "9a", "12b", None if free

    def is_held(self):
        return self.holder is not None

    def release(self):
        self.holder = None

    def update(self, match):
        """
        Called every tick from Match.update()
        If held, lock position to the holder's player
        """
        if self.holder:
            sn = int(self.holder[:-1])
            team_code = self.holder[-1]
            team = match.team_a if team_code == 'a' else match.team_b
            player = team.get_player_by_sn(sn)

            if player:
                self.location = player.location  # Ball moves with player
            