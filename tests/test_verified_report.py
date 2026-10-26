"""Email configuration and verification checks; SMTP is mocked, no email sent."""
import os
import tempfile
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.main import app
from backend import databases

class VerifiedReportTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.env=patch.dict(os.environ,{'SQLITE_DB_PATH':self.tmp.name+'/test.db','VIGILO_API_TOKEN':'','VIGILO_SMTP_HOST':'','VIGILO_SMTP_FROM':'','VIGILO_SMTP_USER':'','VIGILO_SMTP_PASSWORD':'','VIGILO_REPORT_SECRET':''})
        self.env.start();self.client=TestClient(app)
        self.payload={'email':'test@example.org','consent_to_email':True,'yellow_fraction':.2,'brown_fraction':.1,'anomaly_score':.24,'leaf_coverage_fraction':.4}
    def tearDown(self):
        self.client.close();self.env.stop();self.tmp.cleanup()
    def configured(self):
        return patch.dict(os.environ,{'VIGILO_SMTP_HOST':'smtp.example.org','VIGILO_SMTP_FROM':'sender@example.org','VIGILO_SMTP_USER':'sender','VIGILO_SMTP_PASSWORD':'test-only-password','VIGILO_REPORT_SECRET':'test-only-secret-that-is-long-enough-000'})
    def test_missing_settings_have_public_status_without_values(self):
        response=self.client.get('/reports/verify/status')
        self.assertEqual(response.status_code,200)
        self.assertFalse(response.json()['available'])
        self.assertIn('VIGILO_REPORT_SECRET',response.json()['missing_settings'])
    def test_503_identifies_requirements_and_does_not_create_request(self):
        result=self.client.post('/reports/verify/start',json=self.payload)
        self.assertEqual(result.status_code,503)
        self.assertIn('Download your report',result.json()['detail'])
    def test_no_consent_denied(self):
        result=self.client.post('/reports/verify/start',json={**self.payload,'consent_to_email':False})
        self.assertEqual(result.status_code,400)
    def test_full_email_protocol_with_mock_provider(self):
        with self.configured(),patch('backend.verified_report.send_mail') as sender,patch('backend.verified_report.secrets.randbelow',return_value=123456):
            started=self.client.post('/reports/verify/start',json=self.payload)
            self.assertEqual(started.status_code,200,started.text)
            confirmed=self.client.post('/reports/verify/confirm',json={'request_id':started.json()['request_id'],'code':'123456'})
            self.assertEqual(confirmed.status_code,200,confirmed.text)
            self.assertTrue(confirmed.json()['sent'])
            self.assertEqual(sender.call_count,2)
            self.assertEqual(self.client.post('/reports/verify/confirm',json={'request_id':started.json()['request_id'],'code':'123456'}).status_code,400)
    def test_failed_report_delivery_can_be_retried_without_fake_success(self):
        from fastapi import HTTPException
        with self.configured(),patch('backend.verified_report.send_mail',side_effect=[None,HTTPException(502,'Provider unavailable'),None]),patch('backend.verified_report.secrets.randbelow',return_value=123456):
            started=self.client.post('/reports/verify/start',json=self.payload).json()
            payload={'request_id':started['request_id'],'code':'123456'}
            self.assertEqual(self.client.post('/reports/verify/confirm',json=payload).status_code,502)
            retry=self.client.post('/reports/verify/confirm',json=payload)
            self.assertEqual(retry.status_code,200,retry.text)
            self.assertTrue(retry.json()['sent'])
    def test_wrong_attempts_are_committed_and_capped(self):
        with self.configured(),patch('backend.verified_report.send_mail'),patch('backend.verified_report.secrets.randbelow',return_value=123456):
            started=self.client.post('/reports/verify/start',json=self.payload).json()
            for _ in range(5):
                self.assertEqual(self.client.post('/reports/verify/confirm',json={'request_id':started['request_id'],'code':'999999'}).status_code,400)
            with databases.connection() as db:
                count=db.execute('SELECT attempts FROM verified_report_requests WHERE id=?',(started['request_id'],)).fetchone()[0]
            self.assertEqual(count,5)
            self.assertEqual(self.client.post('/reports/verify/confirm',json={'request_id':started['request_id'],'code':'123456'}).status_code,400)
