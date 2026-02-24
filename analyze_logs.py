
import sqlite3
import json
import os
from pathlib import Path
from collections import Counter
from datetime import datetime

def analyze_telemetry():
    db_path = Path.home() / ".swarm" / "telemetry.db"
    
    if not db_path.exists():
        print(f"Telemetry database not found at {db_path}")
        return

    print(f"Reading telemetry from {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Total events
        cursor.execute("SELECT COUNT(*) FROM events")
        total_events = cursor.fetchone()[0]
        print(f"Total events: {total_events}")
        
        if total_events == 0:
            print("No events found. Can't analyze.")
            return

        # 2. Event Types
        cursor.execute("SELECT type, COUNT(*) FROM events GROUP BY type")
        types = cursor.fetchall()
        print("\nEvent Types:")
        for t, count in types:
            print(f"  {t}: {count}")
            
        # 3. Tool Usage
        cursor.execute("SELECT data FROM events WHERE type='tool_use'")
        tool_rows = cursor.fetchall()
        
        tool_counts = Counter()
        errors = Counter()
        durations = {} # tool -> list of durations
        
        for row in tool_rows:
            try:
                data = json.loads(row[0])
                tool_name = data.get('tool_name')
                success = data.get('success')
                duration = data.get('duration_ms', 0)
                error_cat = data.get('error_category')
                
                tool_counts[tool_name] += 1
                
                if tool_name not in durations:
                    durations[tool_name] = []
                durations[tool_name].append(duration)
                
                if tool_name == 'search_codebase' and 'args' in data:
                     # Attempt to extract query from args or kwargs
                     query = None
                     if data.get('kwargs') and 'query' in data['kwargs']:
                         query = data['kwargs']['query']
                     elif data.get('args') and len(data['args']) > 0:
                         query = data['args'][0]
                     
                     if query:
                         print(f"  Search Query: {query}")

                if not success:
                    errors[f"{tool_name}: {error_cat}"] += 1
            except Exception as e:
                pass
                
        print("\nTool Usage (Top 10):")
        for tool, count in tool_counts.most_common(10):
            avg_dur = sum(durations[tool]) / len(durations[tool]) if durations[tool] else 0
            print(f"  {tool}: {count} calls (Avg: {avg_dur:.2f}ms)")
            
        print("\nCommon Errors:")
        if not errors:
            print("  No errors recorded.")
        else:
            for err, count in errors.most_common(5):
                print(f"  {err}: {count}")

        conn.close()
        
    except Exception as e:
        print(f"Error reading database: {e}")

if __name__ == "__main__":
    analyze_telemetry()
