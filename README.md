# Kids Animation Pipeline

Automated 25–30 minute kids-animation episode production.

## Pipeline

```
Push to main
  -> GitHub Actions
  -> Ollama story generation (100 scenes)
  -> Neural narration (Edge TTS)
  -> Layered 2D scene rendering
  -> Character motion + camera movement
  -> FFmpeg 1080p H.264/AAC episode
  -> duration/resolution/audio quality checks
  -> downloadable GitHub Actions artifact
```

Every push to `main` runs the production pipeline automatically. There is no manual workflow trigger.

## Current production files

```
.github/workflows/test.yml   # automated build
prompts/story.txt            # story-generation prompt
worker/pipeline.py            # orchestration
worker/story.py               # 100-scene story generation
worker/tts.py                 # neural narration
worker/blender_animation.py   # layered 2D animation + cinematic rendering
worker/youtube.py             # optional YouTube publishing
worker/requirements.txt       # runtime dependencies
.env.example                  # local configuration template
```

Generated files under `data/` are ignored by Git.

## Episode target

- 100 scenes / 5 acts
- 25–30 minutes
- 1920×1080
- 30 FPS
- H.264 video + AAC audio
- Neural English narration
- Cinematic camera movement, character-layer motion, grading, grain and vignette
- Original, child-safe stories

## YouTube

YouTube upload is **disabled by default**. The build only creates the episode artifact until publishing is explicitly enabled through GitHub repository secrets.

## Development

The repository intentionally keeps one production path: `main` + GitHub Actions. Legacy Docker/FastAPI/manual-generation files are not part of the production pipeline.

For a build failure, inspect the failed GitHub Actions run and fix the source on `main`; the next push automatically starts a fresh build.
