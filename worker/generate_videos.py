#!/usr/bin/env python3
"""
Helper script to generate videos for GitHub Actions
Avoids YAML quoting complexities
"""
import asyncio
import json
import datetime
import sys
from pipeline import generate_story

async def main():
    batch_num = sys.argv[1] if len(sys.argv) > 1 else "1"
    total_count = sys.argv[2] if len(sys.argv) > 2 else "1"
    
    print(f"Generating video {batch_num} of {total_count}...")
    
    try:
        result = asyncio.run(generate_story())
        
        log = {
            'batch': batch_num,
            'timestamp': datetime.datetime.now().isoformat(),
            'status': 'success',
            'job_id': result.get('job_id'),
            'title': result.get('title'),
            'video_file': result.get('video_file'),
            'duration': result.get('total_duration')
        }
        
        print(f'✅ Video {batch_num} generated!')
        print(json.dumps(log, indent=2))
        sys.exit(0)
        
    except Exception as e:
        print(f'❌ Generation {batch_num} failed: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main())
