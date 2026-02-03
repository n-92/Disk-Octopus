"""
Performance Profiling Script
Measures improvements from architecture optimizations
"""

import time
import os
import psutil
from pathlib import Path
from disk_scanner import DiskScanner, FileNode
from cache_manager import get_cache


def format_size(bytes_val):
    """Format bytes to human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_val < 1024:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f} TB"


def get_memory_usage():
    """Get current memory usage in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024


def profile_scan(path: str, use_cache: bool = True):
    """Profile a disk scan operation."""
    print(f"\n{'='*70}")
    print(f"Profiling scan of: {path}")
    print(f"{'='*70}")
    
    cache = get_cache()
    
    # Clear cache for fresh start
    if use_cache:
        print("Using cache (if available)")
    else:
        print("Cache disabled - fresh scan")
        cache.clear_cache(path)
    
    # Baseline memory
    mem_before = get_memory_usage()
    print(f"Memory before scan: {mem_before:.1f} MB")
    
    # Scan
    start_time = time.time()
    scanner = DiskScanner(path)
    root_node = scanner.scan()
    scan_time = time.time() - start_time
    
    # Memory after
    mem_after = get_memory_usage()
    memory_used = mem_after - mem_before
    
    print(f"\n✓ Scan completed in {scan_time:.2f}s")
    print(f"  Memory used: {memory_used:.1f} MB (total: {mem_after:.1f} MB)")
    print(f"  Total files: {scanner.total_files}")
    print(f"  Total dirs: {scanner.total_dirs}")
    print(f"  Root size: {root_node.format_size()}")
    
    # Profile extension stats (with caching)
    print(f"\nProfiling extension stats (first call - builds cache)...")
    start = time.time()
    stats1 = root_node.get_extension_stats()
    time1 = time.time() - start
    print(f"  First call: {time1*1000:.2f}ms (builds cache)")
    
    print(f"  Subsequent calls (using cache)...")
    times = []
    for _ in range(5):
        start = time.time()
        stats = root_node.get_extension_stats()
        times.append((time.time() - start) * 1000)
    
    avg_time = sum(times) / len(times)
    print(f"  Average cached lookup: {avg_time:.3f}ms")
    print(f"  Speedup: {time1/avg_time:.0f}x faster!")
    
    # Save to cache
    if use_cache:
        print(f"\nSaving scan to cache...")
        start = time.time()
        cache.save_scan(path, root_node)
        save_time = time.time() - start
        print(f"  Cache save time: {save_time*1000:.2f}ms")
    
    return {
        'scan_time': scan_time,
        'memory_used': memory_used,
        'files': scanner.total_files,
        'dirs': scanner.total_dirs,
        'stats_time': time1,
        'cached_stats_time': avg_time,
    }


def profile_cache_load(path: str):
    """Profile loading from cache."""
    print(f"\n{'='*70}")
    print(f"Profiling cache load for: {path}")
    print(f"{'='*70}")
    
    cache = get_cache()
    
    mem_before = get_memory_usage()
    
    start = time.time()
    node = cache.load_scan(path)
    load_time = time.time() - start
    
    mem_after = get_memory_usage()
    
    if node:
        print(f"✓ Cache loaded in {load_time*1000:.2f}ms")
        print(f"  Memory used: {(mem_after - mem_before):.1f} MB")
        print(f"  Files: {node.file_count}")
        print(f"  Root size: {node.format_size()}")
        return load_time
    else:
        print(f"✗ No cache found")
        return None


def main():
    """Run performance profiling."""
    print("\n" + "="*70)
    print("DISK OCTOPUS - PERFORMANCE PROFILING")
    print("="*70)
    
    # Profile different drives/directories
    test_paths = [
        "C:\\Users",  # Medium-sized directory
    ]
    
    results = {}
    
    for path in test_paths:
        if os.path.exists(path):
            # First scan
            result = profile_scan(path, use_cache=False)
            results[f"{path}_fresh"] = result
            
            # Try cache load
            cache_time = profile_cache_load(path)
            if cache_time:
                results[f"{path}_cached"] = {'cache_load_time': cache_time}
            
            # Second fresh scan (with cache enabled)
            result2 = profile_scan(path, use_cache=True)
            results[f"{path}_with_cache"] = result2
    
    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    
    if f"{test_paths[0]}_fresh" in results and f"{test_paths[0]}_with_cache" in results:
        r1 = results[f"{test_paths[0]}_fresh"]
        r2 = results[f"{test_paths[0]}_with_cache"]
        
        print(f"\nCache benefits (if available):")
        print(f"  Speedup in stats queries: {r1['stats_time']/r2['cached_stats_time']:.0f}x")
        
        if f"{test_paths[0]}_cached" in results:
            cache_load = results[f"{test_paths[0]}_cached"]['cache_load_time']
            print(f"  Cache load time: {cache_load*1000:.2f}ms")
            print(f"  Fresh scan time: {r1['scan_time']:.2f}s")
            print(f"  Cache speedup: {r1['scan_time']/(cache_load if cache_load else 1):.0f}x faster!")
    
    print(f"\n{'='*70}")
    print("Testing complete! Check ~/.disk-octopus-cache for saved cache files")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
