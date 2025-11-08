# Privacy-Preserving Smart Contracts — Django PoC

## Overview

This is a **3-week PoC** demonstrating privacy-preserving smart contracts with:

- Policy creation & management (Owner)
- Requestor flow to request access
- Mock Oracle that signs attestations (PoC for ZKP/TEE)
- Access Proxy that verifies attestation & issues ephemeral access
- Encrypted storage (local, Fernet-based)
- Authentication (owner/requester/admin), audit log
- Docker-ready & CI-friendly

> **Note:** For PoC, ZKP/TEE is mocked. Full integration requires more work.

---

## Project Structure

privacy_smartcontracts/
├─ contracts/ # contract/policy management
├─ storage/ # encrypted file storage
├─ requests_app/ # data access request handling
├─ oracle/ # mock oracle to sign requests
├─ access_proxy/ # retrieves file after verifying attestation
├─ audit/ # logs all events
├─ users/ # user accounts, roles
├─ privacy_smartcontracts/ # main Django project (settings, urls)
├─ templates/
├─ static/
├─ media/
├─ .env # environment variables (FERNET_KEY, ORACLE keys)
└─ manage.py


---

## Prerequisites

- Python 3.10+
- pip
- virtualenv
- Git
- Optional: Docker

---

## Setup Instructions

```bash
# clone repo
git clone <your-repo-url>
cd privacy_smartcontracts

# create virtualenv
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate    # Windows

# install dependencies
pip install django djangorestframework python-dotenv cryptography

# create .env file in project root
# FERNET_KEY = Fernet.generate_key()
# ORACLE_PRIVATE_KEY = <base64 from Ed25519>
# ORACLE_PUBLIC_KEY = <base64 from Ed25519>
# SECRET_KEY = <any django secret>
# DEBUG=1
# ALLOWED_HOSTS=127.0.0.1,localhost

# make migrations
python manage.py makemigrations
python manage.py migrate

# create superuser
python manage.py createsuperuser

# run development server
python manage.py runserver
