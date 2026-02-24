
import asyncio
import os
import asyncpg
from rich.console import Console
from rich.table import Table

async def verify_db():
    # Use localhost:5433 as per docker-compose mapping
    db_url = "postgresql://swarm:swarm-secret@localhost:5433/swarm_memory"
    console = Console()
    
    try:
        conn = await asyncpg.connect(db_url)
        console.print(f"[green]Successfully connected to {db_url}[/green]")
        
        tables = ["session_state", "archived_memory", "hipporag_graphs", "task_history", "error_knowledge"]
        
        table_output = Table(title="Database Verification Results")
        table_output.add_column("Table Name", style="cyan")
        table_output.add_column("Row Count", style="magenta")
        table_output.add_column("Status", style="green")
        
        for table in tables:
            try:
                row = await conn.fetchrow(f"SELECT count(*) FROM {table}")
                count = row['count']
                status = "✅ Populated" if count > 0 else "⚠️ Empty"
                table_output.add_row(table, str(count), status)
            except Exception as e:
                 table_output.add_row(table, "N/A", f"[red]Error: {e}[/red]")
        
        console.print(table_output)
        await conn.close()
        
    except Exception as e:
        console.print(f"[red]Connection failed: {e}[/red]")

if __name__ == "__main__":
    asyncio.run(verify_db())
