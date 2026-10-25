"""Verify genuine local Fetch messaging with synthetic observations."""
import asyncio
from pathlib import Path
import sys
from dotenv import load_dotenv
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))
load_dotenv(root / '.env')
from backend.fetch_client import investigate
result = asyncio.run(investigate({'features': {'yellow_fraction':0.2,'brown_fraction':0.1,'mean_hue':40,'texture_variance':0.2,'edge_density':0.1},'anomaly_score':0.3,'crop_category':'tomato'}))
assert 'Received five numeric' in result['summary'], 'Receiver did not process the observations.'
print(result)
