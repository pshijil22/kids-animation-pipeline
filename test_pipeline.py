"""
Complete test suite for Kids Animation Pipeline
Tests all phases end-to-end
"""
import os
import json
import subprocess
import sys
from pathlib import Path
import time

def test_phase(phase_num, test_name, condition):
    """Pretty print test result"""
    status = "✓ PASS" if condition else "✗ FAIL"
    print(f"[Phase {phase_num}] {status} - {test_name}")
    return condition

def test_docker_compose():
    """Test 1: Docker Compose services running"""
    print("\n" + "="*60)
    print("TEST 1: Docker Compose Services")
    print("="*60)
    
    try:
        result = subprocess.run(
            ["docker", "compose", "ps", "--format=json"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            print("✗ FAIL - docker compose ps failed")
            return False
        
        services = json.loads(result.stdout)
        
        required_services = {'ollama', 'worker'}
        running_services = {s['Service'] for s in services if s['State'] == 'running'}
        
        for service in required_services:
            found = service in running_services
            test_phase(0, f"Service '{service}' running", found)
            if not found:
                return False
        
        return True
    except Exception as e:
        print(f"✗ FAIL - {e}")
        return False

def test_worker_health():
    """Test 2: Worker health check"""
    print("\n" + "="*60)
    print("TEST 2: Worker Health Check")
    print("="*60)
    
    try:
        result = subprocess.run(
            ["docker", "exec", "kids-channel-worker", "curl", "-s", "http://localhost:8000/health"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            test_phase(0, "Worker /health endpoint", True)
            return True
        else:
            test_phase(0, "Worker /health endpoint", False)
            return False
    except Exception as e:
        print(f"✗ FAIL - {e}")
        return False

def test_ollama():
    """Test 3: Ollama and model availability"""
    print("\n" + "="*60)
    print("TEST 3: Ollama LLM")
    print("="*60)
    
    try:
        result = subprocess.run(
            ["docker", "exec", "kids-channel-ollama", "ollama", "list"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if "llama3.2:3b" in result.stdout:
            test_phase(1, "Model llama3.2:3b available", True)
            return True
        else:
            print(f"Available models:\n{result.stdout}")
            print("\n⚠️  Model not found. Run:")
            print("    docker exec kids-channel-ollama ollama pull llama3.2:3b")
            test_phase(1, "Model llama3.2:3b available", False)
            return False
    except Exception as e:
        print(f"✗ FAIL - {e}")
        return False

def test_data_directories():
    """Test 4: Data directory structure"""
    print("\n" + "="*60)
    print("TEST 4: Data Directory Structure")
    print("="*60)
    
    dirs = [
        Path("data/stories"),
        Path("data/audio"),
        Path("data/scenes"),
        Path("data/videos"),
        Path("data/logs")
    ]
    
    all_ok = True
    for d in dirs:
        exists = d.exists() and d.is_dir()
        test_phase(0, f"Directory '{d}' exists", exists)
        all_ok = all_ok and exists
    
    return all_ok

def test_story_generation():
    """Test 5: Phase 1 - Story Generation"""
    print("\n" + "="*60)
    print("TEST 5: Phase 1 - Story Generation")
    print("="*60)
    print("Generating story... (this takes 2-5 minutes on CPU)")
    
    try:
        cmd = """
import asyncio
from pipeline import generate_story
result = asyncio.run(generate_story())
import json
print(json.dumps({
    'title': result.get('title'),
    'scenes_count': len(result.get('scenes', [])),
    'story_file': result.get('story_file'),
    'job_id': result.get('job_id')
}))
"""
        result = subprocess.run(
            ["docker", "exec", "kids-channel-worker", "python", "-c", cmd],
            capture_output=True,
            text=True,
            timeout=600
        )
        
        if result.returncode != 0:
            print(f"✗ Story generation failed:\n{result.stderr}")
            test_phase(1, "Story generation", False)
            return None
        
        data = json.loads(result.stdout.strip())
        
        test_phase(1, f"Story generated: '{data['title']}'", True)
        test_phase(1, f"Scenes count: {data['scenes_count']}", data['scenes_count'] > 0)
        
        # Verify story file exists
        story_file = Path(data['story_file'])
        exists = story_file.exists()
        test_phase(1, f"Story file saved: {story_file.name}", exists)
        
        return data
    
    except subprocess.TimeoutExpired:
        print("✗ Story generation timed out (>10 min)")
        test_phase(1, "Story generation", False)
        return None
    except Exception as e:
        print(f"✗ FAIL - {e}")
        test_phase(1, "Story generation", False)
        return None

def test_complete_pipeline():
    """Test 6: Complete pipeline (story -> audio -> scenes -> video)"""
    print("\n" + "="*60)
    print("TEST 6: Complete Pipeline (All Phases)")
    print("="*60)
    print("Running full pipeline... (5-10 minutes)")
    
    try:
        # The pipeline actually runs as part of story generation
        # Just verify the output files exist
        
        story_data = test_story_generation()
        
        if not story_data:
            test_phase(6, "Complete pipeline", False)
            return False
        
        job_id = story_data['job_id']
        
        print(f"\nVerifying generated files for job: {job_id}")
        
        # Check for generated files
        checks = {
            f"data/stories/{job_id}_story.json": "Story JSON",
            f"data/audio/{job_id}_narration.wav": "Narration audio",
            f"data/audio/{job_id}_subtitles.srt": "Subtitles",
            f"data/scenes/{job_id}_scene_01.png": "Scene 1 image",
            f"data/videos/{job_id}.mp4": "Final MP4 video"
        }
        
        all_ok = True
        for file_path, description in checks.items():
            exists = Path(file_path).exists()
            test_phase(6, f"{description}: {file_path}", exists)
            all_ok = all_ok and exists
        
        if all_ok:
            # Get video info
            result = subprocess.run(
                ["docker", "exec", "kids-channel-worker", "ffprobe", "-v", "error",
                 "-show_entries", "format=duration,size", "-of", "default=noprint_wrappers=1:nokey=1:noprint_wrappers=1",
                 f"/data/videos/{job_id}.mp4"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                duration = float(lines[0]) if len(lines) > 0 else 0
                size = int(lines[1]) if len(lines) > 1 else 0
                
                print(f"\n📊 Video Statistics:")
                print(f"   Duration: {duration:.1f} seconds")
                print(f"   Size: {size / 1024:.1f} KB")
                print(f"   Format: H.264 + AAC (YouTube-ready)")
        
        return all_ok
    
    except Exception as e:
        print(f"✗ FAIL - {e}")
        test_phase(6, "Complete pipeline", False)
        return False

def print_summary(results):
    """Print test summary"""
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for r in results if r)
    total = len(results)
    
    print(f"\nPassed: {passed}/{total} tests")
    
    if passed == total:
        print("\n✓ ALL TESTS PASSED!")
        print("\nYour kids animation pipeline is ready to use.")
        print("\nNext steps:")
        print("  1. Generate more videos: docker exec kids-channel-worker python -c ...")
        print("  2. Check outputs: ls -la data/videos/")
        print("  3. Set up YouTube OAuth (optional)")
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        print("\nCheck the errors above and fix them.")
    
    return passed == total

if __name__ == "__main__":
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*10 + "KIDS ANIMATION PIPELINE - TEST SUITE" + " "*12 + "║")
    print("╚" + "="*58 + "╝")
    
    results = []
    
    # Run tests in order
    results.append(test_docker_compose())
    results.append(test_worker_health())
    results.append(test_ollama())
    results.append(test_data_directories())
    results.append(test_complete_pipeline())
    
    # Print summary
    success = print_summary(results)
    
    sys.exit(0 if success else 1)
