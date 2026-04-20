Write-Host "--- Stage 1: Installing Python Libraries ---" -ForegroundColor Cyan
pip install -r requirements.txt

Write-Host "--- Stage 2: Pre-downloading AI Models ---" -ForegroundColor Cyan
python scripts/warmup_models.py
