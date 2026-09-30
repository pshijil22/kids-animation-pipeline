# Kids Animation Pipeline

Automated 25–30 minute **free, registration-free animated-movie pipeline**.

Pipeline:
Push to main -> GitHub Actions -> local Ollama story generation -> offline eSpeak NG narration -> Blender Eevee 3D animation -> FFmpeg 1080p MP4 -> quality checks -> downloadable artifact.

## Cost and registration

The production path does **not** require Runway, OpenAI, ElevenLabs, YouTube OAuth, a paid API key, or any other paid AI/video registration.

- GitHub Actions runs the workflow automatically on pushes to `main`. Public repositories can use standard GitHub-hosted runners without Actions minute charges. citeturn0search3turn0search9
- Ollama runs the story model locally in the workflow; local models do not require a cloud API key. citeturn0search0turn0search5
- Blender is open-source and renders the movie locally in background mode with Eevee. Blender documents command-line/background rendering for automated jobs. citeturn1search0turn1search2turn2search0
- eSpeak NG is an open-source offline TTS engine. It can write WAV audio directly and does not require an account. citeturn3search0

There is an important quality tradeoff: removing paid generative-video APIs means the visuals are **procedurally generated 3D animation**, not cloud text-to-video generation. The pipeline still produces a real 3D animated movie with story-driven characters, props, camera movement, lighting and continuity, but it cannot honestly promise the photoreal/feature-film generation quality of a paid foundation video model.

## Production renderer

The renderer uses Blender Eevee to build an original stylized 3D world directly from the story JSON. Scene fields such as location, action, character actions, props, emotion and camera direction affect the generated movie. Blender runs headlessly, so no desktop or manual step is needed. citeturn1search0turn2search0

No Runway secret is needed. `RUNWAYML_API_SECRET` has been removed from the workflow.

## Current production files

- `.github/workflows/test.yml`
- `prompts/story.txt`
- `worker/pipeline.py`
- `worker/story.py`
- `worker/tts.py`
- `worker/generative_video.py`
- `worker/youtube.py`
- `worker/requirements.txt`
- `.env.example`

The obsolete cloud-video renderer is gone. Generated files under `data/` are ignored by Git.

## Output

- 100 story scenes
- 25–30 minutes
- 1920x1080 delivery
- 30 FPS delivery
- H.264/AAC MP4
- offline narration
- subtitles
- story-driven 3D animation
- automatic GitHub Actions artifact
- YouTube upload remains OFF

Every push to `main` automatically runs the full production pipeline; there is no manual workflow trigger.
