# backend/tests/test_integrations_mock.py

import pytest
import sys
from unittest.mock import AsyncMock, Mock, patch

# MOCK SYS MODULES BEFORE IMPORTING ANYTHING THAT MIGHT TRIGGER THE ERROR
# We mock 'backend.src.integrations.enterprise.mssql_client' etc.
# to avoid the ImportError due to missing system libs.
mock_module = Mock()
sys.modules["backend.src.integrations.enterprise.mssql_client"] = mock_module
sys.modules["backend.src.integrations.enterprise.oracle_client"] = mock_module
sys.modules["backend.src.integrations.enterprise.snowflake_client"] = mock_module
sys.modules["backend.src.integrations.enterprise.sap_client"] = mock_module
sys.modules["backend.src.integrations.enterprise.servicenow_client"] = mock_module
sys.modules["backend.src.integrations.enterprise.gitlab_client"] = mock_module
sys.modules["backend.src.integrations.enterprise.bitbucket_client"] = mock_module

sys.modules["src.integrations.enterprise.mssql_client"] = mock_module
sys.modules["src.integrations.enterprise.oracle_client"] = mock_module
sys.modules["src.integrations.enterprise.snowflake_client"] = mock_module
sys.modules["src.integrations.enterprise.sap_client"] = mock_module
sys.modules["src.integrations.enterprise.servicenow_client"] = mock_module
sys.modules["src.integrations.enterprise.gitlab_client"] = mock_module
sys.modules["src.integrations.enterprise.bitbucket_client"] = mock_module

# Also mock the top level package to avoid circular imports if needed
# But here we just want to bypass the submodules that fail.

from src.utils.config import Settings
from src.integrations.github.client import GitHubClient
from src.integrations.iac.terraform import TerraformClient
from src.integrations.enterprise.chat_ops import ChatOpsClient
from src.api.routes.webhooks import slack_interactive_webhook

@pytest.fixture
def settings():
    # Use patch to avoid modifying the actual Settings class which might be frozen or validated
    with patch("src.utils.config.Settings") as MockSettings:
        s = MockSettings.return_value
        s.GITHUB_TOKEN = "fake-token"
        s.SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/XXX"
        s.TERRAFORM_BINARY_PATH = "terraform"
        # Mock getattr behavior for arbitrary attributes if needed
        return s

@pytest.mark.asyncio
async def test_github_client_create_methods(settings):
    client = GitHubClient(settings)

    # Mock the internal _request method to avoid network calls
    client._request = AsyncMock()
    client._request.return_value.status_code = 201
    client._request.return_value.json.return_value = {"id": 1, "url": "http://github.com/api/..."}

    # Test create_branch
    await client.create_branch("org", "repo", "new-feature", "sha123")
    client._request.assert_called_with(
        "POST",
        "/repos/org/repo/git/refs",
        json={"ref": "refs/heads/new-feature", "sha": "sha123"}
    )

    # Test create_file
    client._request.reset_mock()
    client._request.return_value.status_code = 201
    await client.create_file("org", "repo", "path/to/file.txt", "add file", "content", "main")

    # Verify content was base64 encoded
    import base64
    expected_content = base64.b64encode(b"content").decode("utf-8")

    client._request.assert_called_with(
        "PUT",
        "/repos/org/repo/contents/path/to/file.txt",
        json={
            "message": "add file",
            "content": expected_content,
            "branch": "main"
        }
    )

    # Test create_pull_request
    client._request.reset_mock()
    client._request.return_value.status_code = 201
    await client.create_pull_request("org", "repo", "Title", "Body", "head", "base")
    client._request.assert_called_with(
        "POST",
        "/repos/org/repo/pulls",
        json={"title": "Title", "body": "Body", "head": "head", "base": "base"}
    )

def test_terraform_client(settings):
    # Mock shutil.which to pretend terraform exists
    with patch("shutil.which", return_value="/usr/bin/terraform"):
        client = TerraformClient(settings)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "Plan: 1 to add"
            mock_run.return_value.stderr = ""

            # Test init
            client.init("/tmp/tf")
            mock_run.assert_called_with(
                ["terraform", "init", "-no-color"],
                cwd="/tmp/tf",
                capture_output=True,
                text=True,
                check=False
            )

            # Test plan
            client.plan("/tmp/tf", out_file="tfplan")
            mock_run.assert_called_with(
                ["terraform", "plan", "-no-color", "-input=false", "-out", "tfplan"],
                cwd="/tmp/tf",
                capture_output=True,
                text=True,
                check=False
            )

@pytest.mark.asyncio
async def test_chat_ops_client(settings):
    client = ChatOpsClient(settings)

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value.status_code = 200

        await client.ask_for_approval("req-123", "Block IPs?")

        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == settings.SLACK_WEBHOOK_URL
        json_body = kwargs["json"]
        assert "blocks" in json_body
        assert "req-123" in json_body["blocks"][0]["text"]["text"]

@pytest.mark.asyncio
async def test_chat_ops_webhook():
    from fastapi import Request

    # Mock Request
    request = Mock(spec=Request)
    request.form = AsyncMock()

    # Simulate Slack payload
    payload = {
        "actions": [{"value": "req-123:Approve"}]
    }
    import json
    request.form.return_value = {"payload": json.dumps(payload)}

    response = await slack_interactive_webhook(request)
    assert response == {"text": "Request req-123: Approve received."}
