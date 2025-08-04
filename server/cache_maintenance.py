#!/usr/bin/env python3
"""
Cache maintenance utility for Yandex Cloud caching system
Provides tools for cache cleanup, optimization, and monitoring
"""

import argparse
import json
import sys
import time
from datetime import datetime
from typing import Dict, Any

def get_cache_stats():
    """Get detailed cache statistics"""
    try:
        from yandex_cache import get_cache
        cache = get_cache()
        return cache.get_stats()
    except Exception as e:
        print(f"Error getting cache stats: {e}")
        return None

def cleanup_expired():
    """Clean up expired cache entries"""
    try:
        from yandex_cache import get_cache
        cache = get_cache()
        
        print("Starting expired cache cleanup...")
        start_time = time.time()
        
        cleaned_count = cache.cleanup_expired()
        duration = time.time() - start_time
        
        print(f"✅ Cleaned up {cleaned_count} expired entries in {duration:.2f}s")
        return cleaned_count
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        return 0

def optimize_cache():
    """Optimize cache (cleanup + defragmentation)"""
    try:
        from yandex_cache import get_cache
        cache = get_cache()
        
        print("Starting cache optimization...")
        result = cache.optimize()
        
        print("✅ Cache optimization completed:")
        print(f"   Duration: {result['duration_seconds']}s")
        print(f"   Expired cleaned: {result['expired_cleaned']}")
        print(f"   Size: {result['initial_size_mb']}MB → {result['final_size_mb']}MB")
        print(f"   Space freed: {result['space_freed_mb']}MB")
        print(f"   Entries: {result['initial_entries']} → {result['final_entries']}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error during optimization: {e}")
        return None

def clear_cache_by_type(cache_type: str):
    """Clear cache entries by type"""
    try:
        from yandex_cache import get_cache
        cache = get_cache()
        
        print(f"Clearing cache type: {cache_type}")
        deleted_count = cache.clear_by_type(cache_type)
        
        print(f"✅ Cleared {deleted_count} entries of type '{cache_type}'")
        return deleted_count
        
    except Exception as e:
        print(f"❌ Error clearing cache type {cache_type}: {e}")
        return 0

def clear_all_cache():
    """Clear all cache entries"""
    try:
        from yandex_cache import get_cache
        cache = get_cache()
        
        print("⚠️  Clearing ALL cache entries...")
        response = input("Are you sure? This cannot be undone (y/N): ")
        
        if response.lower() != 'y':
            print("Operation cancelled")
            return 0
        
        deleted_count = cache.clear_all()
        print(f"✅ Cleared all {deleted_count} cache entries")
        return deleted_count
        
    except Exception as e:
        print(f"❌ Error clearing all cache: {e}")
        return 0

def show_cache_stats():
    """Display detailed cache statistics"""
    stats = get_cache_stats()
    
    if not stats:
        print("❌ Unable to get cache statistics")
        return
    
    print("\n" + "="*60)
    print("CACHE STATISTICS")
    print("="*60)
    
    print(f"📁 Cache Directory: {stats['cache_dir']}")
    print(f"📊 Total Entries: {stats['total_entries']}")
    print(f"💾 Total Size: {stats['total_size_mb']} MB ({stats['total_size_bytes']} bytes)")
    print(f"🎯 Max Size: {stats['max_size_mb']} MB")
    print(f"📈 Usage: {stats['usage_percent']:.1f}%")
    print(f"⏰ Expired Entries: {stats['expired_entries']}")
    
    print(f"\n📋 TTL Settings:")
    for cache_type, ttl_seconds in stats['ttl_settings'].items():
        hours = ttl_seconds / 3600
        print(f"   {cache_type}: {hours:.1f} hours ({ttl_seconds}s)")
    
    if stats['types_stats']:
        print(f"\n📊 By Type:")
        for cache_type, type_stats in stats['types_stats'].items():
            size_mb = type_stats['size'] / (1024 * 1024)
            print(f"   {cache_type}: {type_stats['count']} entries, {size_mb:.2f} MB")
    
    print("="*60)

def monitor_cache(interval: int = 60):
    """Monitor cache statistics in real-time"""
    print(f"🔍 Monitoring cache every {interval} seconds (Ctrl+C to stop)")
    
    try:
        while True:
            stats = get_cache_stats()
            if stats:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"[{timestamp}] Entries: {stats['total_entries']}, "
                      f"Size: {stats['total_size_mb']:.1f}MB, "
                      f"Usage: {stats['usage_percent']:.1f}%, "
                      f"Expired: {stats['expired_entries']}")
            else:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Unable to get stats")
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n👋 Monitoring stopped")

def export_cache_stats(output_file: str):
    """Export cache statistics to JSON file"""
    try:
        stats = get_cache_stats()
        if not stats:
            print("❌ Unable to get cache statistics")
            return False
        
        # Add timestamp
        stats['exported_at'] = datetime.now().isoformat()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Cache statistics exported to {output_file}")
        return True
        
    except Exception as e:
        print(f"❌ Error exporting stats: {e}")
        return False

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description="Yandex Cloud Cache Maintenance Utility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s stats                    # Show cache statistics
  %(prog)s cleanup                  # Clean expired entries
  %(prog)s optimize                 # Full cache optimization
  %(prog)s clear --type embedding   # Clear embedding cache
  %(prog)s clear --all              # Clear all cache (with confirmation)
  %(prog)s monitor --interval 30    # Monitor cache every 30 seconds
  %(prog)s export stats.json        # Export stats to JSON file
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Stats command
    subparsers.add_parser('stats', help='Show cache statistics')
    
    # Cleanup command
    subparsers.add_parser('cleanup', help='Clean up expired cache entries')
    
    # Optimize command
    subparsers.add_parser('optimize', help='Optimize cache (cleanup + defragmentation)')
    
    # Clear command
    clear_parser = subparsers.add_parser('clear', help='Clear cache entries')
    clear_group = clear_parser.add_mutually_exclusive_group(required=True)
    clear_group.add_argument('--type', choices=['embedding', 'llm_response', 'auth_token', 'document'],
                           help='Clear entries of specific type')
    clear_group.add_argument('--all', action='store_true', help='Clear all cache entries')
    
    # Monitor command
    monitor_parser = subparsers.add_parser('monitor', help='Monitor cache in real-time')
    monitor_parser.add_argument('--interval', type=int, default=60,
                              help='Monitoring interval in seconds (default: 60)')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export cache statistics to JSON')
    export_parser.add_argument('output_file', help='Output JSON file path')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Execute commands
    try:
        if args.command == 'stats':
            show_cache_stats()
            
        elif args.command == 'cleanup':
            cleanup_expired()
            
        elif args.command == 'optimize':
            optimize_cache()
            
        elif args.command == 'clear':
            if args.all:
                clear_all_cache()
            else:
                clear_cache_by_type(args.type)
                
        elif args.command == 'monitor':
            monitor_cache(args.interval)
            
        elif args.command == 'export':
            if not export_cache_stats(args.output_file):
                return 1
        
        return 0
        
    except KeyboardInterrupt:
        print("\n👋 Operation interrupted")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())