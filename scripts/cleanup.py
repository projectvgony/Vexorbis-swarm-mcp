#!/usr/bin/env python3
"""
Swarm Project Cleanup Utility

Removes temporary files, caches, and build artifacts to reclaim disk space.
Provides both dry-run mode and actual cleanup with detailed reporting.
"""

import argparse
import os
import shutil
import sys
from pathlib import Path
from typing import List, Tuple


def get_directory_size(path: Path) -> int:
    """Calculate total size of directory in bytes."""
    total = 0
    try:
        for entry in path.rglob('*'):
            if entry.is_file():
                total += entry.stat().st_size
    except (PermissionError, OSError):
        pass
    return total


def format_size(bytes_size: int) -> str:
    """Format bytes into human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} TB"


def find_cleanup_targets(project_root: Path) -> List[Tuple[str, Path, int]]:
    """Find all cleanup targets and their sizes."""
    targets = []
    
    # Python caches
    for pycache in project_root.rglob('__pycache__'):
        if pycache.is_dir():
            size = get_directory_size(pycache)
            targets.append(("__pycache__", pycache, size))
    
    # .pyc files
    for pyc in project_root.rglob('*.pyc'):
        if pyc.is_file():
            targets.append((".pyc file", pyc, pyc.stat().st_size))
    
    # Test caches
    for cache_dir in ['.pytest_cache', '.mutmut-cache', '.coverage', 'htmlcov']:
        cache_path = project_root / cache_dir
        if cache_path.exists():
            size = get_directory_size(cache_path) if cache_path.is_dir() else cache_path.stat().st_size
            targets.append((cache_dir, cache_path, size))
    
    # HippoRAG cache
    hippo_cache = project_root / '.hipporag_cache'
    if hippo_cache.exists():
        size = hippo_cache.stat().st_size if hippo_cache.is_file() else get_directory_size(hippo_cache)
        targets.append((".hipporag_cache", hippo_cache, size))
    
    # Swarm cache
    swarm_cache = project_root / '.swarm-cache'
    if swarm_cache.exists():
        size = get_directory_size(swarm_cache)
        targets.append((".swarm-cache", swarm_cache, size))
    
    # Log files
    for log in project_root.rglob('*.log'):
        if log.is_file():
            targets.append(("log file", log, log.stat().st_size))
    
    # Build artifacts
    for build_dir in ['build', 'dist', '*.egg-info']:
        for item in project_root.glob(build_dir):
            if item.exists():
                size = get_directory_size(item) if item.is_dir() else item.stat().st_size
                targets.append((f"build artifact ({item.name})", item, size))
    
    return targets


def cleanup(project_root: Path, dry_run: bool = True, skip_hipporag: bool = False) -> Tuple[int, int]:
    """
    Perform cleanup operation.
    
    Returns:
        Tuple of (total_size_removed, items_removed)
    """
    targets = find_cleanup_targets(project_root)
    
    if skip_hipporag:
        targets = [(name, path, size) for name, path, size in targets if '.hipporag_cache' not in str(path)]
    
    if not targets:
        print("✅ No cleanup targets found - project is already clean!")
        return 0, 0
    
    total_size = sum(size for _, _, size in targets)
    
    print(f"\n{'🔍 DRY RUN - ' if dry_run else '🗑️  '}Cleanup Report")
    print("=" * 60)
    print(f"Found {len(targets)} cleanup targets totaling {format_size(total_size)}\n")
    
    # Group by type
    by_type = {}
    for name, path, size in targets:
        by_type.setdefault(name, []).append((path, size))
    
    for target_type, items in sorted(by_type.items()):
        type_size = sum(size for _, size in items)
        print(f"  {target_type}: {len(items)} items, {format_size(type_size)}")
        if len(items) <= 5:  # Show paths if few items
            for path, size in items:
                rel_path = path.relative_to(project_root)
                print(f"    - {rel_path} ({format_size(size)})")
    
    if dry_run:
        print("\n💡 Run with --execute to actually remove these files")
        return total_size, len(targets)
    
    # Actually perform cleanup
    removed_size = 0
    removed_count = 0
    errors = []
    
    print("\n🧹 Removing files...")
    for name, path, size in targets:
        try:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            removed_size += size
            removed_count += 1
            print(f"  ✓ Removed {path.relative_to(project_root)}")
        except Exception as e:
            errors.append((path, str(e)))
            print(f"  ✗ Failed to remove {path.relative_to(project_root)}: {e}")
    
    print(f"\n✅ Cleanup complete!")
    print(f"  Removed: {removed_count} items")
    print(f"  Space freed: {format_size(removed_size)}")
    
    if errors:
        print(f"\n⚠️  {len(errors)} errors occurred:")
        for path, error in errors:
            print(f"  - {path}: {error}")
    
    return removed_size, removed_count


def main():
    parser = argparse.ArgumentParser(
        description="Swarm project cleanup utility - removes caches and build artifacts"
    )
    parser.add_argument(
        '--execute',
        action='store_true',
        help='Actually perform cleanup (default is dry-run)'
    )
    parser.add_argument(
        '--skip-hipporag',
        action='store_true',
        help='Skip removing .hipporag_cache (it takes time to rebuild)'
    )
    parser.add_argument(
        '--project-root',
        type=Path,
        default=Path(__file__).parent.parent,
        help='Project root directory (default: parent of scripts/)'
    )
    
    args = parser.parse_args()
    
    if not args.project_root.exists():
        print(f"❌ Project root not found: {args.project_root}", file=sys.stderr)
        sys.exit(1)
    
    print(f"📂 Project root: {args.project_root}")
    
    cleanup(
        project_root=args.project_root,
        dry_run=not args.execute,
        skip_hipporag=args.skip_hipporag
    )


if __name__ == '__main__':
    main()
