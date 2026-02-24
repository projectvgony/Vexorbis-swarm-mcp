import time
import os
from pathlib import Path
from mcp_core.search_engine import CodebaseIndexer, HybridSearch, IndexConfig


def benchmark():
    root = "."
    query = "FastMCP"
    
    print(f"🚀 Benchmarking Search for: '{query}'")
    print("-" * 40)

    # 1. Setup Swarm Search
    config = IndexConfig(root_path=root)
    indexer = CodebaseIndexer(config)

    # Measure Load Time
    start_load = time.perf_counter()
    loaded = indexer.load_cache()
    end_load = time.perf_counter()

    if not loaded:
        print("❌ Cache not found. Please index first.")
        return

    searcher = HybridSearch(indexer)

    # Measure Swarm Keyword Search (Weighted)
    swarm_times = []
    for _ in range(10):
        start = time.perf_counter()
        searcher.keyword_search(query, top_k=5)
        swarm_times.append(time.perf_counter() - start)
    
    avg_swarm = sum(swarm_times) / len(swarm_times)
    print(f"✅ Swarm Keyword Search: {avg_swarm*1000:.3f}ms (Avg of 10 runs)")
    print(f"   (Loaded {len(indexer.chunks)} chunks in { (end_load - start_load)*1000:.2f}ms)")
    
    print("-" * 40)
    
    # 2. Naive Grep-like search (Python)
    grep_times = []
    for _ in range(10):
        start = time.perf_counter()
        matches = []
        for dirpath, _, filenames in os.walk(root):
            if any(x in dirpath for x in config.exclude_patterns):
                continue
            for f in filenames:
                if f.endswith(".py"):
                    p = Path(dirpath) / f
                    try:
                        content = p.read_text(encoding="utf-8", errors="ignore")
                        if query in content:
                            matches.append(p)
                    except:
                        pass
        grep_times.append(time.perf_counter() - start)
        
    avg_grep = sum(grep_times) / len(grep_times)
    print(f"✅ Naive Python Grep:  {avg_grep*1000:.3f}ms (Avg of 10 runs)")
    
    speedup = avg_grep / avg_swarm
    print("-" * 40)
    print(f"📊 Result: Swarm is {speedup:.1f}x faster than naive file scanning.")

if __name__ == "__main__":
    benchmark()
