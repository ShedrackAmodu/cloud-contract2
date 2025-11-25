from django.test import TestCase

# Create your tests here.
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
# set FERNET_KEY=<output> in .env
