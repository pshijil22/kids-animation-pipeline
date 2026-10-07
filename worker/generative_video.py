"""Real animated cinematic renderer for the quality gate."""
import json, logging, math, os, shutil, subprocess, sys
from pathlib import Path

log=logging.getLogger(__name__)
DATA=Path(os.getenv("DATA_DIR","./data")); VIDEOS=DATA/"videos"; SHOTS=DATA/"generated_shots"
FPS=int(os.getenv("BLENDER_RENDER_FPS","12")); WIDTH=int(os.getenv("BLENDER_RENDER_WIDTH","960")); HEIGHT=int(os.getenv("BLENDER_RENDER_HEIGHT","540"))
MIN_SECONDS=float(os.getenv("QUALITY_MIN_SECONDS","29")); MAX_SECONDS=float(os.getenv("QUALITY_MAX_SECONDS","31"))

def _run_blender(story_file, output):
    blender=shutil.which("blender")
    if not blender: raise RuntimeError("Blender is required")
    cmd=[blender,"--background","--enable-autoexec","--python",str(Path(__file__).resolve()),"--","--cinematic-render","--story",str(Path(story_file).resolve()),"--output",str(Path(output).resolve()),"--fps",str(FPS),"--width",str(WIDTH),"--height",str(HEIGHT)]
    p=subprocess.run(cmd,capture_output=True,text=True,timeout=1200)
    if p.returncode:
        log.error(p.stdout[-5000:]); log.error(p.stderr[-7000:]); raise RuntimeError("Blender cinematic render failed")
    if not output.exists() or output.stat().st_size<100000: raise RuntimeError("No usable animated render produced")

def _sub_filter(srt):
    p=str(Path(srt).resolve()).replace("\\","/").replace(":","\\:")
    return "subtitles='%s':force_style='FontName=DejaVu Sans,FontSize=22,PrimaryColour=&H00FFFFFF,OutlineColour=&H001B1630,BorderStyle=3,Outline=2,Shadow=1,MarginV=38'"%p

def _assemble(video,audio,srt,out,story):
    ff=shutil.which("ffmpeg"); title=str(story.get("title","Little Wonder Trails")).replace("'","\\'")
    vf="fps=30,scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,eq=contrast=1.04:saturation=1.08:gamma=1.01,unsharp=5:5:0.25:5:5:0.0,"+_sub_filter(srt)+",drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='%s':fontcolor=white:fontsize=54:borderw=3:bordercolor=black@0.55:x=(w-text_w)/2:y=70:enable='between(t,0.4,3.8)'"%title
    cmd=[ff,"-y","-loglevel","warning","-i",str(video),"-i",str(audio),"-filter_complex","[0:v]"+vf+"[v]","-map","[v]","-map","1:a:0","-c:v","libx264","-preset",os.getenv("VIDEO_PRESET","veryfast"),"-b:v",os.getenv("VIDEO_BITRATE","3500k"),"-maxrate",os.getenv("VIDEO_MAXRATE","4200k"),"-bufsize",os.getenv("VIDEO_BUFSIZE","8400k"),"-c:a","aac","-b:a","160k","-ar","48000","-pix_fmt","yuv420p","-movflags","+faststart","-shortest",str(out)]
    p=subprocess.run(cmd,capture_output=True,text=True,timeout=600)
    if p.returncode: log.error(p.stderr[-5000:]); raise RuntimeError("Final cinematic assembly failed")

async def generate_scenes(story,job_id):
    SHOTS.mkdir(parents=True,exist_ok=True); VIDEOS.mkdir(parents=True,exist_ok=True)
    scenes=story.get("scenes",[]); expected=int(os.getenv("TOTAL_SCENES","6"))
    if len(scenes)!=expected: raise ValueError("Expected %s scenes, received %s"%(expected,len(scenes)))
    sf=SHOTS/(job_id+"_story.json"); raw=VIDEOS/(job_id+"_blender.mp4")
    sf.write_text(json.dumps(story,ensure_ascii=False),encoding="utf-8")
    log.info("Rendering %s REAL animated shots at %sx%s/%sfps",len(scenes),WIDTH,HEIGHT,FPS)
    _run_blender(sf,raw)
    return {"clips":[raw],"scene_images":[]}

async def create_animated_video(story,audio_data,scene_data,job_id):
    clips=[Path(x) for x in scene_data["clips"]]; out=VIDEOS/(job_id+".mp4")
    _assemble(clips[0],Path(audio_data["narration_file"]),Path(audio_data["subtitles_file"]),out,story)
    d=float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(out)],text=True).strip())
    if not MIN_SECONDS<=d<=MAX_SECONDS: raise RuntimeError("Quality gate duration %.2fs outside %.2f-%.2fs"%(d,MIN_SECONDS,MAX_SECONDS))
    return {"video_file":str(out),"title":story["title"],"description":story.get("description",""),"size_bytes":out.stat().st_size,"duration_seconds":d,"job_id":job_id,"resolution":"1920x1080","fps":30}

def _arg(n,d=None): return sys.argv[sys.argv.index(n)+1] if n in sys.argv else d

def _blender_render():
    import bpy
    from mathutils import Vector
    story=json.loads(Path(_arg("--story")).read_text(encoding="utf-8")); out=Path(_arg("--output"))
    fps=int(_arg("--fps",str(FPS))); w=int(_arg("--width",str(WIDTH))); h=int(_arg("--height",str(HEIGHT)))
    scenes=story["scenes"]

    def mat(name,c,rough=.6,emit=0):
        m=bpy.data.materials.new(name); m.use_nodes=True; b=m.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value=(*c,1); b.inputs["Roughness"].default_value=rough
        if emit: b.inputs["Emission Color"].default_value=(*c,1); b.inputs["Emission Strength"].default_value=emit
        return m
    def sph(name,loc,scale,m,seg=24):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=16,location=loc); o=bpy.context.object; o.name=name; o.scale=scale; o.data.materials.append(m)
        for p in o.data.polygons:p.use_smooth=True
        return o
    def key(o,f,loc=None,rot=None):
        if loc is not None:o.location=loc;o.keyframe_insert("location",frame=f)
        if rot is not None:o.rotation_euler=rot;o.keyframe_insert("rotation_euler",frame=f)
    def aim(o,target,f):o.rotation_euler=(Vector(target)-o.location).to_track_quat("-Z","Y").to_euler();o.keyframe_insert("rotation_euler",frame=f)

    bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
    sc=bpy.context.scene; engines={x.identifier for x in sc.render.bl_rna.properties["engine"].enum_items};sc.render.engine="BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else "BLENDER_EEVEE";sc.render.resolution_x=w;sc.render.resolution_y=h;sc.render.resolution_percentage=100;sc.render.fps=fps
    sc.render.image_settings.file_format="FFMPEG";sc.render.ffmpeg.format="MPEG4";sc.render.ffmpeg.codec="H264";sc.render.ffmpeg.constant_rate_factor="MEDIUM";sc.render.filepath=str(out)
    try:sc.view_settings.look="AgX - Medium High Contrast"
    except Exception:pass
    world=bpy.data.worlds.new("World") if not bpy.data.worlds else bpy.data.worlds[0];sc.world=world;world.use_nodes=True;world.node_tree.nodes["Background"].inputs["Color"].default_value=(.035,.055,.09,1);world.node_tree.nodes["Background"].inputs["Strength"].default_value=.35

    grass=mat("Grass",(.12,.30,.10),.9);wood=mat("Wood",(.28,.12,.045),.85);cream=mat("Cream",(.88,.72,.54),.65);teal=mat("Teal",(.03,.45,.48));honey=mat("Honey",(.48,.25,.10),.8);yellow=mat("Yellow",(.88,.55,.08));orange=mat("Orange",(.82,.26,.055));purple=mat("Purple",(.42,.15,.52));white=mat("White",(.97,.97,.92),.35);black=mat("Black",(.008,.006,.006),.2);gold=mat("Glow",(1,.35,.03),.2,5)
    sph("Ground",(0,2,-.7),(18,14,.55),grass)
    for x,y,s in [(-8,5,1.7),(-5,8,1.2),(7,6,1.6),(10,1,1.1),(-9,-1,1),(6,-4,1)]:
        sph("Trunk",(x,y,1.1*s),(.32*s,.32*s,1.5*s),wood);sph("Canopy",(x,y,2.8*s),(1.7*s,1.5*s,1.8*s),grass)

    def hero(spec,i):
        sp=spec.get("species","").lower();fur,acc=(cream,teal) if "bunny" in sp or "rabbit" in sp else (honey,yellow) if "bear" in sp else (orange,purple)
        root=bpy.data.objects.new("Hero%d"%i,None);bpy.context.collection.objects.link(root)
        body=sph("Body%d"%i,(0,0,1.15),(.72,.58,.95),fur);head=sph("Head%d"%i,(0,0,2.12),(.72,.67,.68),fur);body.parent=root;head.parent=root
        for side in (-1,1):
            e=sph("Eye",(side*.25,-.62,2.22),(.13,.08,.16),white);p=sph("Pupil",(side*.25,-.69,2.22),(.055,.025,.075),black);e.parent=root;p.parent=root
            a=sph("Arm",(side*.72,0,1.32),(.16,.16,.55),fur);a.parent=root
            l=sph("Leg",(side*.3,0,.43),(.2,.2,.48),fur);l.parent=root
        if "bunny" in sp or "rabbit" in sp:
            for side in (-1,1):sph("Ear",(side*.38,0,2.82),(.18,.16,.62),fur).parent=root
        elif "fox" in sp:
            sph("Tail",(0,.58,1.35),(.25,.65,.42),fur).parent=root;sph("TailTip",(0,.95,1.5),(.27,.28,.27),white).parent=root
        else:
            sph("Ear",(-.42,0,2.62),(.23,.18,.24),fur).parent=root;sph("Ear",(.42,0,2.62),(.23,.18,.24),fur).parent=root
        sph("Accessory",(0,-.60,1.55),(.42,.10,.18),acc).parent=root
        return root

    cast=story.get("characters",[]);cast=list(cast.values()) if isinstance(cast,dict) else cast;heroes=[hero(c,i) for i,c in enumerate(cast[:3])]
    cd=bpy.data.cameras.new("Camera");cam=bpy.data.objects.new("Camera",cd);bpy.context.collection.objects.link(cam);sc.camera=cam;cd.dof.use_dof=True;cd.dof.aperture_fstop=2.2
    focus=bpy.data.objects.new("Focus",None);bpy.context.collection.objects.link(focus);cd.dof.focus_object=focus
    for name,energy,size,loc,color in [("Key",1100,7,(-5,-5,9),(1,.72,.48)),("Fill",500,9,(6,-1,6),(.45,.62,1)),("Rim",800,5,(0,7,7),(1,.42,.2))]:
        d=bpy.data.lights.new(name,"AREA");d.energy=energy;d.shape="DISK";d.size=size;d.color=color;o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);o.location=loc

    cursor=1
    for si,s in enumerate(scenes):
        frames=max(1,round(float(s.get("duration_seconds",5))*fps));start,end=cursor,cursor+frames-1;beats=(s.get("visual_beats") or [{},{},{}])[:3]
        for bi,b in enumerate(beats):
            f=start+round((end-start)*(bi/2));act=str(b.get("action","")).lower();camt=str(b.get("camera","")).lower()
            for i,r in enumerate(heroes):
                x=(i-1)*1.8 + (.8*bi if any(k in act for k in ("run","rush","follow")) else 0);z=.3 if "jump" in act and bi==1 else 0;key(r,f,(x,0,z),(0,0,math.radians(-5 if "turn" in act else 0)))
            if "wide" in camt:pos,lens=(0,-13,5.8),34
            elif "close" in camt:pos,lens=(0,-5.2,2.8),72
            elif "low" in camt:pos,lens=(-3.5,-7,1.5),46
            else:pos,lens=(0,-8.5,3.6),52
            key(cam,f,pos);cd.lens=lens;aim(cam,(0,0,1.55),f);focus.location=(0,0,1.55)
        cursor=end+1
    sc.frame_start=1;sc.frame_end=cursor-1;bpy.ops.wm.save_as_mainfile(filepath=str(out.with_suffix(".blend")));bpy.ops.render.render(animation=True);print("CINEMATIC_ANIMATION_DONE",sc.frame_end,flush=True)

if __name__=="__main__" and "--cinematic-render" in sys.argv:_blender_render()
