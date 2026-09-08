#!/bin/bash
set -e

echo "================================================================="
echo "  STARTING F1 SIMULATION & ETL CONTAINER"
echo "================================================================="

echo ">>> Running Master ETL & Database Seeding..."
python etl_and_seed.py

echo ">>> Launching Continuous Live Telemetry Feeder Service..."
python live_simulator.py
