 
from django.test import TestCase, Client
from django.contrib.auth.models import User
from contracts.models import Contract
from requests_app.models import DataAccessRequest
from oracle.models import Attestation
from storage.utils import save_encrypted_file
from io import BytesIO
import json

class EndToEndFlowTest(TestCase):
    def setUp(self):
        # create users
        self.owner = User.objects.create_user("owner", "owner@test.com", "pass")
        self.requester = User.objects.create_user("requester", "req@test.com", "pass")
        self.oracle_user = User.objects.create_user("oracle", "oracle@test.com", "pass")

        self.client_owner = Client()
        self.client_requester = Client()
        self.client_oracle = Client()
        self.client_owner.login(username="owner", password="pass")
        self.client_requester.login(username="requester", password="pass")
        self.client_oracle.login(username="oracle", password="pass")

        # create contract with encrypted file
        uploaded_file = BytesIO(b"secret data")
        uploaded_file.name = "test.txt"
        self.contract = Contract.objects.create(owner=self.owner, title="Test Contract")
        save_encrypted_file(self.owner, uploaded_file, name="test.txt", meta={})
        self.contract.stored_object = self.contract.owner.stored_objects.first()
        self.contract.save()

    def test_full_flow(self):
        # requester creates access request
        self.client_requester.post(f"/requests/create/{self.contract.id}/", {"reason": "Need access"})
        dar = DataAccessRequest.objects.get(contract=self.contract, requester=self.requester)
        self.assertEqual(dar.status, "PENDING")

        # owner approves request
        self.client_owner.get(f"/requests/process/{dar.id}/approve/")
        dar.refresh_from_db()
        self.assertEqual(dar.status, "APPROVED")

        # oracle signs request
        resp = self.client_oracle.post(f"/oracle/sign/{dar.id}/")
        self.assertEqual(resp.status_code, 302)  # redirect
        att = Attestation.objects.get(data_request=dar)
        self.assertTrue(att.signature_b64)

        # requester retrieves file
        resp = self.client_requester.get(f"/access/retrieve/{dar.id}/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, b"secret data")
