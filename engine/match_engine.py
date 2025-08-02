import json
import random
import os

def load_roster(filename):
    with open(filename, 'r') as f:
        return json.load(f)

def avg_current_ability(players):
    total = sum(p['current_ability'] for p in players)
    return total / len(players) if players else 0

def simulate_match(team1_name, team1_players, team2_name, team2_players, turns=20):
    team1_avg = avg_current_ability(team1_players)
    team2_avg = avg_current_ability(team2_players)

    score = {team1_name: 0, team2_name: 0}
    events = []

    for turn in range(1, turns + 1):
        # Weighted dice roll for who scores
        total_ability = team1_avg + team2_avg
        roll = random.uniform(0, total_ability)

        # Determine scoring team and their players
        if roll <= team1_avg:
            scoring_team = team1_name
            scoring_players = team1_players
        else:
            scoring_team = team2_name
            scoring_players = team2_players

        # Pick event type
        event_type = random.choices(
            ['try', 'penalty', 'drop_goal', 'no_score'],
            weights=[0.3, 0.2, 0.1, 0.5],
            k=1
        )[0]

        if event_type == 'no_score':
            points = 0
            events.append(f"Turn {turn}: No score")
        else:
            scorer = random.choice(scoring_players)['name']

            if event_type == 'try':
                points = 5
                score[scoring_team] += points
                events.append(f"Turn {turn}: {scoring_team} scored a TRY by {scorer} (+5 points)")

                # Conversion attempt (50% chance success)
                conversion_success = random.random() < 0.75
                if conversion_success:
                    score[scoring_team] += 2
                    events.append(f"Turn {turn}: {scoring_team} made a CONVERSION (+2 points)")
                else:
                    events.append(f"Turn {turn}: {scoring_team} missed the CONVERSION")

            elif event_type == 'penalty':
                points = 3
                score[scoring_team] += points
                events.append(f"Turn {turn}: {scoring_team} kicked a PENALTY by {scorer} (+3 points)")

            elif event_type == 'drop_goal':
                points = 3
                score[scoring_team] += points
                events.append(f"Turn {turn}: {scoring_team} scored a DROP GOAL by {scorer} (+3 points)")

    return score, events

from load_squad_from_db import load_team_from_db

if __name__ == "__main__":
    db_path = "tmp/temp.db"  # <-- your active temp save
    england_name, england_players = load_team_from_db(db_path, nation_team_id=2)
    ireland_name, ireland_players = load_team_from_db(db_path, nation_team_id=1)

    final_score, match_events = simulate_match(england_name, england_players, ireland_name, ireland_players)

    print("Match Events:")
    for event in match_events:
        print(event)

    print("\nFinal Score:")
    print(f"{england_name} {final_score[england_name]} - {final_score[ireland_name]} {ireland_name}")

