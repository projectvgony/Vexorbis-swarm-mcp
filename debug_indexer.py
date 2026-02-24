
import os
import logging
from pathlib import Path
from mcp_core.search_engine import CodebaseIndexer, IndexConfig

# Configure logging to stdout
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_scan():
    print("🔍 Debugging CodebaseIndexer scan_files...")
    root = "."
    print(f"📂 Root Path: {os.path.abspath(root)}")
    
    config = IndexConfig(root_path=root)
    print(f"🚫 Exclude Patterns: {config.exclude_patterns}")
    print(f"📄 Extensions: {config.extensions}")
    
    indexer = CodebaseIndexer(config)
    
    # 1. Manual Walk with logging
    print("\n--- Manual Walk Debug ---")
    files_found = 0
    files_excluded = 0
    
    ext_set = set(config.extensions)
    
    for dirpath, dirnames, filenames in os.walk(root):
        # Check directory exclusions
        # Note: Indexer logic modifies dirnames in-place
        original_dirs = list(dirnames)
        
        # Simulate Indexer Pruning
        dirnames[:] = [
            d for d in dirnames 
            if not any(excl in os.path.join(dirpath, d) for excl in config.exclude_patterns)
            and not any(excl in d for excl in config.exclude_patterns)
        ]
        
        pruned = set(original_dirs) - set(dirnames)
        if pruned:
            print(f"✂️  Pruned dirs in {dirpath}: {pruned}")
            
        for f in filenames:
            _, ext = os.path.splitext(f)
            if ext in ext_set:
                file_path = Path(dirpath) / f
                # Check file exclusions
                if any(excl in str(file_path) for excl in config.exclude_patterns):
                    print(f"❌ Excluded file: {file_path}")
                    files_excluded += 1
                    continue
                
                # print(f"✅ Found: {file_path}")
                files_found += 1
            else:
                # print(f"⚪ Skipped ext: {f}")
                pass
                
    print(f"\n📊 Total Files Found: {files_found}")
    print(f"🗑️  Total Files Excluded: {files_excluded}")

    # 2. Run Indexer.scan_files
    print("\n--- Indexer.scan_files() ---")
    scanned = indexer.scan_files()
    print(f"✅ Indexer returned {len(scanned)} files.")

if __name__ == "__main__":
    debug_scan()
