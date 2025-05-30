import json

# Read the current coalition_ships_all.json file
with open('data/coalition_aircraft.json', 'r') as file:
    ships_data = json.load(file)

# Filter ships that have "Submarine Detection Skill" not equal to null
filtered_ships = [ship for ship in ships_data if ship.get("Submarine Detection Skill") is not None]

# Write the filtered data to coalition_ships_onlyASW.json
with open('data/coalition_aircraft_onlyASW.json', 'w') as file:
    json.dump(filtered_ships, file, indent=2)

print(f"Filtered from {len(ships_data)} ships to {len(filtered_ships)} ships with Submarine Detection Skill")
print(f"Results saved to coalition_aircraft_onlyASW.json")

# Print the names of ships that have submarine detection capability
print("\nShips with Submarine Detection Skill:")
for ship in filtered_ships:
    skill_level = ship.get("Submarine Detection Skill")
    print(f"- {ship['name']}: {skill_level}")