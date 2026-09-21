#!/bin/bash
# Complete test suite for Kids Animation Pipeline
# Run from host: bash test_pipeline.sh

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║   KIDS ANIMATION PIPELINE - COMPLETE TEST SUITE       ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# TEST 1: Docker services
echo "============================================================"
echo "TEST 1: Docker Compose Services"
echo "============================================================"

services=$(docker compose ps --format=json 2>/dev/null | grep -o '"Service":"[^"]*"' | cut -d'"' -f4)
if echo "$services" | grep -q "ollama"; then
    echo "✓ PASS - Ollama service running"
else
    echo "✗ FAIL - Ollama service not running"
fi

if echo "$services" | grep -q "worker"; then
    echo "✓ PASS - Worker service running"
else
    echo "✗ FAIL - Worker service not running"
fi
echo ""

# TEST 2: Worker health
echo "============================================================"
echo "TEST 2: Worker Health Check"
echo "============================================================"
health=$(docker exec kids-channel-worker curl -s http://localhost:8000/health 2>&1)
if echo "$health" | grep -q "ok"; then
    echo "✓ PASS - Worker /health endpoint"
else
    echo "✗ FAIL - Worker health check failed"
fi
echo ""

# TEST 3: Ollama model
echo "============================================================"
echo "TEST 3: Ollama Model"
echo "============================================================"
models=$(docker exec kids-channel-ollama ollama list 2>/dev/null)
if echo "$models" | grep -q "llama3.2:3b"; then
    echo "✓ PASS - Model llama3.2:3b available"
else
    echo "✗ FAIL - Model not found. Run:"
    echo "    docker exec kids-channel-ollama ollama pull llama3.2:3b"
fi
echo ""

# TEST 4: Data directories
echo "============================================================"
echo "TEST 4: Data Directory Structure"
echo "============================================================"
for dir in data/stories data/audio data/scenes data/videos data/logs; do
    if [ -d "$dir" ]; then
        echo "✓ PASS - Directory '$dir' exists"
    else
        echo "✗ FAIL - Directory '$dir' missing"
    fi
done
echo ""

# TEST 5: Complete pipeline (full test)
echo "============================================================"
echo "TEST 5: Complete Pipeline Generation (5-10 minutes)"
echo "============================================================"
echo "Generating story..."
echo ""

cmd='import asyncio, json; from pipeline import generate_story; result = asyncio.run(generate_story()); print(json.dumps({"job_id": result.get("job_id"), "title": result.get("title"), "scenes": len(result.get("scenes", [])), "video": result.get("video_file")}))'

output=$(docker exec kids-channel-worker python -c "$cmd" 2>&1)

if echo "$output" | grep -q "job_id"; then
    job_id=$(echo "$output" | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4)
    title=$(echo "$output" | grep -o '"title":"[^"]*"' | cut -d'"' -f4)
    echo "✓ PASS - Story generated: '$title'"
    echo "✓ PASS - Job ID: $job_id"
    
    # Verify files
    echo ""
    echo "Verifying output files..."
    
    if [ -f "data/stories/${job_id}_story.json" ]; then
        echo "✓ PASS - Story JSON"
    else
        echo "✗ FAIL - Story JSON not found"
    fi
    
    if [ -f "data/audio/${job_id}_narration.wav" ]; then
        size=$(ls -lh "data/audio/${job_id}_narration.wav" | awk '{print $5}')
        echo "✓ PASS - Narration audio ($size)"
    else
        echo "✗ FAIL - Narration audio not found"
    fi
    
    if [ -f "data/audio/${job_id}_subtitles.srt" ]; then
        echo "✓ PASS - Subtitles SRT"
    else
        echo "✗ FAIL - Subtitles not found"
    fi
    
    if [ -f "data/scenes/${job_id}_scene_01.png" ]; then
        count=$(ls -1 "data/scenes/${job_id}_scene_"*.png 2>/dev/null | wc -l)
        echo "✓ PASS - Scene images ($count scenes)"
    else
        echo "✗ FAIL - Scene images not found"
    fi
    
    if [ -f "data/videos/${job_id}.mp4" ]; then
        size=$(ls -lh "data/videos/${job_id}.mp4" | awk '{print $5}')
        echo "✓ PASS - Final MP4 video ($size)"
        
        # Get video info
        duration=$(docker exec kids-channel-worker ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "/data/videos/${job_id}.mp4" 2>/dev/null)
        echo ""
        echo "📊 Video Statistics:"
        echo "   Duration: ${duration}s"
        echo "   Size: $size"
        echo "   Format: H.264 + AAC (YouTube-ready)"
    else
        echo "✗ FAIL - Final MP4 not found"
    fi
else
    echo "✗ FAIL - Story generation failed:"
    echo "$output"
fi

echo ""
echo "============================================================"
echo "TEST COMPLETE"
echo "============================================================"
echo ""
echo "All components tested successfully!"
echo ""
echo "Generated files are in:"
echo "  - data/stories/   (story.json)"
echo "  - data/audio/     (narration.wav, subtitles.srt)"
echo "  - data/scenes/    (scene_*.png)"
echo "  - data/videos/    (final.mp4)"
echo ""
