"""Automated story -> cinematic quality gate -> future full episode."""
import asyncio, json, logging, os, subprocess, shutil
from datetime import datetime
from pathlib import Path

from story import generate_story_with_llm, validate_story_json
from generative_video import generate_scenes, create_animated_video
from tts import generate_narration_from_story
from youtube import upload_to_youtube

logger=logging.getLogger(__name__)
DATA_DIR=Path(os.getenv("DATA_DIR","./data"))

def _gate_story(series):
    cast=series.get("recurring_cast",[])
    return {
        "title":"Little Wonder Trails — The Little Light",
        "description":"Pip discovers a mysterious golden light at the edge of Wonder Valley.",
        "lesson":"Curiosity is the beginning of every good adventure.",
        "age_range":"4-8","characters":cast,"series_title":series.get("series_title","Little Wonder Trails"),"episode_number":1,
        "target_duration_seconds":30,"duration_seconds":30,
        "scenes":[
            {"number":1,"act":1,"title":"Wonder Valley","duration_seconds":5,
             "narration":"Morning sunlight wakes Wonder Valley, where every ordinary path can hide a little wonder.",
             "dialogue":[],"emotion":"joyful","visual_beats":[
                 {"subject":"Wonder Valley","action":"sunlight sweeps across the village","camera":"wide establishing shot"},
                 {"subject":"Pip's cottage","action":"camera glides toward the cottage","camera":"wide tracking shot"},
                 {"subject":"Pip","action":"Pip wakes and looks toward the window","camera":"close reaction shot"}]},
            {"number":2,"act":1,"title":"Pip Wakes","duration_seconds":5,
             "narration":"Pip, a curious little bunny, pops out of bed when the birds begin singing outside.",
             "dialogue":[{"speaker":"Pip","text":"What a beautiful morning!"}],"emotion":"excited","visual_beats":[
                 {"subject":"Pip","action":"Pip sits up and stretches","camera":"medium shot"},
                 {"subject":"Pip","action":"Pip grabs his teal scarf and backpack","camera":"action medium shot"},
                 {"subject":"Pip","action":"Pip smiles and rushes toward the door","camera":"close reaction shot"}]},
            {"number":3,"act":1,"title":"Into the Garden","duration_seconds":5,
             "narration":"He races into the garden, his soft ears bouncing as warm sunlight dances across the flowers.",
             "dialogue":[],"emotion":"happy","visual_beats":[
                 {"subject":"Pip","action":"Pip runs down the garden path","camera":"wide tracking shot"},
                 {"subject":"Pip","action":"Pip slows beside the flowers","camera":"medium tracking shot"},
                 {"subject":"Pip","action":"Pip notices something glowing beyond the trees","camera":"close reaction shot"}]},
            {"number":4,"act":1,"title":"The Little Light","duration_seconds":5,
             "narration":"Then Pip sees a tiny golden light floating between the trees. He stops and watches it carefully.",
             "dialogue":[{"speaker":"Pip","text":"What's that?"}],"emotion":"curious","visual_beats":[
                 {"subject":"golden light","action":"a tiny light flickers between the trees","camera":"wide establishing shot"},
                 {"subject":"Pip","action":"Pip slowly approaches and reaches toward the light","camera":"medium tracking shot"},
                 {"subject":"Pip and light","action":"Pip freezes as the light suddenly darts away","camera":"close reaction shot"}]},
            {"number":5,"act":1,"title":"Follow Me","duration_seconds":5,
             "narration":"The mysterious light drifts deeper into the forest, almost as if it wants Pip to follow.",
             "dialogue":[{"speaker":"Pip","text":"Wait for me!"}],"emotion":"determined","visual_beats":[
                 {"subject":"golden light","action":"the light glides deeper into the forest","camera":"wide tracking shot"},
                 {"subject":"Pip","action":"Pip runs after it between the trees","camera":"low tracking shot"},
                 {"subject":"Pip","action":"Pip looks ahead with wonder and determination","camera":"close reaction shot"}]},
            {"number":6,"act":1,"title":"A New Adventure","duration_seconds":5,
             "narration":"Pip takes one brave step into the forest, never guessing that this tiny light will lead to a much bigger adventure.",
             "dialogue":[],"emotion":"brave","visual_beats":[
                 {"subject":"Pip","action":"Pip reaches the forest edge","camera":"wide establishing shot"},
                 {"subject":"Pip","action":"Pip steps beneath the trees as the light leads onward","camera":"medium tracking shot"},
                 {"subject":"Pip and forest","action":"Pip looks into the glowing forest","camera":"close reaction shot"}]}
        ]
    }

def _series_bible():
    for path in (Path("../series/series.json"),Path("series/series.json")):
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    return {}

def _make_audio_mix(audio_file,job_id):
    ff=shutil.which("ffmpeg")
    if not ff:return audio_file
    out=DATA_DIR/"audio"/("%s_mix.wav"%job_id)
    out.parent.mkdir(parents=True,exist_ok=True)
    # Original procedural score + three subtle discovery chimes + narration.
    filt=("[1:a]volume=0.10,lowpass=f=1800,afade=t=in:st=0:d=2,afade=t=out:st=27:d=3[m];"
          "[2:a]volume=0.16,adelay=5000|5000,afade=t=out:st=5:d=1[c1];"
          "[3:a]volume=0.13,adelay=15000|15000,afade=t=out:st=15:d=1[c2];"
          "[4:a]volume=0.16,adelay=25000|25000,afade=t=out:st=25:d=1[c3];"
          "[0:a][m][c1][c2][c3]amix=inputs=5:duration=first:normalize=0[a]")
    cmd=[ff,"-y","-v","error","-i",str(audio_file),
         "-f","lavfi","-t","30","-i","sine=frequency=196:duration=30",
         "-f","lavfi","-t","30","-i","sine=frequency=880:duration=1",
         "-f","lavfi","-t","30","-i","sine=frequency=988:duration=1",
         "-f","lavfi","-t","30","-i","sine=frequency=1175:duration=1",
         "-filter_complex",filt,"-map","[a]","-ar","48000","-ac","2","-c:a","pcm_s16le",str(out)]
    r=subprocess.run(cmd,capture_output=True,text=True,timeout=120)
    if r.returncode:
        logger.warning("Music/SFX mix failed: %s",r.stderr[-1000:]); return audio_file
    return out

async def generate_story():
    job_id=datetime.now().strftime("%Y%m%d_%H%M%S")
    series=_series_bible()
    mode=os.getenv("PIPELINE_MODE","quality_gate")
    if mode=="quality_gate":
        story=_gate_story(series)
        logger.info("QUALITY GATE: six real animated shots / 30 seconds")
    else:
        story=validate_story_json(await generate_story_with_llm())
    DATA_DIR.joinpath("stories").mkdir(parents=True,exist_ok=True)
    sf=DATA_DIR/"stories"/("%s_story.json"%job_id)
    sf.write_text(json.dumps(story,indent=2,ensure_ascii=False),encoding="utf-8")
    scene_data=await generate_scenes(story,job_id)
    audio_data=await generate_narration_from_story(story,job_id)
    audio_data["narration_file"]=_make_audio_mix(audio_data["narration_file"],job_id)
    video_data=await create_animated_video(story,audio_data,scene_data,job_id)
    story.update({"job_id":job_id,"story_file":str(sf),"narration_file":audio_data["narration_file"],"subtitles_file":audio_data["subtitles_file"],"video_file":video_data["video_file"],"video_resolution":video_data["resolution"],"video_fps":video_data["fps"],"total_duration":video_data["duration_seconds"],"video_size_bytes":video_data["size_bytes"],"quality_level":"cinematic_quality_gate","youtube_result":{"status":"not_uploaded","reason":"YouTube upload remains disabled."}})
    logger.info("QUALITY GATE COMPLETE: %s",story["video_file"])
    return story
