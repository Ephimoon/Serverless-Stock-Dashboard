import pytest

from common import secrets
from common.secrets import SecretError, get_stock_api_key


class FakeSecretsManagerClient:
    def __init__(self, secret_string):
        self.secret_string = secret_string

    def get_secret_value(self, SecretId):
        return {"SecretString": self.secret_string}


def test_get_stock_api_key_uses_local_env_key(monkeypatch):
    monkeypatch.setenv("STOCK_API_KEY", "local-key")

    result = get_stock_api_key()

    assert result == "local-key"


def test_get_stock_api_key_reads_json_secret(monkeypatch):
    monkeypatch.setenv("STOCK_API_KEY", "placeholder")

    def fake_client(service_name, region_name):
        assert service_name == "secretsmanager"
        assert region_name == secrets.AWS_REGION
        return FakeSecretsManagerClient('{"STOCK_API_KEY": "secret-key"}')

    monkeypatch.setattr(secrets.boto3, "client", fake_client)

    result = get_stock_api_key()

    assert result == "secret-key"


def test_get_stock_api_key_reads_massive_api_key_field(monkeypatch):
    monkeypatch.delenv("STOCK_API_KEY", raising=False)

    def fake_client(service_name, region_name):
        return FakeSecretsManagerClient('{"MASSIVE_API_KEY": "massive-key"}')

    monkeypatch.setattr(secrets.boto3, "client", fake_client)

    result = get_stock_api_key()

    assert result == "massive-key"


def test_get_stock_api_key_reads_raw_secret_string(monkeypatch):
    monkeypatch.delenv("STOCK_API_KEY", raising=False)

    def fake_client(service_name, region_name):
        return FakeSecretsManagerClient("raw-secret-key")

    monkeypatch.setattr(secrets.boto3, "client", fake_client)

    result = get_stock_api_key()

    assert result == "raw-secret-key"


def test_get_stock_api_key_rejects_missing_secret_name(monkeypatch):
    monkeypatch.delenv("STOCK_API_KEY", raising=False)
    monkeypatch.setattr(secrets, "SECRET_NAME", "")

    with pytest.raises(SecretError, match="missing SECRET_NAME"):
        get_stock_api_key()


def test_get_stock_api_key_rejects_empty_secret_string(monkeypatch):
    monkeypatch.delenv("STOCK_API_KEY", raising=False)

    def fake_client(service_name, region_name):
        return FakeSecretsManagerClient("")

    monkeypatch.setattr(secrets.boto3, "client", fake_client)

    with pytest.raises(SecretError, match="failed to load stock API key"):
        get_stock_api_key()


def test_get_stock_api_key_rejects_secret_without_supported_key(monkeypatch):
    monkeypatch.delenv("STOCK_API_KEY", raising=False)

    def fake_client(service_name, region_name):
        return FakeSecretsManagerClient('{"WRONG_KEY": "value"}')

    monkeypatch.setattr(secrets.boto3, "client", fake_client)

    with pytest.raises(SecretError, match="failed to load stock API key"):
        get_stock_api_key()


def test_get_stock_api_key_wraps_boto3_errors(monkeypatch):
    monkeypatch.delenv("STOCK_API_KEY", raising=False)

    def fake_client(service_name, region_name):
        raise RuntimeError("aws unavailable")

    monkeypatch.setattr(secrets.boto3, "client", fake_client)

    with pytest.raises(SecretError, match="failed to load stock API key"):
        get_stock_api_key()

def test_get_stock_api_key_trims_local_env_key(monkeypatch):
    monkeypatch.setenv("STOCK_API_KEY", "  local-key  ")

    result = get_stock_api_key()

    assert result == "local-key"

def test_get_stock_api_key_trims_json_secret_value(monkeypatch):
    monkeypatch.delenv("STOCK_API_KEY", raising=False)

    def fake_client(service_name, region_name):
        return FakeSecretsManagerClient('{"STOCK_API_KEY": "  secret-key  "}')

    monkeypatch.setattr(secrets.boto3, "client", fake_client)

    result = get_stock_api_key()

    assert result == "secret-key"


def test_get_stock_api_key_trims_raw_secret_string(monkeypatch):
    monkeypatch.delenv("STOCK_API_KEY", raising=False)

    def fake_client(service_name, region_name):
        return FakeSecretsManagerClient("  raw-secret-key  ")

    monkeypatch.setattr(secrets.boto3, "client", fake_client)

    result = get_stock_api_key()

    assert result == "raw-secret-key"