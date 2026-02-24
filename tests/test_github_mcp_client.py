import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from mcp_core.github_mcp_client import GitHubMCPClient
import json

class TestGitHubMCPClient:
    @pytest.fixture
    def client(self):
        client = GitHubMCPClient()
        client.connect = AsyncMock(return_value=True)
        def side_effect(tool_name, args):
            if tool_name == "create_issue":
                return MagicMock(content=[MagicMock(text={"number": 1, "title": "test title"})])
            elif tool_name == "merge_pull_request":
                return MagicMock(content=[MagicMock(text={"success": True})])
        client._call_tool = AsyncMock(side_effect=side_effect)
        return client

    @pytest.mark.asyncio
    async def test_connect(self, client):
        assert await client.connect() is True

    @pytest.mark.asyncio
    async def test_create_issue(self, client):
        issue = await client.create_issue("owner", "repo", "test title", "test body")
        assert issue["number"] == 1
        assert "test title" in issue["title"]

    @pytest.mark.asyncio
    async def test_merge_pull_request(self, client):
        result = await client.merge_pull_request("owner", "repo", 101)
        assert result["success"] is True
