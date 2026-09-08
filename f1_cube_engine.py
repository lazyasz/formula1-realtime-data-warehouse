"""
Formula 1 Race Performance Data Cube Engine
Demonstrates Multi-Dimensional Data Cube generation and Lattice of Cuboids.
Computes multi-dimensional aggregated views across:
- Time Dimension (Season, Quarter)
- Location Dimension (Circuit Country, Track)
- Team Dimension (Constructor)
- Athlete Dimension (Driver)
"""

import sqlite3
import pandas as pd

DB_PATH = "f1_warehouse.db"

def build_data_cubes():
    conn = sqlite3.connect(DB_PATH)
    
    print("================================================================================")
    print("  DATA CUBE DESIGN & MULTI-DIMENSIONAL AGGREGATION ENGINE")
    print("================================================================================")

    # 1. 3D CUBE: [Season x Constructor x Circuit Country]
    print("\n--- [3D CUBE: Season x Constructor x Circuit Country] ---")
    query_3d = """
    SELECT 
        r.season_year,
        c.constructor_name,
        r.circuit_country,
        COUNT(f.result_id) AS total_entries,
        SUM(f.is_win) AS wins,
        SUM(f.is_podium) AS podiums,
        ROUND(SUM(f.race_points), 1) AS total_points,
        ROUND(AVG(f.race_points), 2) AS avg_points_per_entry,
        ROUND(AVG(f.finish_position), 2) AS avg_finish_position
    FROM FACT_RACE_RESULTS_STAR f
    JOIN DIM_RACE_STAR r ON f.race_id = r.race_id
    JOIN DIM_CONSTRUCTOR c ON f.constructor_id = c.constructor_id
    GROUP BY r.season_year, c.constructor_name, r.circuit_country
    ORDER BY r.season_year DESC, total_points DESC
    """
    df_3d = pd.read_sql_query(query_3d, conn)
    print(df_3d.head(12).to_string(index=False))
    print(f"[Total 3D Cuboids: {len(df_3d)}]")

    # 2. 2D CUBE: [Constructor x Season] (High-level Management View)
    print("\n--- [2D CUBE: Constructor x Season] ---")
    query_2d = """
    SELECT 
        c.constructor_name,
        r.season_year,
        SUM(f.is_win) AS total_season_wins,
        SUM(f.is_podium) AS total_podiums,
        ROUND(SUM(f.race_points), 1) AS total_season_points,
        ROUND(AVG(f.fastest_lap_speed), 2) AS avg_fastest_lap_speed
    FROM FACT_RACE_RESULTS_STAR f
    JOIN DIM_RACE_STAR r ON f.race_id = r.race_id
    JOIN DIM_CONSTRUCTOR c ON f.constructor_id = c.constructor_id
    GROUP BY c.constructor_name, r.season_year
    ORDER BY r.season_year DESC, total_season_points DESC
    """
    df_2d = pd.read_sql_query(query_2d, conn)
    print(df_2d.head(10).to_string(index=False))

    # 3. APEX CUBOID (0D All-Aggregated Grand Summary)
    print("\n--- [0D APEX CUBOID: Grand Overall Totals] ---")
    query_0d = """
    SELECT 
        COUNT(DISTINCT r.season_year) AS total_seasons,
        COUNT(DISTINCT f.race_id) AS total_grand_prix_held,
        COUNT(f.result_id) AS total_driver_entries,
        SUM(f.is_win) AS total_race_winners,
        ROUND(SUM(f.race_points), 1) AS total_points_awarded,
        ROUND(AVG(f.fastest_lap_speed), 2) AS overall_avg_top_lap_speed_kmh,
        ROUND(AVG(f.total_pit_duration_sec), 2) AS overall_avg_pit_time_sec
    FROM FACT_RACE_RESULTS_STAR f
    JOIN DIM_RACE_STAR r ON f.race_id = r.race_id
    """
    df_0d = pd.read_sql_query(query_0d, conn)
    print(df_0d.to_string(index=False))

    conn.close()

if __name__ == "__main__":
    build_data_cubes()
