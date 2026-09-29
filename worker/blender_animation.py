"""FFmpeg compositor with narration-driven timing and gentle camera animation."""
import logging
import os
import subprocess
from pathlib import Path

logger=logging.getLogger(__name__)
DATA_DIR=Path(os.getenv("DATA_DIR","./data"))
VIDEOS_DIR=DATA_DIR/"videos"
VIDEO_WIDTH=int(os.getenv("VIDEO_WIDTH","1280"))
VIDEO_HEIGHT=int(os.getenv("VIDEO_HEIGHT","720"))
VIDEO_FPS=int(os.getenv("VIDEO_FPS","30"))
VIDEO_CRF=os.getenv("VIDEO_CRF","19")
VIDEO_PRESET=os.getenv("VIDEO_PRESET","medium")


def _scene_durations(story,audio_data,scene_images):
    actual=audio_data.get("scene_narrations") or []
    by_num={int(x.get("scene_num",i+1)):float(x.get("duration",0) or 0) for i,x in enumerate(actual)}
    fallback=float(audio_data.get("total_duration",story.get("duration_seconds",60)) or 60)/max(1,len(scene_images))
    return [max(2.0,by_num.get(int(s.get("number",i+1)),fallback)) for i,s in enumerate(scene_images)]


def _subtitle_filter(path):
    # FFmpeg subtitles filter escaping for POSIX/Windows-ish paths.
    value=str(Path(path).resolve()).replace("\","/").replace(":","\\:").replace("'","\\'")
    return f"subtitles='{value}':force_style='FontName=DejaVu Sans,FontSize=22,PrimaryColour=&H00FFFFFF,OutlineColour=&H001B1630,BorderStyle=3,Outline=2,Shadow=1,MarginV=34'"


async def create_animated_video(story,audio_data,scene_data,job_id):
    VIDEOS_DIR.mkdir(parents=True,exist_ok=True)
    images=scene_data.get("scene_images",[])
    if not images:
        raise ValueError("No scene images were generated")
    narration=Path(audio_data["narration_file"])
    subtitles=Path(audio_data["subtitles_file"])
    if not narration.exists():
        raise FileNotFoundError(narration)
    durations=_scene_durations(story,audio_data,images)
    output=VIDEOS_DIR/f"{job_id}.mp4"

    inputs=[]
    filters=[]
    for i,(scene,duration) in enumerate(zip(images,durations)):
        path=Path(scene["path"])
        if not path.exists():
            raise FileNotFoundError(path)
        frames=max(1,round(duration*VIDEO_FPS))
        # Each scene gets a different slow camera move: zoom + horizontal drift.
        if i%4==0:
            z="min(zoom+0.00055,1.10)"
            x="iw/2-(iw/zoom/2)"
        elif i%4==1:
            z="max(1.0,zoom-0.00035)"
            x="iw/2-(iw/zoom/2)-20"
        elif i%4==2:
            z="min(zoom+0.00045,1.08)"
            x="(iw-iw/zoom)*on/{frames}"
        else:
            z="min(zoom+0.00045,1.08)"
            x="(iw-iw/zoom)*(1-on/{frames})"
        inputs += ["-loop","1","-t",f"{duration:.3f}","-i",str(path)]
        filters.append(
            f"[{i}:v]scale={VIDEO_WIDTH*2}:{VIDEO_HEIGHT*2}:force_original_aspect_ratio=increase,"
            f"crop={VIDEO_WIDTH*2}:{VIDEO_HEIGHT*2},zoompan=z='{z}':x='{x}':y='ih/2-(ih/zoom/2)':"
            f"d={frames}:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:fps={VIDEO_FPS},setsar=1[v{i}]"
        )
    concat="".join(f"[v{i}]" for i in range(len(images)))+f"concat=n={len(images)}:v=1:a=0[v]"
    filters.append(concat)
    filters.append(f"[v]{_subtitle_filter(subtitles)}[vout]")
    cmd=["ffmpeg","-y","-loglevel","warning",*inputs,"-i",str(narration),"-filter_complex",";".join(filters),
         "-map","[vout]","-map",f"{len(images)}:a:0","-c:v","libx264","-preset",VIDEO_PRESET,
         "-crf",VIDEO_CRF,"-tune","animation","-c:a","aac","-b:a","160k","-ar","48000",
         "-pix_fmt","yuv420p","-movflags","+faststart","-shortest",str(output)]
    result=subprocess.run(cmd,capture_output=True,text=True,timeout=900)
    if result.returncode!=0:
        logger.error(result.stderr[-4000:])
        raise RuntimeError("FFmpeg animation render failed")
    size=output.stat().st_size
    if size<100_000:
        raise RuntimeError(f"Video output is suspiciously small: {size} bytes")
    return {"video_file":str(output),"title":story["title"],"description":story["description"],
            "size_bytes":size,"duration_seconds":sum(durations),"job_id":job_id,
            "resolution":f"{VIDEO_WIDTH}x{VIDEO_HEIGHT}","fps":VIDEO_FPS}
