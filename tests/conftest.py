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


@pytest.fixture
def auth_headers(rsa_keys):
    """Generate valid JWT auth headers using the ephemeral RSA keypair."""
    private_pem, _ = rsa_keys
    token = pyjwt.encode(
        {'username': 'testuser', 'iat': int(time.time()), 'exp': int(time.time()) + 3600},
        private_pem,
        algorithm='RS256'
    )
    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }


@pytest.fixture
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

    # Mock file_read_backwards if not available
    try:
        import file_read_backwards  # noqa: F401
    except ImportError:
        mock_modules['file_read_backwards'] = MagicMock()

    return mock_modules


# Patch sys.modules before any app imports
_MOCK_MODULES = _mock_external_modules()
for mod_name, mod_mock in _MOCK_MODULES.items():
    if mod_name not in sys.modules:
        sys.modules[mod_name] = mod_mock


@pytest.fixture
def app_client(rsa_keys):
    """
    Create a FastAPI TestClient with all external dependencies mocked.
    Patches the JWT public key so our ephemeral RSA keys are accepted.
    """
    _, public_pem = rsa_keys

    # We need to patch the public key used for JWT verification in utils module.
    # The app module imports utils at module level, so we patch after import.
    # Clear any cached app module state to get fresh imports
    modules_to_clear = [k for k in sys.modules if k.startswith(('main', 'core.', 'utils'))]
    saved_modules = {}
    for mod in modules_to_clear:
        saved_modules[mod] = sys.modules.pop(mod)

    try:
        # Patch the PEM file open so utils.py doesn't fail on missing file
        import builtins
        original_open = builtins.open

        def patched_open(path, *args, **kwargs):
            if isinstance(path, str) and 'exec_venue_public_pem.pem' in path:
                from io import StringIO
                return StringIO(public_pem)
            return original_open(path, *args, **kwargs)

        with patch.object(builtins, 'open', side_effect=patched_open):
            import utils
            import main
            from fastapi.testclient import TestClient
            # Also patch the already-loaded public key
            utils.exec_venue_public_pem = public_pem

        client = TestClient(main.app)
        yield client
    finally:
        # Restore original modules
        modules_to_clear_again = [k for k in sys.modules if k.startswith(('main', 'core.', 'utils'))]
        for mod in modules_to_clear_again:
            sys.modules.pop(mod, None)
        for mod, module in saved_modules.items():
            sys.modules[mod] = module
