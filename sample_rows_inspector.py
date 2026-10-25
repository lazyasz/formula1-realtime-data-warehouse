import pandas as pd

df = pd.read_csv("F1_ML_Winner_Prediction_Dataset.csv", low_memory=False)

samples = [
    ("Michael Schumacher", 2004, "Ferrari"),
    ("Sebastian Vettel", 2012, "Red Bull"),
    ("Lewis Hamilton", 2020, "Mercedes"),
    ("Max Verstappen", 2024, "Red Bull"),
    ("Lando Norris", 2024, "McLaren")
]

for driver, season, team in samples:
    match = df[(df["driver_name"].str.contains(driver, case=False, na=False)) & (df["season"] == season) & (df["constructor_name"].str.contains(team, case=False, na=False))]
    if len(match) > 0:
        row = match.iloc[0]
        print("="*85)
        print(f"DRIVER: {row['driver_name']} ({row['constructor_name']}) | SEASON: {row['season']} Round {row['round']} ({row['race_name']})")
        print("="*85)
        print("1. CAR FEATURES:")
        print(f"   - Chassis Model             : {row['car_chassis_model']}")
        print(f"   - Power Unit Supplier       : {row['car_power_unit_supplier']}")
        print(f"   - Engine Architecture       : {row['car_engine_architecture']}")
        print(f"   - Estimated Engine Output   : {row['car_estimated_power_bhp']} BHP")
        print(f"   - Min Car Regulation Weight : {row['car_min_weight_kg']} kg")
        print(f"   - Power-to-Weight Ratio     : {row['car_power_to_weight_ratio']} BHP/kg")
        print(f"   - Mechanical Reliability    : {row['car_mechanical_reliability_score']*100:.1f}%")
        print(f"   - Constructor Pace Index    : {row['constructor_pace_index']}")
        print("2. LAP RECORD & SPEEDS:")
        print(f"   - Circuit All-Time Record   : {row['circuit_lap_record_str']} ({row['circuit_lap_record_sec']}s)")
        print(f"   - Record Holder & Year      : {row['circuit_lap_record_holder']} ({row['circuit_lap_record_year']})")
        print(f"   - Driver Race Fastest Lap   : {row['driver_fastest_lap_sec']}s")
        print(f"   - Gap to All-Time Record    : +{row['driver_lap_record_delta_sec']}s")
        print(f"   - Pace Ratio vs Record      : {row['driver_lap_record_ratio']}")
        print(f"   - Driver Qualifying Time    : {row['driver_qualifying_sec']}s")
        print(f"   - Quali Delta to Record     : +{row['driver_quali_to_record_delta_sec']}s")
        print("3. PIT STOP STRATEGY & TIMES:")
        print(f"   - Total Pit Stops           : {row['pit_stop_count']}")
        print(f"   - Avg Pit Duration          : {row['avg_pit_duration_sec']}s")
        print(f"   - Est. Stationary Stop Time : {row['estimated_stationary_pit_sec']}s")
        print(f"   - Circuit Pit Lane Loss     : {row['circuit_pit_lane_loss_sec']}s")
        print(f"   - Pit Crew Efficiency Score : {row['pit_crew_efficiency_score']}/100")
        print(f"   - Net Race Pit Loss         : {row['total_race_pit_loss_sec']}s")
        print(f"   - Pit Delta to Field Mean   : {row['pit_loss_delta_to_race_mean_sec']}s")
        print("4. RACE OUTCOME & TARGET:")
        print(f"   - Grid: P{row['grid_position']} | Finish: P{int(row['finish_position']) if pd.notna(row['finish_position']) else 'DNF'} | Grand Prix Winner (is_win): {row['is_win']}")
        print()
