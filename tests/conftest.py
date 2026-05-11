"""
Shared test fixtures for VenueServer test suite.

Provides mock infrastructure for external dependencies (mtak, lad) and
ephemeral RSA keys for JWT authentication testing.
"""

import sys
import time
import pytest
from unittest.mock import MagicMock, patch

import jwt as pyjwt
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization


@pytest.fixture(scope='session')
def rsa_keys():
    """Generate an ephemeral RSA keypair for JWT testing."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption()
    ).decode()
    public_pem = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()
    return private_pem, public_pem


@pytest.fixture(scope='session')
def auth_headers(rsa_keys):
    """Generate valid JWT auth headers using the ephemeral RSA keypair."""
    private_pem, _ = rsa_keys
    token = pyjwt.encode(
        {'username': 'testuser', 'iat': int(time.time()), 'exp': int(time.time()) + 86400},
        private_pem,
        algorithm='RS256'
    )
    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }


@pytest.fixture(scope='session')
def expired_auth_headers(rsa_keys):
    """Generate expired JWT auth headers."""
    private_pem, _ = rsa_keys
    token = pyjwt.encode(
        {'username': 'testuser', 'iat': int(time.time()) - 7200, 'exp': int(time.time()) - 3600},
        private_pem,
        algorithm='RS256'
    )
    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }


def _mock_external_modules():
    """
    Insert mock modules for mtak and lad into sys.modules.
    These modules are only available in the AMPCS environment.
    """
    mock_modules = {}

    # Mock mtak module hierarchy
    mock_mtak = MagicMock()
    mock_mtak_wrapper = MagicMock()
    mock_mtak.wrapper = mock_mtak_wrapper
    mock_modules['mtak'] = mock_mtak
    mock_modules['mtak.wrapper'] = mock_mtak_wrapper

    # Mock lad module hierarchy
    mock_lad = MagicMock()
    mock_lad_client = MagicMock()
    mock_lad_gdsclient = MagicMock()
    mock_lad.client = mock_lad_client
    mock_lad.gdsclient = mock_lad_gdsclient
    mock_modules['lad'] = mock_lad
    mock_modules['lad.client'] = mock_lad_client
    mock_modules['lad.gdsclient'] = mock_lad_gdsclient

    # Mock modules that may not be installed outside the deployment environment
    for optional_mod in ['file_read_backwards', 'requests']:
        try:
            __import__(optional_mod)
        except ImportError:
            mock_modules[optional_mod] = MagicMock()

    return mock_modules


# Patch sys.modules before any app imports
_MOCK_MODULES = _mock_external_modules()
for mod_name, mod_mock in _MOCK_MODULES.items():
    if mod_name not in sys.modules:
        sys.modules[mod_name] = mod_mock


# Import app modules once at conftest load time (after external mocks are in place).
# Patch builtins.open so utils.py can load a PEM file placeholder during import.
# The actual public key is overwritten per-session by the app_client fixture.
import builtins as _builtins
_original_open = _builtins.open

def _patched_open(path, *args, **kwargs):
    if isinstance(path, str) and 'exec_venue_public_pem.pem' in path:
        from io import StringIO
        return StringIO('placeholder')
    return _original_open(path, *args, **kwargs)

_builtins.open = _patched_open
import utils as _utils   # noqa: E402
import main as _main     # noqa: E402
_builtins.open = _original_open


@pytest.fixture(scope='session')
def app_client(rsa_keys):
    """
    Create a FastAPI TestClient with all external dependencies mocked.
    Patches the JWT public key so our ephemeral RSA keys are accepted.

    Session-scoped and imports app modules once at conftest load time so that
    all test patches target the same module objects. This avoids Python 3.12
    PicklingError with ProcessPoolExecutor when module references diverge
    across re-imports.
    """
    _, public_pem = rsa_keys

    # Overwrite the placeholder public key that utils loaded during import
    _utils.exec_venue_public_pem = public_pem

    from fastapi.testclient import TestClient
    client = TestClient(_main.app)
    yield client
