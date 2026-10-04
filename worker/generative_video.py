"""Shot-based cinematic Blender renderer with original procedural 3D puppets."""
import json
import logging
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path

logger=logging.getLogger(__name__)
DATA_DIR=Path(os.getenv("DATA_DIR","./data"))
VIDEOS_DIR=DATA_DIR/"videos"
SHOTS_DIR=DATA_DIR/"generated_shots"
PREVIEW=os.getenv("CINEMATIC_PREVIEW","true").lower()=="true"
FPS=int(os.getenv("BLENDER_RENDER_FPS","12"))
WIDTH=int(os.getenv("BLENDER_RENDER_WIDTH","640"))
HEIGHT=int(os.getenv("BLENDER_RENDER_HEIGHT","360"))
SCENE_SECONDS=float(os.getenv("CINEMATIC_SCENE_SECONDS","15"))
MIN_SECONDS=80 if PREVIEW else 1140
MAX_SECONDS=110 if PREVIEW else 1260

def _run_blender(story_file,output_file):
    """Render the episode in parallel Blender shards, then stitch losslessly."""
    blender,ffmpeg=shutil.which("blender"),shutil.which("ffmpeg")
    if not blender or not ffmpeg: raise RuntimeError("Blender and FFmpeg must be installed.")
    story=json.loads(Path(story_file).read_text(encoding="utf-8"))
    scenes=story.get("scenes",[])
    requested=int(os.getenv("BLENDER_SHARDS","4"))
    shard_count=max(1,min(requested,len(scenes) or 1))
    shard_size=math.ceil(len(scenes)/shard_count)
    work_dir=output_file.with_name(output_file.stem+"_shards")
    work_dir.mkdir(parents=True,exist_ok=True)

    def render_one(index):
        first=index*shard_size
        shard_scenes=scenes[first:first+shard_size]
        shard_story=dict(story)
        shard_story["scenes"]=shard_scenes
        shard_story_file=work_dir/("story_%02d.json"%index)
        shard_output=work_dir/("part_%02d.mp4"%index)
        shard_frames=work_dir/("frames_%02d"%index)
        shard_frames.mkdir(parents=True,exist_ok=True)
        shard_story_file.write_text(json.dumps(shard_story,ensure_ascii=False),encoding="utf-8")
        command=[blender,"--background","--enable-autoexec","--python",str(Path(__file__).resolve()),"--","--free-blender-render","--story",str(shard_story_file.resolve()),"--output",str((shard_frames/"frame_####").resolve()),"--fps",str(FPS),"--width",str(WIDTH),"--height",str(HEIGHT)]
        result=subprocess.run(command,capture_output=True,text=True,timeout=120*60)
        if result.returncode:
            logger.error("Blender shard %s stdout: %s",index,result.stdout[-5000:])
            logger.error("Blender shard %s stderr: %s",index,result.stderr[-7000:])
            raise RuntimeError("Blender shard %s failed"%index)
        frames=sorted(shard_frames.rglob("frame_*.jpg"))
        if len(frames)<max(100,FPS*8) or not (shard_frames/"frame_0001.jpg").exists():
            logger.error("Blender shard %s produced %s frames",index,len(frames))
            raise RuntimeError("Blender shard %s did not produce enough frames"%index)
        frame_pattern=shard_frames/"frame_%04d.jpg"
        encode=[ffmpeg,"-y","-loglevel","warning","-framerate",str(FPS),"-start_number","1","-i",str(frame_pattern),"-c:v","libx264","-preset",os.getenv("VIDEO_PRESET","slow"),"-b:v",os.getenv("VIDEO_BITRATE","1400k"),"-maxrate",os.getenv("VIDEO_MAXRATE","1600k"),"-bufsize",os.getenv("VIDEO_BUFSIZE","3200k"),"-pix_fmt","yuv420p","-movflags","+faststart",str(shard_output)]
        encoded=subprocess.run(encode,capture_output=True,text=True,timeout=60*60)
        if encoded.returncode or not shard_output.exists():
            logger.error("FFmpeg shard %s stderr: %s",index,encoded.stderr[-6000:])
            raise RuntimeError("FFmpeg shard %s failed"%index)
        shutil.rmtree(shard_frames,ignore_errors=True)
        return shard_output

    from concurrent.futures import ThreadPoolExecutor
    logger.info("Rendering %s scenes in %s parallel Blender shards (%sx%s/%sfps)",len(scenes),shard_count,WIDTH,HEIGHT,FPS)
    with ThreadPoolExecutor(max_workers=shard_count) as pool:
        parts=list(pool.map(render_one,range(shard_count)))

    concat_file=work_dir/"concat.txt"
    concat_file.write_text("".join("file '%s'\n"%p.resolve().as_posix().replace("'","'\\''") for p in parts),encoding="utf-8")
    command=[ffmpeg,"-y","-loglevel","warning","-f","concat","-safe","0","-i",str(concat_file),"-c","copy","-movflags","+faststart",str(output_file)]
    result=subprocess.run(command,capture_output=True,text=True,timeout=30*60)
    if result.returncode or not output_file.exists():
        logger.error("FFmpeg concat stderr: %s",result.stderr[-6000:])
        raise RuntimeError("FFmpeg could not stitch the cinematic shards")
    shutil.rmtree(work_dir,ignore_errors=True)

def _concat_audio_video(video,narration,subtitles,output):
    sub=str(subtitles.resolve()).replace(chr(92),"/").replace(":","\:")
    filt=("subtitles='"+sub+"':force_style='FontName=DejaVu Sans,FontSize=22,PrimaryColour=&H00FFFFFF,OutlineColour=&H001B1630,BorderStyle=3,Outline=2,Shadow=1,MarginV=34'")
    cmd=["ffmpeg","-y","-loglevel","warning","-i",str(video),"-i",str(narration),"-filter_complex","[0:v]fps=30,scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,eq=contrast=1.04:saturation=1.08:gamma=1.01,unsharp=5:5:0.25:5:5:0.0,"+filt+"[v]","-map","[v]","-map","1:a:0","-c:v","libx264","-preset",os.getenv("VIDEO_PRESET","slow"),"-b:v",os.getenv("VIDEO_BITRATE","1400k"),"-maxrate",os.getenv("VIDEO_MAXRATE","1600k"),"-bufsize",os.getenv("VIDEO_BUFSIZE","3200k"),"-c:a","aac","-b:a","96k","-ar","48000","-pix_fmt","yuv420p","-movflags","+faststart","-shortest",str(output)]
    result=subprocess.run(cmd,capture_output=True,text=True,timeout=7200)
    if result.returncode: logger.error(result.stderr[-5000:]); raise RuntimeError("Final movie assembly failed")

async def generate_scenes(story,job_id):
    SHOTS_DIR.mkdir(parents=True,exist_ok=True); VIDEOS_DIR.mkdir(parents=True,exist_ok=True)
    scenes=story.get("scenes",[]); expected=6 if PREVIEW else int(os.getenv("TOTAL_SCENES","80"))
    if len(scenes)!=expected: raise ValueError("Expected %s scenes, received %s"%(expected,len(scenes)))
    story_file=SHOTS_DIR/("%s_story.json"%job_id); silent=VIDEOS_DIR/("%s_cinematic.mp4"%job_id)
    story_file.write_text(json.dumps(story,ensure_ascii=False),encoding="utf-8")
    logger.info("Rendering %s scenes as three cinematic shots each at %sx%s/%sfps",len(scenes),WIDTH,HEIGHT,FPS)
    _run_blender(story_file,silent)
    if not silent.exists() or silent.stat().st_size<100000: raise RuntimeError("No usable cinematic movie was produced")
    return {"clips":[silent],"scene_images":[]}

async def create_animated_video(story,audio_data,scene_data,job_id):
    clips=[Path(x) for x in scene_data.get("clips",[])]
    if not clips: raise ValueError("No cinematic render was produced")
    output=VIDEOS_DIR/("%s.mp4"%job_id)
    _concat_audio_video(clips[0],Path(audio_data["narration_file"]),Path(audio_data["subtitles_file"]),output)
    duration=float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(output)],text=True).strip())
    if not MIN_SECONDS<=duration<=MAX_SECONDS: raise RuntimeError("Generated movie duration %.1fs outside %s-%ss"%(duration,MIN_SECONDS,MAX_SECONDS))
    size=output.stat().st_size
    if size<100000: raise RuntimeError("Video output is suspiciously small")
    return {"video_file":str(output),"title":story["title"],"description":story["description"],"size_bytes":size,"duration_seconds":duration,"job_id":job_id,"resolution":"1920x1080","fps":30}

def _arg(name,default=None):
    return sys.argv[sys.argv.index(name)+1] if name in sys.argv else default

def _blender_render():
    import bpy
    from mathutils import Vector
    story=json.loads(Path(_arg("--story")).read_text(encoding="utf-8")); output=Path(_arg("--output"))
    fps=int(_arg("--fps",str(FPS))); width=int(_arg("--width",str(WIDTH))); height=int(_arg("--height",str(HEIGHT)))
    scenes=story["scenes"]; total_frames=int(sum(float(x.get("duration_seconds",SCENE_SECONDS)) for x in scenes)*fps)

    def mat(name,color,rough=.55):
        m=bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes=True
        b=m.node_tree.nodes.get("Principled BSDF"); b.inputs["Base Color"].default_value=(*color,1); b.inputs["Roughness"].default_value=rough
        if "Specular IOR Level" in b.inputs: b.inputs["Specular IOR Level"].default_value=.35
        return m
    def sphere(name,loc,scale,material):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=10,location=loc); o=bpy.context.object; o.name=name; o.scale=scale; o.data.materials.append(material)
        for p in o.data.polygons: p.use_smooth=True
        return o
    def curve(name,points,bevel,material):
        c=bpy.data.curves.new(name,"CURVE"); c.dimensions="3D"; c.bevel_depth=bevel; c.bevel_resolution=3
        s=c.splines.new("BEZIER"); s.bezier_points.add(len(points)-1)
        for p,co in zip(s.bezier_points,points): p.co=co; p.handle_left_type="AUTO"; p.handle_right_type="AUTO"
        o=bpy.data.objects.new(name,c); bpy.context.collection.objects.link(o); o.data.materials.append(material); return o
    def key(o,frame,loc=None,rot=None,scale=None):
        if loc is not None: o.location=loc; o.keyframe_insert("location",frame=frame)
        if rot is not None: o.rotation_euler=rot; o.keyframe_insert("rotation_euler",frame=frame)
        if scale is not None: o.scale=scale; o.keyframe_insert("scale",frame=frame)
    def aim(o,target,frame):
        o.rotation_euler=(Vector(target)-o.location).to_track_quat("-Z","Y").to_euler(); o.keyframe_insert("rotation_euler",frame=frame)

    bpy.ops.object.select_all(action="SELECT"); bpy.ops.object.delete(use_global=False)
    scene=bpy.context.scene; engines={x.identifier for x in scene.render.bl_rna.properties["engine"].enum_items}
    scene.render.engine="BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else "BLENDER_EEVEE"
    scene.render.resolution_x,scene.render.resolution_y=width,height; scene.render.resolution_percentage=100; scene.render.fps=fps
    scene.render.image_settings.file_format="JPEG"; scene.render.image_settings.color_mode="RGB"; scene.render.image_settings.quality=92; scene.render.use_file_extension=True; scene.render.filepath=str(output); scene.render.use_file_extension=True
    scene.frame_start,scene.frame_end=1,total_frames
    try: scene.view_settings.look="AgX - Medium High Contrast"
    except Exception: pass
    world=bpy.data.worlds.new("CinematicWorld") if not bpy.data.worlds else bpy.data.worlds[0]; scene.world=world; world.use_nodes=True
    bg=world.node_tree.nodes.get("Background"); bg.inputs["Strength"].default_value=.32

    ground=mat("Ground",(.18,.32,.15),.82); sand=mat("Sand",(.72,.56,.34),.9); water=mat("Water",(.06,.30,.48),.2)
    leaf=mat("Leaves",(.10,.40,.16),.72); wood=mat("Wood",(.24,.11,.05),.88); rock=mat("Rock",(.30,.32,.34),.92)
    white=mat("Foam",(.93,.96,.94),.4); eye=mat("Eye",(.97,.98,.94),.2); pupil=mat("Pupil",(.01,.008,.012),.15); mouth=mat("Mouth",(.16,.02,.018),.35)
    sphere("Ground",(0,2,-.85),(18,16,.65),ground); sphere("Sand",(0,-5,-.48),(17,8,.32),sand); sphere("Water",(0,-12,-.22),(17,7,.12),water)
    for x,y,s in [(-8,4,1.6),(-5,7,1),(7,5,1.4),(9,1,1.1),(-10,-1,.9),(6,-3,.8)]:
        sphere("Trunk",(x,y,1*s),(.14*s,.14*s,1*s),wood); sphere("Canopy",(x,y,2.2*s),(1.1*s,.9*s,1.2*s),leaf)
    for x,y,s in [(-5,1,1),(4,3,.8),(8,-2,1.1),(-8,-3,.65)]: sphere("Rock",(x,y,.02),(s,s*.7,s*.4),rock)
    for y in (-7,-8.2,-9.4): curve("Wave",[(-14,y,0),(-7,y+.35,.08),(0,y,.02),(7,y-.3,.08),(14,y,0)],.045,white)

    def prop_for(text, material_map):
        t=(text or "").lower()
        choices=[
            (("box","chest","treasure"),"box"),(("key",),"key"),(("map","paper","letter"),"map"),
            (("book","storybook"),"book"),(("ball","toy"),"ball"),(("flower","rose","plant"),"flower"),
            (("shell",),"shell"),(("lantern","lamp"),"lantern"),(("boat","ship"),"boat"),
            (("kite",),"kite"),(("apple","fruit"),"apple"),(("cookie","cake"),"cookie"),
            (("backpack","bag"),"backpack"),(("bridge",),"bridge"),(("star","moon"),"star"),
            (("stick","branch"),"stick"),(("stone","rock","pebble"),"stone")
        ]
        for words,kind in choices:
            if any(w in t for w in words): return kind
        return None
    def make_prop(kind,materials):
        if not kind: return None
        wood,metal,blue,red,yellow,green=materials
        if kind=="box": return sphere("StoryBox",(0,0,.65),(.62,.52,.45),wood)
        if kind=="key": return curve("StoryKey",[(-.45,0,.65),(.2,0,.65),(.35,0,.82)],.07,metal)
        if kind=="map": return sphere("StoryMap",(0,0,.5),(.7,.08,.5),yellow)
        if kind=="book": return sphere("StoryBook",(0,0,.55),(.55,.32,.12),red)
        if kind in ("ball","apple","cookie","stone","shell"): return sphere("StoryObject",(0,0,.6),(.38,.38,.38),red if kind=="apple" else yellow if kind=="cookie" else blue)
        if kind=="flower": return curve("StoryFlower",[(0,0,.2),(0,0,.8),(0,0,1.2)],.035,green)
        if kind=="lantern": return sphere("StoryLantern",(0,0,.8),(.3,.3,.5),yellow)
        if kind=="boat": return sphere("StoryBoat",(0,-1,.2),(1.2,.45,.25),blue)
        if kind=="kite": return curve("StoryKite",[(0,0,1),(0,0,2)],.025,red)
        if kind=="backpack": return sphere("StoryBag",(0,.35,1),(.55,.25,.65),blue)
        if kind=="bridge": return curve("StoryBridge",[(-2,0,.3),(0,0,.7),(2,0,.3)],.22,wood)
        if kind=="star": return sphere("StoryStar",(0,0,1.3),(.25,.25,.25),yellow)
        if kind=="stick": return curve("StoryStick",[(-.5,0,.5),(.5,0,.8)],.08,wood)
        return None
    prop_mats=(wood,rock,water,white,leaf,sand)

    def light(name,energy,size,loc,color):
        d=bpy.data.lights.new(name,"AREA"); d.energy=energy; d.shape="DISK"; d.size=size; d.color=color
        o=bpy.data.objects.new(name,d); bpy.context.collection.objects.link(o); o.location=loc; return o
    light("Key",850,6,(-5,-4,10),(1,.72,.50)); light("Fill",520,8,(6,-1,6),(.48,.68,1)); light("Rim",700,5,(0,7,7),(1,.55,.30))

    cd=bpy.data.cameras.new("Camera"); camera=bpy.data.objects.new("Camera",cd); bpy.context.collection.objects.link(camera); scene.camera=camera
    cd.dof.use_dof=True; cd.dof.aperture_fstop=2.2; focus=bpy.data.objects.new("Focus",None); bpy.context.collection.objects.link(focus); cd.dof.focus_object=focus

    palettes=[(.88,.32,.16),(.18,.48,.78),(.62,.24,.66)]
    heroes=[]
    characters=story.get("characters",[])
    if isinstance(characters,dict):
        characters=list(characters.values())
    elif not isinstance(characters,list):
        characters=[]
    for idx,_unused in enumerate(characters[:3]):
        bm=mat("Hero%d"%idx,palettes[idx%3],.48); root=bpy.data.objects.new("HeroRoot%d"%idx,None); bpy.context.collection.objects.link(root)
        body=sphere("Body%d"%idx,(0,0,1.15),(.78,.58,.92),bm); head=sphere("Head%d"%idx,(0,-.02,2.15),(.72,.65,.68),bm); body.parent=root; head.parent=root
        arms=[]; legs=[]; pupils=[]; brows=[]
        for side in (-1,1):
            e=sphere("Eye",(side*.25,-.59,2.25),(.15,.08,.18),eye); e.parent=root
            p=sphere("Pupil",(side*.25,-.665,2.25),(.065,.025,.09),pupil); p.parent=root
            b=curve("Brow",[(side*.39,-.64,2.49),(side*.15,-.68,2.54)],.025,pupil); b.parent=root
            a=sphere("Arm",(side*.78,-.02,1.35),(.18,.18,.62),bm); a.parent=root; arms.append(a)
            l=sphere("Leg",(side*.34,.02,.47),(.20,.20,.58),bm); l.parent=root; legs.append(l)
            ear=sphere("Ear",(side*.42,.02,2.70),(.24,.18,.48),bm); ear.parent=root; ears=[]
            pupils.append(p); brows.append(b)
        m=curve("Mouth",[(-.18,-.66,1.95),(0,-.70,1.90),(.18,-.66,1.95)],.035,mouth); m.parent=root
        tail=curve("Tail",[(0,.45,1.35),(.45,.72,1.48),(.82,.70,1.85)],.13,bm); tail.parent=root
        heroes.append({"root":root,"body":body,"arms":arms,"legs":legs,"pupils":pupils,"brows":brows,"mouth":m,"tail":tail})

    def animate(h,action,emotion,start,end,lane):
        text=(action or "").lower(); moving=any(w in text for w in ("run","walk","chase","follow","move","rush","approach")); jumping=any(w in text for w in ("jump","leap","hop"))
        x0=-1+lane*1.05; x1=x0+(2.7 if moving else .5); mid=start+(end-start)//2
        key(h["root"],start,(x0,0,0),(0,0,0)); key(h["root"],mid,((x0+x1)/2,0,.65 if jumping else .08),(0,0,math.radians(-7))); key(h["root"],end,(x1,0,.35 if jumping else 0),(0,0,math.radians(-5)))
        for j,l in enumerate(h["legs"]):
            a=math.radians(24 if j==0 and moving else -24 if moving else 0); key(l,start,rot=(0,a,0)); key(l,mid,rot=(0,-a,0)); key(l,end,rot=(0,a,0))
        for j,aobj in enumerate(h["arms"]):
            a=math.radians(-25 if j==0 else 15)
            if "wave" in text: a=math.radians(-42 if j==0 else 8)
            if any(w in text for w in ("reach","grab","pick")): a=math.radians(-34)
            key(aobj,start,rot=(0,a,0)); key(aobj,mid,rot=(0,-a*.7,0)); key(aobj,end,rot=(0,a*.4,0))
        key(h["body"],start,scale=(.78,.58,.92)); key(h["body"],mid,scale=(.80,.60,.95)); key(h["body"],end,scale=(.78,.58,.92))
        e=(emotion or "").lower(); worried=any(w in e for w in ("worried","sad","scared","nervous")); smile=any(w in e for w in ("happy","joy","excited","proud","brave"))
        for b in h["brows"]:
            r=math.radians(-12 if worried else 5 if smile else 0); key(b,start,rot=(0,0,r)); key(b,end,rot=(0,0,r))
        blink=start+int(1.8*fps)
        for p in h["pupils"]: key(p,blink,scale=(.065,.025,.02)); key(p,blink+max(1,fps//8),scale=(.065,.025,.09))

    def shot(style,start,end,target,n):
        s=(style or "").lower()
        if "close" in s or n%5==2: lens,p0,p1,fs=85,(0,-5.3,2.8),(.35,-4.6,2.5),1.7
        elif "wide" in s or n%5==0: lens,p0,p1,fs=28,(0,-13,6.2),(1,-11,5.3),3.2
        elif "low" in s: lens,p0,p1,fs=45,(-3.8,-7,1.8),(2.8,-6,2.4),2.4
        elif "overhead" in s: lens,p0,p1,fs=35,(0,-3,9),(1,-1,4.5),3
        else: lens,p0,p1,fs=50,(0,-8.5,4),(1,-7,3.1),2.5
        cd.lens=lens; cd.dof.aperture_fstop=fs; camera.location=p0; aim(camera,target,start); camera.keyframe_insert("location",frame=start)
        camera.location=p1; aim(camera,(target[0]+.3,target[1],target[2]),end); camera.keyframe_insert("location",frame=end)
        focus.location=target; focus.keyframe_insert("location",frame=start); focus.location=(target[0]+.2,target[1],target[2]); focus.keyframe_insert("location",frame=end)

    frame=1; shot_no=0
    for i,sc in enumerate(scenes):
        dur=float(sc.get("duration_seconds",SCENE_SECONDS)); start=frame; end=frame+int(dur*fps)-1; third=max(1,(end-start+1)//3)
        beats=sc.get("visual_beats") or []
        while len(beats)<3: beats.append({"action":sc.get("action",""),"prop":sc.get("props",""),"camera":sc.get("camera",""),"subject":sc.get("character_actions","")})
        for bidx,beat in enumerate(beats[:3]):
            bs=start+bidx*third
            be=end if bidx==2 else start+(bidx+1)*third-1
            beat_text=" ".join(str(beat.get(k,"")) for k in ("narration_line","subject","action","prop"))
            beat_action=str(beat.get("action") or sc.get("action") or "")
            beat_subject=str(beat.get("subject") or sc.get("character_actions") or "")
            beat_emotion=str(sc.get("emotion") or "curious")
            for idx,h in enumerate(heroes):
                animate(h, beat_action+" "+beat_subject, beat_emotion, bs, be, idx)
            beat_kind=prop_for(beat_text, prop_mats)
            beat_prop=make_prop(beat_kind, prop_mats)
            target=(-.2+(i%3)*.4,-.35,1.8)
            if beat_prop:
                beat_prop.location=(.15,-.55,.55); beat_prop.keyframe_insert("location",frame=bs)
                beat_prop.location=(.25,-.25,.85); beat_prop.keyframe_insert("location",frame=be)
                beat_prop.scale=(1,1,1); beat_prop.keyframe_insert("scale",frame=bs)
                beat_prop.scale=(1.08,1.08,1.08); beat_prop.keyframe_insert("scale",frame=be)
                if any(w in beat_action.lower() for w in ("open","reveal","turn","lift")):
                    key(beat_prop,bs,rot=(0,0,math.radians(-8))); key(beat_prop,be,rot=(0,math.radians(35),math.radians(8)))
                target=(.25,-.4,.9)
            if not beat_kind:
                target=(-.2+(i%3)*.4,-.35,1.8)
            shot(str(beat.get("camera") or sc.get("camera") or ""),bs,be,target,shot_no)
            shot_no+=1
        frame=end+1
    for o in list(bpy.data.objects):
        if o.animation_data and o.animation_data.action:
            for fc in o.animation_data.action.fcurves:
                for kp in fc.keyframe_points: kp.interpolation="BEZIER"
    scene.frame_set(1); bpy.ops.wm.save_as_mainfile(filepath=str(output.parent/"scene.blend"))
    print("CINEMATIC_RENDER_START", total_frames, fps, width, height, flush=True)
    result=bpy.ops.render.render(animation=True)
    print("CINEMATIC_RENDER_RESULT", result, flush=True)
    if "FINISHED" not in result: raise RuntimeError("Blender animation render did not finish")

if "--free-blender-render" in sys.argv:
    _blender_render()
