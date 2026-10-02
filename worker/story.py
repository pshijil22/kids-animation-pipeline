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
SCENES_PER_BATCH = 10
PREVIEW = os.getenv("CINEMATIC_PREVIEW", "true").lower() == "true"
PREVIEW_SCENES = int(os.getenv("CINEMATIC_PREVIEW_SCENES", "6"))


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


async def _ask_ollama(prompt, timeout=900):
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

    total_scenes = PREVIEW_SCENES if PREVIEW else 100
    acts_to_generate = 1 if PREVIEW else 5
    batches_per_act = 1 if PREVIEW else 2
    for act in range(1, acts_to_generate + 1):
        for batch in range(batches_per_act):
            batch_size = min(SCENES_PER_BATCH, total_scenes - len(scenes))
            if batch_size <= 0:
                break
            start_number = len(scenes) + 1
            recent = scenes[-3:] if scenes else []
            context = json.dumps(
                {"characters": characters, "recent_scenes": recent, "next_act": act},
                ensure_ascii=False,
            )
            prompt = f"""
{base}

You are generating ACT {act} of 5, BATCH {batch + 1} of 2.
Generate EXACTLY {batch_size} scenes in this batch.
This run must contain {total_scenes} scenes.
This batch covers scene numbers {start_number} through {start_number + batch_size - 1}.

Continuity context from earlier scenes:
{context}

For ACT 1, BATCH 1, create the title, description, lesson, age_range, characters and acts.
For all other batches, keep the same characters, setting, story premise and lesson.
Do not rename characters or change their appearance.

Each scene must contain 38-45 natural spoken words, a concrete visible action,
and useful visual details. The scene duration target is about 15-18 seconds.
Return ONLY valid JSON.

For ACT 1, BATCH 1 return:
{{
  "title":"...",
  "description":"...",
  "lesson":"...",
  "age_range":"4-8",
  "target_duration_seconds":1650,
  "duration_seconds":1650,
  "characters":[{{"name":"...","species":"...","appearance":"...","personality":"..."}}],
  "acts":[{{"number":1,"title":"..."}},{{"number":2,"title":"..."}},{{"number":3,"title":"..."}},{{"number":4,"title":"..."}},{{"number":5,"title":"..."}}],
  "scenes":[{{"number":{start_number},"act":{act},"title":"...","narration":"...","visual_description":"...","visual_beats":[{{"narration_line":"...","subject":"...","action":"...","prop":"...","camera":"..."}},{{"narration_line":"...","subject":"...","action":"...","prop":"...","camera":"..."}},{{"narration_line":"...","subject":"...","action":"...","prop":"...","camera":"..."}}],"location":"...","time_of_day":"...","action":"...","character_actions":"...","props":"...","emotion":"...","camera":"...","motion":"...","continuity":"...","duration_seconds":16}}]
}}

For every other batch return:
{{
  "scenes":[{{"number":{start_number},"act":{act},"title":"...","narration":"...","visual_description":"...","location":"...","time_of_day":"...","action":"...","character_actions":"...","props":"...","emotion":"...","camera":"...","motion":"...","continuity":"...","duration_seconds":16}}]
}}
"""
            logger.info("Generating story act %s/5 batch %s/2...", act, batch + 1)

            # LLMs can occasionally return valid JSON with an empty/short scenes
            # array. Retry the same batch with a progressively stricter instruction
            # instead of throwing away the entire 25-30 minute production.
            result = None
            act_scenes = []
            for attempt in range(1, 4):
                retry_prompt = prompt
                if attempt > 1:
                    retry_prompt += f"""
IMPORTANT RETRY {attempt}/3:
Your previous response did not contain {batch_size} usable scenes.
Return ONLY a JSON object with a "scenes" array containing EXACTLY
{batch_size} complete scene objects for this batch. Do not return an
empty array. Do not summarize. Do not omit any scene.
"""
                try:
                    result = await _ask_ollama(retry_prompt)
                    act_scenes = result.get("scenes", []) if isinstance(result, dict) else []
                    if len(act_scenes) >= batch_size:
                        break
                    logger.warning(
                        "Act %s batch %s attempt %s returned %s scenes; retrying",
                        act, batch + 1, attempt, len(act_scenes)
                    )
                except (ValueError, requests.RequestException) as exc:
                    logger.warning(
                        "Act %s batch %s attempt %s failed: %s; retrying",
                        act, batch + 1, attempt, exc
                    )
                    if attempt == 3:
                        raise

            if len(act_scenes) < SCENES_PER_BATCH:
                raise ValueError(
                    f"Act {act} batch {batch + 1} must contain at least "
                    f"{batch_size} scenes after 3 attempts; received {len(act_scenes)}"
                )
            act_scenes = act_scenes[:batch_size]
            for offset, scene in enumerate(act_scenes):
                if isinstance(scene, dict):
                    scene["number"] = start_number + offset
                    scene["act"] = act
            if act == 1 and batch == 0:
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
    expected_scenes = PREVIEW_SCENES if PREVIEW else 100
    if len(story["scenes"]) != expected_scenes:
        raise ValueError(f"Story needs exactly {expected_scenes} scenes for this run; received {len(story['scenes'])}")

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
        scene.setdefault("visual_description", "A cinematic 3D animated-feature scene with the recurring characters.")
        beats = scene.get("visual_beats")
        if not isinstance(beats, list) or len(beats) < 3:
            narration = str(scene.get("narration", "")).strip()
            parts = [p.strip() for p in re.split(r"(?<=[.!?])\\s+", narration) if p.strip()]
            while len(parts) < 3:
                parts.append(narration)
            base_subject = scene.get("character_actions", "") or "the main character"
            base_action = scene.get("action", "") or "moves through the scene"
            base_prop = scene.get("props", "") or ""
            beats = [
                {"narration_line": parts[0], "subject": base_subject, "action": "sets up the situation: " + base_action, "prop": base_prop, "camera": "establishing shot"},
                {"narration_line": parts[1], "subject": base_subject, "action": base_action, "prop": base_prop, "camera": "action medium shot"},
                {"narration_line": parts[2], "subject": base_subject, "action": "reacts and completes the moment: " + base_action, "prop": base_prop, "camera": "close reaction shot"},
            ]
        scene["visual_beats"] = beats[:3]
        scene.setdefault("location", "the established story world")
        scene.setdefault("time_of_day", "day")
        scene.setdefault("action", "The characters move together and discover something new.")
        scene.setdefault("character_actions", scene.get("action", "The characters move together."))
        scene.setdefault("props", "")
        scene.setdefault("emotion", "curious")
        scene.setdefault("camera", "medium shot")
        scene.setdefault("motion", "gentle camera movement")
        scene.setdefault("continuity", "Continue naturally from the previous shot.")
        scene["duration_seconds"] = max(8, min(24, float(scene.get("duration_seconds", 16))))
        normalized.append(scene)
    story["scenes"] = normalized
    return story
