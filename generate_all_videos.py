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

# Change to worker directory
os.chdir('worker')
sys.path.insert(0, os.getcwd())

from pipeline import generate_story

async def main():
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    
    # Ensure data directories exist
    Path("../data/stories").mkdir(parents=True, exist_ok=True)
    Path("../data/audio").mkdir(parents=True, exist_ok=True)
    Path("../data/scenes").mkdir(parents=True, exist_ok=True)
    Path("../data/videos").mkdir(parents=True, exist_ok=True)
    
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
    
    # List generated files
    videos = list(Path("../data/videos").glob("*.mp4"))
    print(f"\nGenerated {len(videos)} MP4 file(s):")
    for v in sorted(videos):
        size_mb = v.stat().st_size / 1024 / 1024
        print(f"  - {v.name} ({size_mb:.1f} MB)")

if __name__ == '__main__':
    asyncio.run(main())
