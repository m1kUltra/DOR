def log_tick(tick_count, match):
    print(f"[TICK {tick_count}] Ball: {match.ball.location} held by {match.ball.holder or 'None'}")
    if match.ball.holder:
        holder = match.get_player_by_code(match.ball.holder)
        dir_a = match.team_a.tactics.get("attack_dir")
        dir_b = match.team_b.tactics.get("attack_dir")
        print(f"   dirs A/B: {dir_a}/{dir_b} | holder {holder.sn}{holder.team_code} at {holder.location}")
    for player in match.players:
        print(f"  - {player.sn}{player.team_code} ({player.name}): {player.current_action or 'idle'} at {player.location}")
