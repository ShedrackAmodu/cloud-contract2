from django.test import TestCase
from django.contrib.auth import get_user_model
from contracts.models import Contract
from requests_app.models import DataAccessRequest
from .models import SecureComputationValidation

User = get_user_model()

class SecureComputationValidationTestCase(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='owner', email='owner@test.com', password='pass')
        self.requester = User.objects.create_user(username='requester', email='requester@test.com', password='pass')
        self.contract = Contract.objects.create(
            title='Test Contract',
            description='Test Description',
            owner=self.owner,
            visibility='PUBLIC'
        )
        self.request = DataAccessRequest.objects.create(
            contract=self.contract,
            requester=self.requester,
            reason='Test request'
        )

    def test_secure_validation_creation(self):
        """Test that secure validation can be created for a request"""
        validation = SecureComputationValidation.objects.create(request=self.request)
        self.assertFalse(validation.overall_verified)
        self.assertIsNone(validation.validated_at)

    def test_perform_validation(self):
        """Test the real validation process with cryptographic TEE"""
        validation = SecureComputationValidation.objects.create(request=self.request)
        result = validation.perform_validation()

        self.assertTrue(result)
        self.assertTrue(validation.zkp_verified)
        self.assertTrue(validation.tee_verified)
        self.assertTrue(validation.smpc_verified)
        self.assertTrue(validation.overall_verified)
        self.assertIsNotNone(validation.validated_at)
        self.assertIsNotNone(validation.zkp_proof)
        self.assertIsNotNone(validation.tee_attestation)
        self.assertIsNotNone(validation.smpc_result)
