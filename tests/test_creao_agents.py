"""App-scoped contracts, privacy boundaries, role ownership, output handling."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import httpx
from backend import databases
from backend.creao_api import start_investigation, get_investigation
from backend.creao_agents import ROLES
from backend.identity import workspace_id

FEATURES = {'yellow_fraction':0.2,'brown_fraction':0.1,'mean_hue':40,'texture_variance':0.2,'edge_density':0.1}

class HostedAgents(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        settings = {'SQLITE_DB_PATH':str(Path(self.temp.name)/'db.sqlite')}
        for role in ROLES:
            settings['CREAO_'+role.upper()+'_APP_ID'] = 'app-'+role
            settings['CREAO_'+role.upper()+'_API_KEY'] = 'test-only-'+role
        self.env = patch.dict(os.environ, settings)
        self.env.start()
        databases.set_preferences({'external_services_enabled':True})
        from backend.RAG.ingest import ingest_documents
        ingest_documents()
    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()
    def test_each_role_uses_matching_app_and_key(self):
        for role in ROLES:
            with self.subTest(role=role):
                def handler(request):
                    self.assertEqual(request.url.path, '/api/v1/apps/app-'+role+'/runs')
                    self.assertEqual(request.headers['authorization'], 'Bearer test-only-'+role)
                    body=json.loads(request.content)
                    self.assertEqual(set(body), {'inputs'})
                    self.assertEqual(set(body['inputs']), {'measurements','observations','crop','references','question'} if role=='leaf_analyst' else {'prompt'})
                    return httpx.Response(202,json={'id':'run-123456','status':'pending'})
                with httpx.Client(transport=httpx.MockTransport(handler)) as client:
                    result=start_investigation({'task':'investigate_visible_discoloration','features':FEATURES},role=role,explicit_authorization=True,client=client)
                    self.assertEqual(result['role'],role)
    def test_denied_payload_sends_no_request(self):
        for authorized,payload in [(False,{'task':'investigate_visible_discoloration','features':FEATURES}),(True,{'task':'investigate_visible_discoloration','features':FEATURES,'raw_image':'private'})]:
            def handler(request):
                self.fail('Privacy rejection must happen before network access')
            with httpx.Client(transport=httpx.MockTransport(handler)) as client:
                with self.assertRaises(PermissionError):
                    start_investigation(payload,explicit_authorization=authorized,client=client)
    def test_output_variants_and_matching_poll_key(self):
        for field in ('result','outputs','output'):
            def handler(request):
                self.assertEqual(request.headers['authorization'],'Bearer test-only-leaf_analyst')
                self.assertEqual(request.url.path,'/api/v1/runs/run-123456')
                return httpx.Response(200,json={'status':'Complete',field:{'text':'observed'}})
            with httpx.Client(transport=httpx.MockTransport(handler)) as client:
                result=get_investigation('run-123456',role='leaf_analyst',client=client)
                self.assertEqual(result['status'],'completed')
                self.assertEqual(result['result'],{'text':'observed'})
    def test_completed_empty_output_is_explicit(self):
        with httpx.Client(transport=httpx.MockTransport(lambda r:httpx.Response(200,json={'status':'completed'}))) as client:
            self.assertIn('without usable',get_investigation('run-123456',client=client)['notice'])
    def test_roles_and_runs_are_owner_scoped(self):
        marker=workspace_id.set('owner-a')
        try:
            databases.remember_creao_run('run-123456')
            databases.remember_creao_role('run-123456','leaf_analyst')
            self.assertEqual(databases.creao_run_role('run-123456'),'leaf_analyst')
            workspace_id.set('owner-b')
            self.assertFalse(databases.has_creao_run('run-123456'))
            self.assertEqual(databases.creao_run_role('run-123456'),'coordinator')
        finally:
            workspace_id.reset(marker)

    def test_immediate_completion_keeps_output(self):
        from backend.orchestration.coordinator import coordinate
        from backend.orchestration.schemas import InvestigationRequest
        with patch('backend.creao_api.api_request', return_value={'id':'run-immediate', 'status':'Complete','outputs':{'text':'immediate result'}}):
            result = coordinate(InvestigationRequest(features=FEATURES, provider='creao', creao_role='leaf_analyst', authorize_external=True))
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['result'], {'text':'immediate result'})
        self.assertTrue(databases.has_creao_run('run-immediate'))
        self.assertEqual(databases.creao_run_role('run-immediate'), 'leaf_analyst')

    def test_partial_coordinator_credentials_do_not_mix_with_legacy(self):
        from backend.creao_api import credentials, CreaoConfigurationError
        with patch.dict(os.environ, {'CREAO_COORDINATOR_APP_ID':'', 'CREAO_COORDINATOR_API_KEY':'new-test-key', 'creao_app_id':'legacy-app', 'creao_api_key':'legacy-test-key'}):
            with self.assertRaises(CreaoConfigurationError):
                credentials()

    def test_status_route_uses_owned_role_and_hides_other_workspaces(self):
        from fastapi.testclient import TestClient
        from backend.main import app
        with patch.dict(os.environ, {'VIGILO_API_TOKEN':''}), TestClient(app) as client:
            owner = client.post('/auth/workspaces').json()
            other = client.post('/auth/workspaces').json()
            headers = {'Authorization': 'Bearer ' + owner['token']}
            client.put('/privacy/settings', json={'external_services_enabled':True}, headers=headers)
            def remote(method, path, **kwargs):
                self.assertEqual(kwargs['role'], 'leaf_analyst')
                return {'id':'run-owned-123', 'status':'pending' if method=='POST' else 'completed', 'output':'owned result'}
            with patch('backend.creao_api.api_request', side_effect=remote) as transport:
                start = client.post('/agents/analyze', json={'features':FEATURES,'provider':'creao','creao_role':'leaf_analyst','authorize_external':True}, headers=headers)
                self.assertEqual(start.status_code,200,start.text)
                done = client.get('/agents/creao/run-owned-123',headers=headers)
                self.assertEqual(done.json()['result'],'owned result')
                count = transport.call_count
                denied = client.get('/agents/creao/run-owned-123',headers={'Authorization':'Bearer '+other['token']})
                self.assertEqual(denied.status_code,404)
                self.assertEqual(transport.call_count,count)
            deleted = client.delete('/auth/workspace',headers=headers)
            self.assertEqual(deleted.status_code,200)
            with databases.connection() as db:
                self.assertEqual(db.execute('SELECT count(*) FROM creao_run_roles WHERE owner_id=?',(owner['workspace_id'],)).fetchone()[0],0)
