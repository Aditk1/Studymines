@echo off
echo --- Stage 1: Installing Python Libraries ---
pip install -r requirements.txt
echo --- Stage 2: Pre-downloading AI Models ---
python scripts/warmup_models.py
pause
