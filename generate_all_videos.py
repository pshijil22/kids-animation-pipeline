#!/usr/bin/env python3
"""
Complete video generation script for GitHub Actions
Generates videos and saves them to data/ directory
"""
import asyncio
import json
import datetime
import sys
import os
from pathlib import Path

# Work from repo root
repo_root = Path.cwd()
worker_dir = repo_root / 'worker'
data_dir = repo_root / 'data'

# Set DATA_DIR env var BEFORE importing modules
os.environ['DATA_DIR'] = str(data_dir)

# Change to worker directory for imports
os.chdir(worker_dir)
sys.path.insert(0, str(worker_dir))

from pipeline import generate_story

async def main():
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    
    # Ensure data directories exist in repo root
    (data_dir / 'stories').mkdir(parents=True, exist_ok=True)
    (data_dir / 'audio').mkdir(parents=True, exist_ok=True)
    (data_dir / 'scenes').mkdir(parents=True, exist_ok=True)
    (data_dir / 'videos').mkdir(parents=True, exist_ok=True)
    
    for i in range(1, count + 1):
        print(f"\n{'='*60}")
        print(f"Generating video {i} of {count}...")
        print('='*60)
        
        try:
            result = await generate_story()
            
            log = {
                'batch': str(i),
                'timestamp': datetime.datetime.now().isoformat(),
                'status': 'success',
                'job_id': result.get('job_id'),
                'title': result.get('title'),
                'video_file': result.get('video_file'),
                'duration': result.get('total_duration')
            }
            
            print(f'\n✅ Video {i} generated!')
            print(json.dumps(log, indent=2))
            
            # Verify file exists
            video_path = Path(result.get('video_file'))
            if video_path.exists():
                size_mb = video_path.stat().st_size / 1024 / 1024
                print(f"✅ Video saved: {video_path} ({size_mb:.1f} MB)")
            else:
                print(f"⚠️  Video file not found: {video_path}")
            
            if i < count:
                print(f"\nWaiting 30 seconds before next generation...")
                await asyncio.sleep(30)
            
        except Exception as e:
            print(f'\n❌ Generation {i} failed: {e}')
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    # Final summary
    print(f"\n{'='*60}")
    print(f"✅ All {count} video(s) generated successfully!")
    print('='*60)
    
    # List generated files from repo root data dir
    videos = list((data_dir / 'videos').glob('*.mp4'))
    print(f"\nGenerated {len(videos)} MP4 file(s) in {data_dir / 'videos'}:")
    for v in sorted(videos):
        size_mb = v.stat().st_size / 1024 / 1024
        print(f"  - {v.name} ({size_mb:.1f} MB)")
    
    if not videos:
        print("\n⚠️  No videos found! Check paths above.")

if __name__ == '__main__':
    asyncio.run(main())
