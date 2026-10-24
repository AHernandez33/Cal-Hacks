"""Explicitly synthetic telemetry, local fallback until Tiger Data credentials/config exist."""
from datetime import datetime,timedelta,timezone

def history():
    now=datetime.now(timezone.utc).replace(minute=0,second=0,microsecond=0)
    return {'source':'synthetic demonstration (not Tiger Data)','units':{'soil_moisture':'fraction','temperature_c':'°C'},
      'measurements':[{'timestamp':(now-timedelta(hours=23-i)).isoformat(),
                       'soil_moisture':round(0.34+0.07*((i%7)/7),3),
                       'temperature_c':round(19+((i*3)%11)/2,2),
                       'humidity_pct':round(57+((i*5)%24),1)} for i in range(24)]}
