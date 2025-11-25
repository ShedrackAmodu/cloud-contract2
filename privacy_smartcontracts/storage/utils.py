from cryptography.fernet import Fernet
from django.conf import settings
from django.core.files.base import ContentFile
from .models import StoredObject

def get_fernet():
    key = settings.FERNET_KEY
    if not key:
        raise RuntimeError("FERNET_KEY not set in settings or environment")
    # key should be bytes or str base64 urlsafe; ensure bytes
    if isinstance(key, str):
        key = key.encode()
    return Fernet(key)

def encrypt_bytes(raw_bytes: bytes) -> bytes:
    f = get_fernet()
    return f.encrypt(raw_bytes)

def decrypt_bytes(enc_bytes: bytes) -> bytes:
    f = get_fernet()
    return f.decrypt(enc_bytes)

def save_encrypted_file(owner, uploaded_file, name=None, meta=None):
    raw = uploaded_file.read()
    enc = encrypt_bytes(raw)
    filename = (name or uploaded_file.name) + ".enc"
    obj = StoredObject(owner=owner, name=(name or uploaded_file.name), meta=meta or {})
    obj.encrypted_file.save(filename, ContentFile(enc), save=True)
    return obj
