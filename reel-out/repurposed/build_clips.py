import subprocess, sys
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
X=0.5  # crossfade seconds
PANEL_Y=330
CLIPS={
 "clip1_limited-life": dict(segs=[(1.70,30.00),(72.00,76.15)], hook_end=22.75,
     hook=["“But life, that's a", "very limited life.”"]),
 "clip2_no-smarter-than-you": dict(segs=[(31.30,42.45),(61.00,66.60),(72.30,76.15)], wide=[1],
     hook=["“...people that were", "no smarter than you.”"]),
 "clip3_push-and-it-pops-out": dict(segs=[(49.25,60.20),(67.70,76.15)],
     hook=["“If you push in, something", "will pop out the other side.”"]),
}
def build(name,c):
    segs=c["segs"]; n=len(segs)
    durs=[b-a for a,b in segs]; total=sum(durs)-X*(n-1)
    hook_end=c.get("hook_end",durs[0]-X)
    inp=[];fc=[]
    for i,(a,b) in enumerate(segs):
        inp+=["-ss",f"{a}","-t",f"{b-a}","-i","src.mp4"]
        panel=("crop=960:720:160:0,scale=680:510:flags=lanczos,pad=680:720:0:105:black" if i in c.get("wide",[])
               else "crop=680:720:300:0")
        fc.append(f"[{i}:v]settb=AVTB,setpts=PTS-STARTPTS,fps=30,{panel},setsar=1,format=yuv420p[v{i}]")
        fc.append(f"[{i}:a]asetpts=PTS-STARTPTS[a{i}]")
    vprev,aprev,off="v0","a0",0
    for i in range(1,n):
        off+=durs[i-1]-X
        fc.append(f"[{vprev}][v{i}]xfade=transition=fade:duration={X}:offset={off:.3f}[vx{i}]")
        fc.append(f"[{aprev}][a{i}]acrossfade=d={X}:c1=qsin:c2=qsin[ax{i}]")
        vprev,aprev=f"vx{i}",f"ax{i}"
    fc.append(f"[{vprev}]split[p1][p2]")
    fc.append(f"[p1]scale=1080:1144:flags=lanczos,setsar=1[fg]")
    fc.append(f"[p2]crop=255:720:212:0,scale=1080:1920,boxblur=40:2,eq=brightness=-0.22:saturation=0.8,setsar=1[bg]")
    alpha=f"if(lt(t,0.3),t/0.3,if(lt(t,{hook_end-0.3:.2f}),1,max(0,({hook_end:.2f}-t)/0.3)))"
    dt=[]
    for j,line in enumerate(c["hook"]):
        txt=line.replace("'", "’").replace(":", "\\:")
        dt.append(f"drawtext=fontfile={FONT}:text='{txt}':fontsize=54:fontcolor=white:alpha='{alpha}'"
                  f":shadowcolor=black@0.7:shadowx=3:shadowy=3:x=(w-text_w)/2:y={150+j*74}:enable='lt(t,{hook_end:.2f})'")
    fc.append(f"[bg][fg]overlay=0:{PANEL_Y},{','.join(dt)},format=yuv420p[v]")
    fc.append(f"[{aprev}]afade=t=in:d=0.08,afade=t=out:st={total-0.8:.2f}:d=0.8[au]")
    cmd=["ffmpeg","-v","error","-y",*inp,"-filter_complex",";".join(fc),"-map","[v]","-map","[au]",
         "-c:v","libx264","-preset","slow","-crf","18","-profile:v","high","-r","30",
         "-c:a","aac","-b:a","192k","-ar","48000","-movflags","+faststart","-t",f"{total:.3f}",f"{name}.mp4"]
    subprocess.run(cmd,check=True)
    print(name, f"{total:.2f}s", "hook until", f"{hook_end:.2f}")
for k,v in CLIPS.items():
    if len(sys.argv)<2 or k in sys.argv[1:]: build(k,v)
