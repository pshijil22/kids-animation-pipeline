"""Offline eSpeak NG narration."""
import os
import shutil
import subprocess
from pathlib import Path

DATA_DIR=Path(os.getenv("DATA_DIR","./data"))
AUDIO_DIR=DATA_DIR/"audio"
AUDIO_DIR.mkdir(parents=True,exist_ok=True)
TARGET=float(os.getenv("CINEMATIC_SCENE_SECONDS","15" if os.getenv("CINEMATIC_PREVIEW","true").lower()=="true" else "16.5"))
VOICE=os.getenv("TTS_VOICE","en-us")
RATE=os.getenv("TTS_RATE","155")
PITCH=os.getenv("TTS_PITCH","50")

def _duration(path):
    r=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",path],capture_output=True,text=True,timeout=10)
    return float(r.stdout.strip()) if r.stdout.strip() else 0.0

def _speak(text,out):
    binary=shutil.which("espeak-ng") or shutil.which("espeak")
    if not binary: raise RuntimeError("espeak-ng is not installed")
    r=subprocess.run([binary,"-v",VOICE,"-s",str(RATE),"-p",str(PITCH),"-w",str(out),text],capture_output=True,text=True,timeout=60)
    if r.returncode: raise RuntimeError(r.stderr[-1500:] or "eSpeak failed")

async def generate_narration_from_story(story,job_id):
    files=[]
    entries=[]
    total=0.0
    for i,sc in enumerate(story.get("scenes",[]),1):
        text=(sc.get("narration") or "").strip() or "Let's see what happens next."
        wav=AUDIO_DIR/("%s_scene_%03d.wav"%(job_id,i))
        _speak(text,wav)
        norm=wav.with_suffix(".norm.wav")
        r=subprocess.run(["ffmpeg","-y","-v","error","-i",str(wav),"-ar","22050","-ac","1","-c:a","pcm_s16le",str(norm)],capture_output=True,text=True,timeout=60)
        if r.returncode: raise RuntimeError(r.stderr[-1000:] or "Audio conversion failed")
        norm.replace(wav)
        spoken=_duration(str(wav))
        if spoken<=0: raise RuntimeError("Invalid narration for scene %s"%i)
        if spoken>TARGET or spoken<TARGET*.7:
            tempo=spoken/TARGET
            factors=[]
            while tempo>2: factors.append("2.0"); tempo/=2
            while tempo<.5: factors.append("0.5"); tempo/=0.5
            factors.append("%.6f"%tempo)
            af=",".join("atempo="+x for x in factors)+",apad,atrim=duration=%.3f"%TARGET
        else:
            af="apad,atrim=duration=%.3f"%TARGET
        out=wav.with_suffix(".pad.wav")
        r=subprocess.run(["ffmpeg","-y","-v","error","-i",str(wav),"-af",af,"-ar","22050","-ac","1","-c:a","pcm_s16le",str(out)],capture_output=True,text=True,timeout=60)
        if r.returncode: raise RuntimeError(r.stderr[-1000:] or "Narration normalization failed")
        out.replace(wav)
        files.append(str(wav))
        entries.append((i,total,min(spoken,TARGET),sc.get("title","Scene %s"%i),text[:220]))
        total+=TARGET

    concat=AUDIO_DIR/("%s_concat.txt"%job_id)
    with concat.open("w",encoding="utf-8") as f:
        for p in files: f.write("file '%s'\n"%Path(p).resolve())
    narration=AUDIO_DIR/("%s_narration.wav"%job_id)
    r=subprocess.run(["ffmpeg","-y","-v","error","-f","concat","-safe","0","-i",str(concat),"-c","copy",str(narration)],capture_output=True,text=True,timeout=180)
    concat.unlink(missing_ok=True)
    if r.returncode: raise RuntimeError(r.stderr[-1000:] or "Audio combine failed")

    srt=AUDIO_DIR/("%s_subtitles.srt"%job_id)
    with srt.open("w",encoding="utf-8") as f:
        for idx,start,spoken,title,text in entries:
            f.write("%s\n%s --> %s\n%s\n%s\n\n"%(idx,_srt(start),_srt(start+spoken),title,text))
    return {"narration_file":str(narration),"subtitles_file":str(srt),"scene_narrations":files,"total_duration":total}

def _srt(x):
    h=int(x//3600)
    m=int((x%3600)//60)
    s=int(x%60)
    ms=int((x%1)*1000)
    return "%02d:%02d:%02d,%03d"%(h,m,s,ms)
