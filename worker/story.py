"""Long-form story generation for the kids animation pipeline.

Generate the complete 100-scene episode in small, coherent batches so the
local LLM does not time out while preserving the full 25-30 minute plan.
"""
import asyncio
import json
import logging
import os
import re
from pathlib import Path

import requests

logger = logging.getLogger(__name__)
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
MIN_SECONDS = 1140
MAX_SECONDS = 1260
SCENES_PER_ACT = 16
SCENES_PER_BATCH = 5


async def wait_for_ollama(max_retries=180, delay=1):
    for attempt in range(max_retries):
        try:
            if requests.get(f"{OLLAMA_URL}/api/tags", timeout=3).status_code == 200:
                return True
        except Exception:
            pass
        if attempt < max_retries - 1:
            await asyncio.sleep(delay)
    raise RuntimeError(f"Ollama not responding at {OLLAMA_URL}")


def _series_bible():
    for path in (Path("../series/series.json"), Path("series/series.json")):
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception as exc:
                logger.warning("Could not load series bible: %s", exc)
    return {}


def _prompt_file():
    paths = [
        Path("/app/prompts/story.txt"),
        Path("./prompts/story.txt"),
        Path("../prompts/story.txt"),
    ]
    path = next((p for p in paths if p.exists()), None)
    if not path:
        raise FileNotFoundError(f"Prompt file not found: {paths}")
    return path


def _extract_json(raw):
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            raise ValueError("Could not parse valid JSON from LLM output")
        return json.loads(match.group(0))


async def _ask_ollama(prompt, timeout=600):
    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "num_ctx": 8192,
                "num_predict": 6000,
                "temperature": 0.7,
            },
        },
        timeout=timeout,
    )
    response.raise_for_status()
    text = response.json().get("response", "").strip()
    if not text:
        raise ValueError("Ollama returned an empty response")
    return _extract_json(text)


def _scene_schema(start_number, batch_size, include_episode):
    episode = ""
    if include_episode:
        episode = """
For the first batch also return title, description, lesson, age_range,
characters and the five acts. Characters must be reusable and visually
specific so the Blender renderer can keep them consistent.
"""
    return f"""
Return ONLY valid JSON.
{episode}
Return a "scenes" array containing EXACTLY {batch_size} scene objects.
The scene numbers must run from {start_number} through
{start_number + batch_size - 1}.

Every scene object MUST contain:
number, act, title, narration, visual_description, visual_beats,
location, time_of_day, action, character_actions, props, emotion, camera,
motion, continuity, duration_seconds.

visual_beats MUST contain EXACTLY 3 objects. Each beat MUST contain:
narration_line, subject, action, prop, camera.

The three beats must represent three different moments from the same
scene: setup, physical action/discovery, and reaction/payoff. The
narration_line must be the actual portion of narration represented.
Do not repeat the same action, camera or background for all three beats.
If narration says a character finds a key, show approaching/searching,
the key being noticed/picked up, and the character reacting to it.
If narration says a character opens a box, show reaching/opening, the
lid changing state, and the reaction to what is revealed.

Each scene's narration should be 38-45 natural spoken words. It must
advance the story rather than describe a generic picture. Every concrete
noun or action in narration should have a matching visual beat.
"""


async def generate_story_with_llm():
    await wait_for_ollama()
    base = _prompt_file().read_text(encoding="utf-8")
    series = _series_bible()
    story = None
    scenes = []
    characters = []

    total_scenes = int(os.getenv("TOTAL_SCENES", "80"))
    total_batches = (total_scenes + SCENES_PER_BATCH - 1) // SCENES_PER_BATCH

    for batch_index in range(total_batches):
        act = (batch_index // (SCENES_PER_ACT // SCENES_PER_BATCH)) + 1
        start_number = len(scenes) + 1
        batch_size = min(SCENES_PER_BATCH, total_scenes - len(scenes))
        recent = scenes[-4:] if scenes else []
        context = json.dumps(
            {
                "characters": characters,
                "recent_scenes": recent,
                "next_act": act,
                "completed_scene_count": len(scenes),
            },
            ensure_ascii=False,
        )
        include_episode = batch_index == 0
        prompt = f"""
{base}

SERIES BIBLE (maintain continuity across future episodes):
{json.dumps(series, ensure_ascii=False)}

You are generating the complete episode in ACT {act} of 5.
This is batch {batch_index + 1} of {total_batches}.
The episode MUST remain exactly {total_scenes} scenes and target approximately 20 minutes.

{_scene_schema(start_number, batch_size, include_episode)}

Continuity context from the preceding scenes:
{context}

Story requirements for this batch:
- Continue the same central problem and character goals.
- Escalate the adventure gently; do not reset the story.
- Preserve character names, species, appearance and personality.
- Preserve important props and locations when continuity requires them.
- Introduce new visible events rather than filler travel scenes.
- Act 1 establishes the hook and goal; Acts 2-4 develop discoveries,
  obstacles and teamwork; Act 5 resolves the goal and lands the lesson.
- Make every scene visually distinct and physically animatable in Blender.
- Keep all events warm, funny, adventurous and age-appropriate.
"""
        logger.info(
            "Generating story batch %s/%s (act %s, scenes %s-%s)",
            batch_index + 1,
            total_batches,
            act,
            start_number,
            start_number + batch_size - 1,
        )

        result = None
        act_scenes = []
        for attempt in range(1, 4):
            retry_prompt = prompt
            if attempt > 1:
                retry_prompt += f"""
RETRY {attempt}/3: The previous response was incomplete.
Return ONLY one JSON object with exactly {batch_size} complete scenes.
Do not summarize, omit, merge, or invent a different scene count.
Every scene must include exactly three visual_beats with concrete actions.
"""
            try:
                result = await _ask_ollama(retry_prompt)
                act_scenes = result.get("scenes", []) if isinstance(result, dict) else []
                if len(act_scenes) >= batch_size:
                    break
                logger.warning(
                    "Batch %s attempt %s returned %s scenes; retrying",
                    batch_index + 1,
                    attempt,
                    len(act_scenes),
                )
            except (ValueError, requests.RequestException) as exc:
                logger.warning(
                    "Batch %s attempt %s failed: %s; retrying",
                    batch_index + 1,
                    attempt,
                    exc,
                )
                if attempt == 3:
                    raise

        if len(act_scenes) < batch_size:
            raise ValueError(
                f"Batch {batch_index + 1} needs {batch_size} scenes; "
                f"received {len(act_scenes)}"
            )

        act_scenes = act_scenes[:batch_size]
        for offset, scene in enumerate(act_scenes):
            if isinstance(scene, dict):
                scene["number"] = start_number + offset
                scene["act"] = act

        if include_episode:
            story = {
                "title": result.get("title", "A New Adventure"),
                "description": result.get(
                    "description", "An original adventure for children."
                ),
                "lesson": result.get(
                    "lesson", "Kindness and teamwork help us solve problems."
                ),
                "age_range": result.get("age_range", "4-8"),
                "target_duration_seconds": total_scenes * 15,
                "duration_seconds": total_scenes * 15,
                "characters": result.get("characters", []) or series.get("recurring_cast", []),
                "acts": result.get("acts", []),
                "series_title": series.get("series_title", "Original Kids Adventures"),
                "episode_number": int(series.get("episode_number", 1)),
            }
            characters = story["characters"]

        scenes.extend(act_scenes)

    if story is None or len(scenes) != total_scenes:
        raise ValueError(f"Expected {total_scenes} generated scenes, received {len(scenes)}")
    story["scenes"] = scenes
    return json.dumps(story, ensure_ascii=False)


def validate_story_json(raw_text):
    return repair_story_json(_extract_json(raw_text))


def repair_story_json(story):
    if not isinstance(story, dict):
        raise ValueError("Story must be a JSON object")
    story.setdefault("title", "Untitled Story")
    story.setdefault("description", "An original story for children")
    story.setdefault("lesson", "Kindness and teamwork help us solve problems.")
    story.setdefault("age_range", "4-8")
    story.setdefault("characters", [])
    if isinstance(story.get("characters"), dict):
        story["characters"] = list(story["characters"].values())
    story["characters"] = [c for c in story.get("characters", []) if isinstance(c, dict) and c.get("name")][:3]
    story.setdefault("acts", [])
    if not isinstance(story.get("scenes"), list) or not story["scenes"]:
        raise ValueError("Story must have a non-empty scenes array")
    if len(story["scenes"]) != int(os.getenv("TOTAL_SCENES", "80")):
        raise ValueError(
            f"Story needs exactly {int(os.getenv('TOTAL_SCENES', '80'))} scenes for the full episode; "
            f"received {len(story['scenes'])}"
        )

    story["duration_seconds"] = max(
        MIN_SECONDS, min(MAX_SECONDS, int(story.get("duration_seconds", 1200)))
    )
    story["target_duration_seconds"] = max(
        MIN_SECONDS, min(MAX_SECONDS, int(story.get("target_duration_seconds", 1200)))
    )

    normalized = []
    for i, scene in enumerate(story["scenes"], 1):
        if not isinstance(scene, dict):
            scene = {}
        scene["number"] = i
        scene.setdefault("act", ((i - 1) // SCENES_PER_ACT) + 1)
        scene.setdefault("title", f"Scene {i}")
        scene.setdefault(
            "narration",
            "The adventure continues as everyone works together.",
        )
        scene.setdefault(
            "visual_description",
            "A cinematic 3D animated-feature scene with the recurring characters.",
        )
        beats = scene.get("visual_beats")
        if not isinstance(beats, list) or len(beats) < 3:
            narration = str(scene.get("narration", "")).strip()
            parts = [
                p.strip()
                for p in re.split(r"(?<=[.!?])\s+", narration)
                if p.strip()
            ]
            while len(parts) < 3:
                parts.append(narration)
            base_subject = scene.get("character_actions", "") or "the main character"
            base_action = scene.get("action", "") or "moves through the scene"
            base_prop = scene.get("props", "") or ""
            beats = [
                {
                    "narration_line": parts[0],
                    "subject": base_subject,
                    "action": "sets up the situation: " + base_action,
                    "prop": base_prop,
                    "camera": "establishing shot",
                },
                {
                    "narration_line": parts[1],
                    "subject": base_subject,
                    "action": base_action,
                    "prop": base_prop,
                    "camera": "action medium shot",
                },
                {
                    "narration_line": parts[2],
                    "subject": base_subject,
                    "action": "reacts and completes the moment: " + base_action,
                    "prop": base_prop,
                    "camera": "close reaction shot",
                },
            ]
        scene["visual_beats"] = beats[:3]
        scene.setdefault("location", "the established story world")
        scene.setdefault("time_of_day", "day")
        scene.setdefault(
            "action",
            "The characters move together and discover something new.",
        )
        scene.setdefault(
            "character_actions",
            scene.get("action", "The characters move together."),
        )
        scene.setdefault("props", "")
        scene.setdefault("emotion", "curious")
        scene.setdefault("camera", "medium shot")
        scene.setdefault("motion", "gentle camera movement")
        scene.setdefault("continuity", "Continue naturally from the previous shot.")
        scene["duration_seconds"] = max(
            8, min(24, float(scene.get("duration_seconds", 16.5)))
        )
        normalized.append(scene)
    story["scenes"] = normalized
    return story
