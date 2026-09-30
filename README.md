# Kids Animation Pipeline

Automated 25–30 minute generative animated-movie production.

Pipeline:
Push to main -> GitHub Actions -> Ollama story generation -> neural narration -> generative cinematic video shots -> continuity-aware shot generation -> FFmpeg movie assembly -> 1080p H.264/AAC -> duration/resolution/audio QC -> artifact.

## Production renderer

The production renderer uses a generative video model rather than procedural 2D drawings. Each scene is written as a film shot with location, time, character actions, props, emotion, camera direction and continuity. The generated movie keeps the same character/world bible in every prompt and feeds the previous shot's final frame into the next shot as a continuity anchor.

The current provider is Runway Dev's WAN 3.0 (wan3) at 720p, then the finished movie is delivered at 1920x1080. WAN 3.0 supports reference-driven video generation and 2–30 second shots.

### Required GitHub secret

Add RUNWAYML_API_SECRET to the repository's GitHub Actions secrets. Do not put the API key in source code or .env files.

Every push to main runs automatically. No manual workflow trigger.

Current production files:
- .github/workflows/test.yml
- prompts/story.txt
- worker/pipeline.py
- worker/story.py
- worker/tts.py
- worker/generative_video.py
- worker/youtube.py
- worker/requirements.txt
- .env.example

The old procedural worker/blender_animation.py renderer has been removed.

Generated files under data/ are ignored by Git.

Episode target: 100 story scenes, 25–30 minutes, 1920x1080 delivery, 30 FPS, H.264/AAC, neural English narration, cinematic generated animation, scene continuity, expressive character motion, story-driven camera work and original child-safe stories.

YouTube upload is disabled by default.
