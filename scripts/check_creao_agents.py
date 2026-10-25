"""Check configuration, or explicitly submit a synthetic hosted investigation."""
import argparse
import json
from pathlib import Path
import sys
from dotenv import load_dotenv
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))
load_dotenv(root / '.env')
from backend.creao_agents import ROLES, configured_roles
from backend.creao_api import start_investigation, get_investigation
from backend import databases

parser = argparse.ArgumentParser()
parser.add_argument('--role', choices=ROLES, default='coordinator')
parser.add_argument('--run', action='store_true', help='Explicitly authorize sending synthetic observations to CREAO; saved external permission must be enabled.')
parser.add_argument('--run-id', help='Poll an existing locally owned run without starting another.')
args = parser.parse_args()
if args.run_id:
    if not databases.has_creao_run(args.run_id):
        parser.error('Run is not owned by this local workspace.')
    from backend.privacy import get_settings
    if not get_settings()['external_services_enabled']:
        parser.error('External services are disabled.')
    print(json.dumps(get_investigation(args.run_id, role=databases.creao_run_role(args.run_id)), indent=2))
elif args.run:
    result = start_investigation({'task':'investigate_visible_discoloration', 'features':{'yellow_fraction':0.2,'brown_fraction':0.1,'mean_hue':40,'texture_variance':0.2,'edge_density':0.1}}, role=args.role, explicit_authorization=True)
    databases.remember_creao_run(result['run_id'])
    databases.remember_creao_role(result['run_id'], args.role)
    print(json.dumps(result, indent=2))
else:
    print(json.dumps(configured_roles(), indent=2))
