
import asyncio
import logging
from mcp_core.postgres_client import PostgreSQLMCPClient

# Configure logging
logging.basicConfig(level=logging.INFO)

async def ingest_knowledge():
    # Use localhost:5433 as per docker-compose mapping and verify_db_migration.py
    # Ideally this reads from env but for this script we hardcode the known working local URL
    db_url = "postgresql://swarm:swarm-secret@localhost:5433/swarm_memory"
    
    client = PostgreSQLMCPClient(url=db_url)
    
    knowledge_items = [
        {
            "pattern": "SyntaxError: Invalid or unexpected token",
            "symptom": "GitHub Actions failure in actions/github-script due to Python-style comments (#) in JavaScript code.",
            "recommendation": "Use JavaScript-style comments (//) instead of Python-style comments (#) inside github-script blocks."
        },
        {
            "pattern": "F821 undefined name",
            "symptom": "Flake8 error F821 appearing in CI even if code looks correct locally, often due to missing module-level imports for type hints.",
            "recommendation": "Ensure all types used in type hints are imported at the module level (top of file), not just inside functions, to satisfy static analysis."
        }
    ]

    print(f"Connecting to {db_url}...")
    # We don't need client.connect() as execute_query handles connection, 
    # but we need to ensure the client is initialized correctly.
    
    for item in knowledge_items:
        print(f"Ingesting: {item['pattern']}...")
        try:
            await client.save_error_knowledge(
                pattern=item["pattern"],
                symptom=item["symptom"],
                recommendation=item["recommendation"]
            )
            print("✅ Success")
        except Exception as e:
            print(f"❌ Failed: {e}")

if __name__ == "__main__":
    asyncio.run(ingest_knowledge())
