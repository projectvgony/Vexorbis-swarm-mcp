import os
import sys
import asyncio
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_core.postgres_client import PostgreSQLMCPClient

async def migrate():
    # Paths
    error_log_path = Path("docs/ai/memory/active/00_ERROR_LOG.md")
    if not error_log_path.exists():
        print(f"Error log not found at {error_log_path}")
        return

    content = error_log_path.read_text(encoding="utf-8")
    
    # Simple parser for the markdown sections
    # Ideally looks for ### titles (symptoms) and then "Cause/Fix"
    sections = content.split("### ")[1:] # Skip header
    
    client = PostgreSQLMCPClient()
    await client.connect()
    
    count = 0
    for section in sections:
        lines = section.splitlines()
        if not lines:
            continue
            
        symptom = lines[0].strip()
        body = "\n".join(lines[1:])
        
        # Heuristic for pattern: use the first few words of the symptom or specialized bits
        pattern = symptom.split("(")[0].strip() if "(" in symptom else symptom
        
        # Try to extract a specific code pattern if available
        if "connectex" in body: pattern = "connectex"
        elif "ReadError" in body: pattern = "httpx.ReadError"
        elif "WinError 10048" in body: pattern = "WinError 10048"
        elif "server name" in body: pattern = "server name .* not found"
        
        print(f"Migrating: {symptom} -> Pattern: {pattern}")
        await client.save_error_knowledge(
            pattern=pattern,
            symptom=symptom,
            recommendation=body.strip()
        )
        count += 1
        
    print(f"Successfully migrated {count} entries to PostgreSQL.")

if __name__ == "__main__":
    asyncio.run(migrate())
