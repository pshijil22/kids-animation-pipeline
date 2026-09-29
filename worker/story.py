"""Long-form story generation for the kids animation pipeline.

The LLM is called in five smaller act requests instead of one giant JSON response.
This keeps output reliable while still producing a single coherent 25-30 minute episode.
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
MIN_SECONDS = 1500
MAX_SECONDS = 1800
SCENES_PER_ACT = 20


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


def _prompt_file():
    paths = [Path("/app/prompts/story.txt"), Path("./prompts/story.txt"), Path("../prompts/story.txt")]
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


async def _ask_ollama(prompt, timeout=1200):
    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"num_ctx": 16384, "temperature": 0.7},
        },
        timeout=timeout,
    )
    response.raise_for_status()
    text = response.json().get("response", "").strip()
    if not text:
        raise ValueError("Ollama returned an empty response")
    return _extract_json(text)


async def generate_story_with_llm():
    await wait_for_ollama()
    base = _prompt_file().read_text(encoding="utf-8")
    story = None
    scenes = []
    characters = []

    for act in range(1, 6):
        recent = scenes[-3:] if scenes else []
        context = json.dumps(
            {"characters": characters, "recent_scenes": recent, "next_act": act},
            ensure_ascii=False,
        )
        prompt = f"""
{base}

You are generating ACT {act} of 5.
Generate EXACTLY {SCENES_PER_ACT} scenes for this act.
The complete episode must contain 100 scenes and 25-30 minutes of narration.

Continuity context from earlier acts:
{context}

For ACT 1, create the title, description, lesson, age_range, characters and acts.
For ACTS 2-5, keep the same characters, setting, story premise and lesson.
Do not rename characters or change their appearance.

Each scene must contain 38-45 natural spoken words, a concrete visible action,
and useful visual details. The scene duration target is about 15-18 seconds.
Return ONLY valid JSON.

For ACT 1 return:
{{
  "title":"...",
  "description":"...",
  "lesson":"...",
  "age_range":"4-8",
  "target_duration_seconds":1650,
  "duration_seconds":1650,
  "characters":[{{"name":"...","species":"...","appearance":"...","personality":"..."}}],
  "acts":[{{"number":1,"title":"..."}},{{"number":2,"title":"..."}},{{"number":3,"title":"..."}},{{"number":4,"title":"..."}},{{"number":5,"title":"..."}}],
  "scenes":[{{"number":1,"act":1,"title":"...","narration":"...","visual_description":"...","action":"...","emotion":"...","camera":"...","motion":"...","duration_seconds":16}}]
}}

For later acts return:
{{
  "scenes":[{{"number":{(act-1)*SCENES_PER_ACT+1},"act":{act},"title":"...","narration":"...","visual_description":"...","action":"...","emotion":"...","camera":"...","motion":"...","duration_seconds":16}}]
}}
"""
        logger.info("Generating story act %s/5...", act)
        result = await _ask_ollama(prompt)
        act_scenes = result.get("scenes", [])
        if len(act_scenes) < SCENES_PER_ACT:
            raise ValueError(
                f"Act {act} must contain at least {SCENES_PER_ACT} scenes; received {len(act_scenes)}"
            )
        if len(act_scenes) > SCENES_PER_ACT:
            logger.warning(
                "Act %s returned %s scenes; keeping the first %s to enforce the episode's 100-scene budget.",
                act,
                len(act_scenes),
                SCENES_PER_ACT,
            )
            act_scenes = act_scenes[:SCENES_PER_ACT]
        for scene in act_scenes:
            if isinstance(scene, dict):
                scene["act"] = act
        if act == 1:
            story = {
                "title": result.get("title", "A New Adventure"),
                "description": result.get("description", "An original adventure for children."),
                "lesson": result.get("lesson", "Kindness and teamwork help us solve problems."),
                "age_range": result.get("age_range", "4-8"),
                "target_duration_seconds": 1650,
                "duration_seconds": 1650,
                "characters": result.get("characters", []),
                "acts": result.get("acts", []),
            }
            characters = story["characters"]
        scenes.extend(act_scenes)

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
    story.setdefault("acts", [])
    if not isinstance(story.get("scenes"), list) or not story["scenes"]:
        raise ValueError("Story must have a non-empty scenes array")
    if len(story["scenes"]) != 100:
        raise ValueError(f"Long-form story needs exactly 100 scenes; received {len(story['scenes'])}")

    story["duration_seconds"] = max(MIN_SECONDS, min(MAX_SECONDS, int(story.get("duration_seconds", 1650))))
    story["target_duration_seconds"] = max(MIN_SECONDS, min(MAX_SECONDS, int(story.get("target_duration_seconds", 1650))))

    normalized = []
    for i, scene in enumerate(story["scenes"], 1):
        if not isinstance(scene, dict):
            scene = {}
        scene["number"] = i
        scene.setdefault("act", ((i - 1) // SCENES_PER_ACT) + 1)
        scene.setdefault("title", f"Scene {i}")
        scene.setdefault("narration", "The adventure continues as everyone works together.")
        scene.setdefault("visual_description", "A colorful children's cartoon scene with the recurring characters.")
        scene.setdefault("action", "The characters move together and discover something new.")
        scene.setdefault("emotion", "curious")
        scene.setdefault("camera", "medium shot")
        scene.setdefault("motion", "gentle camera movement")
        scene["duration_seconds"] = max(8, min(24, float(scene.get("duration_seconds", 16))))
        normalized.append(scene)
    story["scenes"] = normalized
    return story
