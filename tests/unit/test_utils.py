"""Tests for JWT utilities in utils.py

These tests import utils after mocking the PEM file loading,
since utils.py reads the PEM at module import time.
"""

import sys
import time
import pytest
from unittest.mock import patch, MagicMock

import jwt as pyjwt
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization


@pytest.fixture
def test_keys():
    """Generate a fresh RSA keypair for this test module."""
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
def wrong_keys():
    """Generate a different RSA keypair (for signature mismatch tests)."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption()
    ).decode()
    return private_pem


@pytest.fixture
def utils_module(test_keys):
    """Import utils with PEM file mocked to use ephemeral keys."""
    _, public_pem = test_keys

    # Remove cached utils module if present
    saved = sys.modules.pop('utils', None)
    try:
        import builtins
        original_open = builtins.open

        def patched_open(path, *args, **kwargs):
            if isinstance(path, str) and 'exec_venue_public_pem.pem' in path:
                from io import StringIO
                return StringIO(public_pem)
            return original_open(path, *args, **kwargs)

        with patch.object(builtins, 'open', side_effect=patched_open):
            import utils
            utils.exec_venue_public_pem = public_pem

        yield utils
    finally:
        sys.modules.pop('utils', None)
        if saved is not None:
            sys.modules['utils'] = saved


class TestGetDecodedToken:
    def test_valid_token(self, test_keys, utils_module):
        private_pem, _ = test_keys
        token = pyjwt.encode(
            {'username': 'testuser', 'iat': int(time.time()), 'exp': int(time.time()) + 3600},
            private_pem, algorithm='RS256'
        )
        result = utils_module.get_decoded_token(f'Bearer {token}')
        assert result['username'] == 'testuser'

    def test_missing_authorization_header(self, utils_module):
        with pytest.raises(Exception, match='Authorization header was not provided'):
            utils_module.get_decoded_token(None)

    def test_empty_authorization_header(self, utils_module):
        with pytest.raises(Exception, match='Authorization header was not provided'):
            utils_module.get_decoded_token('')

    def test_malformed_header_no_bearer(self, utils_module):
        with pytest.raises(Exception, match='Authorization header should be of format'):
            utils_module.get_decoded_token('Basic sometoken')

    def test_bearer_only_no_token(self, utils_module):
        with pytest.raises(Exception, match='Authorization header should be of format'):
            utils_module.get_decoded_token('Bearer')

    def test_expired_token(self, test_keys, utils_module):
        private_pem, _ = test_keys
        token = pyjwt.encode(
            {'username': 'testuser', 'iat': int(time.time()) - 7200, 'exp': int(time.time()) - 3600},
            private_pem, algorithm='RS256'
        )
        with pytest.raises(pyjwt.ExpiredSignatureError):
            utils_module.get_decoded_token(f'Bearer {token}')

    def test_invalid_signature(self, test_keys, wrong_keys, utils_module):
        wrong_private_pem = wrong_keys
        token = pyjwt.encode(
            {'username': 'testuser', 'iat': int(time.time()), 'exp': int(time.time()) + 3600},
            wrong_private_pem, algorithm='RS256'
        )
        with pytest.raises(pyjwt.InvalidSignatureError):
            utils_module.get_decoded_token(f'Bearer {token}')

    def test_token_without_exp_claim(self, test_keys, utils_module):
        private_pem, _ = test_keys
        token = pyjwt.encode(
            {'username': 'testuser', 'iat': int(time.time())},
            private_pem, algorithm='RS256'
        )
        result = utils_module.get_decoded_token(f'Bearer {token}')
        assert result['username'] == 'testuser'
