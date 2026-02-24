#!/usr/bin/env python3
"""
Docker Cleanup Utility for Swarm MCP

Prunes dangling Docker images, containers, and build cache.
Provides detailed reporting of space savings.
"""

import argparse
import subprocess
import sys
from typing import Dict, List


def run_command(cmd: List[str], capture_output: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True,
            check=False
        )
        return result
    except Exception as e:
        print(f"❌ Command failed: {' '.join(cmd)}", file=sys.stderr)
        print(f"   Error: {e}", file=sys.stderr)
        sys.exit(1)


def get_docker_disk_usage() -> Dict[str, str]:
    """Get current Docker disk usage."""
    result = run_command(['docker', 'system', 'df'])
    if result.returncode != 0:
        print("❌ Failed to get Docker disk usage", file=sys.stderr)
        return {}
    
    print("\n📊 Current Docker Disk Usage:")
    print("=" * 60)
    print(result.stdout)
    return {}


def prune_docker(dry_run: bool = True, aggressive: bool = False):
    """
    Prune Docker system to remove unused data.
    
    Args:
        dry_run: If True, only show what would be deleted
        aggressive: If True, remove all unused images (not just dangling)
    """
    print("\n🐳 Docker Cleanup Utility")
    print("=" * 60)
    
    if dry_run:
        print("🔍 DRY RUN MODE - showing what would be removed\n")
    else:
        print("🗑️  EXECUTING cleanup\n")
    
    # Get current usage
    get_docker_disk_usage()
    
    # Prune containers
    print("\n1️⃣  Pruning stopped containers...")
    cmd = ['docker', 'container', 'prune', '--force']
    if dry_run:
        # Check for stopped containers
        result = run_command(['docker', 'ps', '-a', '--filter', 'status=exited', '--format', '{{.ID}} {{.Names}} {{.Status}}'])
        if result.stdout.strip():
            print(f"   Would remove:\n{result.stdout}")
        else:
            print("   No stopped containers to remove")
    else:
        result = run_command(cmd)
        print(f"   {result.stdout}")
    
    # Prune dangling images
    print("\n2️⃣  Pruning dangling images (<none>:<none>)...")
    cmd = ['docker', 'image', 'prune', '--force']
    if dry_run:
        result = run_command(['docker', 'images', '--filter', 'dangling=true', '--format', '{{.ID}} {{.Repository}}:{{.Tag}} {{.Size}}'])
        if result.stdout.strip():
            print(f"   Would remove:\n{result.stdout}")
        else:
            print("   No dangling images to remove")
    else:
        result = run_command(cmd)
        print(f"   {result.stdout}")
    
    # Prune all unused images (if aggressive)
    if aggressive:
        print("\n3️⃣  Pruning ALL unused images...")
        cmd = ['docker', 'image', 'prune', '--all', '--force']
        if dry_run:
            result = run_command(['docker', 'images', '--format', '{{.ID}} {{.Repository}}:{{.Tag}} {{.Size}}'])
            print(f"   Would remove unused images from:\n{result.stdout}")
        else:
            result = run_command(cmd)
            print(f"   {result.stdout}")
    
    # Prune build cache
    print("\n4️⃣  Pruning build cache...")
    cmd = ['docker', 'builder', 'prune', '--force']
    if dry_run:
        result = run_command(['docker', 'system', 'df'])
        print("   Build cache would be cleared")
    else:
        result = run_command(cmd)
        print(f"   {result.stdout}")
    
    # Prune volumes (optional)
    print("\n5️⃣  Checking for unused volumes...")
    cmd = ['docker', 'volume', 'ls', '--filter', 'dangling=true', '--format', '{{.Name}}']
    result = run_command(cmd)
    if result.stdout.strip():
        print(f"   ⚠️  Found dangling volumes: {result.stdout.strip()}")
        print("   Run 'docker volume prune' manually if you want to remove them")
    else:
        print("   No dangling volumes found")
    
    # Final disk usage
    if not dry_run:
        print("\n" + "=" * 60)
        get_docker_disk_usage()
        print("\n✅ Docker cleanup complete!")
    else:
        print("\n💡 Run with --execute to actually perform cleanup")
        print("💡 Add --aggressive to remove ALL unused images (not just dangling)")


def main():
    parser = argparse.ArgumentParser(
        description="Docker cleanup utility - removes dangling images, containers, and build cache"
    )
    parser.add_argument(
        '--execute',
        action='store_true',
        help='Actually perform cleanup (default is dry-run)'
    )
    parser.add_argument(
        '--aggressive',
        action='store_true',
        help='Remove ALL unused images, not just dangling ones'
    )
    
    args = parser.parse_args()
    
    prune_docker(dry_run=not args.execute, aggressive=args.aggressive)


if __name__ == '__main__':
    main()
