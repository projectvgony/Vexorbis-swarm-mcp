"""
Test script for Vector Archive functionality.
This creates test data with mock embeddings to verify the database schema and tools work.
"""
import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load env before imports
load_dotenv(Path(__file__).parent.parent / ".env")

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from mcp_core.postgres_client import PostgreSQLMCPClient

@pytest.mark.asyncio
async def test_vector_archive():
    """Test the vector archive with mock embeddings."""
    print("🧪 Testing Vector Archive Implementation...\n")
    
    # Mock embedding (768-dimensional vector of zeros for testing)
    mock_embedding = [0.0] * 768
    mock_embedding[0] = 1.0  # Make it slightly different for search ranking
    
    client = PostgreSQLMCPClient()
    
    # Test 1: Save archived memory
    print("1. Testing save_archived_memory...")
    try:
        await client.save_archived_memory(
            content="# Archived Task: Authentication Refactor\n\nImplemented OAuth2 flow with JWT tokens.",
            embedding=mock_embedding,
            source_file="2026_01_auth_refactor.md",
            tags=["authentication", "oauth", "jwt"]
        )
        print("   ✅ Successfully saved archived memory\n")
    except Exception as e:
        print(f"   ❌ Failed: {e}\n")
        return
    
    # Test 2: Save another entry
    print("2. Adding second entry...")
    mock_embedding2 = [0.0] * 768
    mock_embedding2[1] = 1.0
    try:
        await client.save_archived_memory(
            content="# Archived Task: Database Migration\n\nMigrated from SQLite to PostgreSQL with zero downtime.",
            embedding=mock_embedding2,
            source_file="2026_01_db_migration.md",
            tags=["database", "migration", "postgresql"]
        )
        print("   ✅ Successfully saved second entry\n")
    except Exception as e:
        print(f"   ❌ Failed: {e}\n")
        return
    
    # Test 3: Search archived memory
    print("3. Testing search_archived_memory...")
    query_embedding = mock_embedding  # Use same embedding to test similarity
    try:
        results = await client.search_archived_memory(query_embedding, top_k=5)
        print(f"   ✅ Search returned {len(results)} results")
        if results:
            for i, res in enumerate(results, 1):
                print(f"      {i}. {res.get('source_file', 'Unknown')} (similarity: {res.get('similarity', 0):.4f})")
        print()
    except Exception as e:
        print(f"   ❌ Search failed: {e}\n")
        return
    
    # Test 4: Session State (bonus)
    print("4. Testing session state save/load...")
    try:
        await client.save_session_state(
            session_id="test_session_001",
            profile_data={"tasks": [{"id": 1, "description": "Test task"}]},
            agent_id="test_agent"
        )
        print("   ✅ Saved session state")
        
        loaded = await client.load_session_state("test_session_001")
        if loaded:
            print(f"   ✅ Loaded session state: {loaded}")
        else:
            print("   ⚠️  Session state was saved but couldn't be loaded")
        print()
    except Exception as e:
        print(f"   ❌ Session state test failed: {e}\n")
    
    print("🏆 Vector Archive Schema Test Complete!")
    print("\nNote: This test used mock embeddings. Real usage requires:")
    print("  - POSTGRES_URL environment variable")
    print("  - GEMINI_API_KEY or OPENAI_API_KEY for embeddings")
    print("  - Run 'python scripts/migrate_archive.py' to migrate real data")

if __name__ == "__main__":
    asyncio.run(test_vector_archive())
