# matchEngine/utils/logger.py

def log_tick(tick_count, match):
    print(f"[TICK {tick_count}] Ball: {match.ball.location} held by {match.ball.holder or 'None'}")

    for player in match.players:
        print(f"  - {player.sn}{player.team_code} ({player.name}): {player.current_action or 'idle'} at {player.location}")
