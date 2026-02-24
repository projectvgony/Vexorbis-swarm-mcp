import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load env before imports
load_dotenv(Path(__file__).parent.parent / ".env")

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_core.postgres_client import PostgreSQLMCPClient
from mcp_core.llm import generate_embedding

async def migrate():
    """
    Migrate all markdown files from docs/ai/memory/archive/ to PostgreSQL with embeddings.
    """
    archive_dir = Path("docs/ai/memory/archive")
    if not archive_dir.exists():
        print(f"Archive directory not found at {archive_dir}")
        return

    client = PostgreSQLMCPClient()
    await client.connect()
    
    # Get all markdown files
    md_files = list(archive_dir.glob("*.md"))
    print(f"Found {len(md_files)} archive files to migrate.")
    
    count = 0
    for md_file in md_files:
        print(f"Processing: {md_file.name}...")
        
        try:
            content = md_file.read_text(encoding="utf-8")
            
            # Generate embedding
            # Use first 500 chars as summary for embedding (or full content if shorter)
            embedding_text = content[:500] if len(content) > 500 else content
            embedding = await generate_embedding(embedding_text)
            
            # Extract tags from filename (e.g., "2026_01_Summary" -> ["2026", "01", "summary"])
            tags = md_file.stem.lower().replace("-", "_").replace(" ", "_").split("_")
            
            # Save to PostgreSQL
            await client.save_archived_memory(
                content=content,
                embedding=embedding,
                source_file=md_file.name,
                tags=tags
            )
            
            count += 1
            print(f"  ✅ Migrated {md_file.name}")
            
        except Exception as e:
            print(f"  ❌ Failed to migrate {md_file.name}: {e}")
            continue
    
    print(f"\n✅ Successfully migrated {count}/{len(md_files)} archive files to PostgreSQL.")

if __name__ == "__main__":
    asyncio.run(migrate())
