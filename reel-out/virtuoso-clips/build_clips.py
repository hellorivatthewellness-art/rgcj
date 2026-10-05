# 9:16 topic clips from the letterboxed "virtuoso" film.
# Picture (y 92-627) and the burned-in subtitle strip (letterbox bar, y ~670-685) are cropped
# separately so the subtitles can be enlarged under the picture.
import subprocess, sys
X=0.5
PIC="crop=720:535:280:92"        # 720 wide centre of the 2.39:1 picture
SUB="crop=520:60:380:640"        # subtitles span x 396-882, y 659-680 (letterbox bar)
PIC_Y, SUB_Y = 496, 1299
CLIPS={
 "clip1_virtuoso":     dict(segs=[(0.00,10.93),(40.60,44.70)]),
 "clip2_giving-hope":  dict(segs=[(17.93,31.40),(40.60,44.70)]),
 "clip3_without-him":  dict(segs=[(11.33,17.37),(31.10,44.70)]),
}
def build(name,c):
    segs=c["segs"]; n=len(segs); durs=[b-a for a,b in segs]
    total=sum(durs)-X*(n-1)
    inp=[];fc=[]
    for i,(a,b) in enumerate(segs):
        inp+=["-ss",f"{a}","-t",f"{b-a}","-i","src.mp4"]
        fc.append(f"[{i}:v]settb=AVTB,setpts=PTS-STARTPTS,fps=30,format=yuv420p[v{i}]")
        fc.append(f"[{i}:a]asetpts=PTS-STARTPTS[a{i}]")
    v,a,off="v0","a0",0
    for i in range(1,n):
        off+=durs[i-1]-X
        fc.append(f"[{v}][v{i}]xfade=transition=fade:duration={X}:offset={off:.3f}[vx{i}]")
        fc.append(f"[{a}][a{i}]acrossfade=d={X}:c1=qsin:c2=qsin[ax{i}]"); v,a=f"vx{i}",f"ax{i}"
    fc.append(f"[{v}]split=3[s1][s2][s3]")
    fc.append(f"[s1]{PIC},scale=1080:803:flags=lanczos,setsar=1[pic]")
    fc.append(f"[s2]{SUB},scale=1080:125:flags=lanczos,setsar=1[sub]")
    fc.append(f"[s3]crop=300:535:490:92,scale=1080:1920,boxblur=40:2,eq=brightness=-0.25:saturation=0.8,setsar=1[bg]")
    fc.append(f"[bg][pic]overlay=0:{PIC_Y}[t1];[t1][sub]overlay=0:{SUB_Y},format=yuv420p[v]")
    fc.append(f"[{a}]afade=t=in:d=0.05,afade=t=out:st={total-0.8:.2f}:d=0.8[au]")
    subprocess.run(["ffmpeg","-v","error","-y",*inp,"-filter_complex",";".join(fc),"-map","[v]","-map","[au]",
        "-c:v","libx264","-preset","slow","-crf","18","-profile:v","high","-r","30","-c:a","aac","-b:a","192k",
        "-ar","48000","-movflags","+faststart","-t",f"{total:.3f}",f"{name}.mp4"],check=True)
    print(name,f"{total:.2f}s")
for k,c in CLIPS.items():
    if len(sys.argv)<2 or k in sys.argv[1:]: build(k,c)
