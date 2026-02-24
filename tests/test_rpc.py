import pytest
import httpx
import asyncio

@pytest.mark.anyio
async def test_rpc():
    # FastMCP uses a specific protocol over SSE, but we can also hit the 'tools/call' endpoint 
    # if it's exposed, OR we just verify the /sse endpoint handshake.
    # Actually, FastMCP adds a /tools/call endpoint relative to the mount?
    # Let's check the FastMCP docs/server implementation.
    # It usually listens on /sse for events and /messages (or similar) for POST requests.
    # The initial SSE handshake gives the endpoint for posting messages.
    
    url = "http://127.0.0.1:8000/sse"
    print(f"Connecting to {url}...")
    
    try:
        async with httpx.AsyncClient() as client:
            async with client.stream("GET", url) as response:
                print(f"SSE Status: {response.status_code}")
                
                ensure_endpoint = None
                
                async for line in response.aiter_lines():
                    if line.startswith("event: endpoint"):
                        # Next line is data: /message?session_id=...
                        pass
                    if line.startswith("data:"):
                        endpoint_suffix = line.replace("data: ", "").strip()
                        ensure_endpoint = f"http://127.0.0.1:8000{endpoint_suffix}"
                        print(f"✅ Found POST endpoint: {ensure_endpoint}")
                        break
                        
                if ensure_endpoint:
                    # Try to call 'index_codebase'
                    payload = {
                        "jsonrpc": "2.0",
                        "method": "tools/call", 
                        "params": {
                            "name": "index_codebase",
                            "arguments": {"path": "docs/ai/memory", "provider": "keyword_only"} 
                        },
                        "id": 1
                    }
                    print("Sending RPC tool call...")
                    # Note: FastMCP expects JSON-RPC 2.0 messages
                    resp = await client.post(ensure_endpoint, json=payload)
                    print(f"RPC Response ({resp.status_code}): {resp.text[:500]}")

    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_rpc())
