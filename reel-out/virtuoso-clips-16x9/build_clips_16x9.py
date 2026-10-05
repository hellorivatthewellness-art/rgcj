# Full-frame 16:9 (1920x1080) versions of the virtuoso topic clips.
# The 2.39:1 picture is cropped to 16:9 from the area every shot shares (y 144-627),
# and the burned-in subtitles (letterbox bar, y 659-680) are lifted onto the picture.
import subprocess, sys
X=0.5
PIC="crop=860:484:210:144"       # 16:9 out of the common picture area, centred
SUB="crop=520:40:380:650"        # subtitles span x 396-882, y 659-680
SCALE=1920/860
SW,SH=round(520*SCALE),round(40*SCALE)
SX,SY=(1920-SW)//2, 1080-SH-60
CLIPS={
 "clip1_virtuoso_16x9":    [(0.00,10.93),(40.60,44.70)],
 "clip2_giving-hope_16x9": [(17.93,31.40),(40.60,44.70)],
 "clip3_without-him_16x9": [(11.33,17.37),(31.10,44.70)],
}
def build(name,segs):
    n=len(segs); durs=[b-a for a,b in segs]; total=sum(durs)-X*(n-1)
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
    fc.append(f"[{v}]split[s1][s2]")
    fc.append(f"[s1]{PIC},scale=1920:1080:flags=lanczos,setsar=1,format=yuv420p[pic]")
    # subtitle luma -> alpha: white text, plus a soft dark shadow for legibility on bright shots
    fc.append(f"[s2]{SUB},scale={SW}:{SH}:flags=lanczos,format=gray,split[m1][m2]")
    fc.append(f"color=white:s={SW}x{SH}:r=30,format=rgba[w];[w][m1]alphamerge[txt]")
    fc.append(f"color=black:s={SW}x{SH}:r=30,format=rgba[k];[m2]boxblur=6:2,lut=y='min(255,val*2.2)'[mb];[k][mb]alphamerge,colorchannelmixer=aa=0.85[sh]")
    fc.append(f"[pic][sh]overlay={SX}:{SY}:shortest=1[t1];[t1][txt]overlay={SX}:{SY}:shortest=1,format=yuv420p[v]")
    fc.append(f"[{a}]afade=t=in:d=0.05,afade=t=out:st={total-0.8:.2f}:d=0.8[au]")
    subprocess.run(["ffmpeg","-v","error","-y",*inp,"-filter_complex",";".join(fc),"-map","[v]","-map","[au]",
        "-c:v","libx264","-preset","slow","-crf","18","-profile:v","high","-r","30","-c:a","aac","-b:a","192k",
        "-ar","48000","-movflags","+faststart","-t",f"{total:.3f}",f"{name}.mp4"],check=True)
    print(name,f"{total:.2f}s")
for k,s in CLIPS.items():
    if len(sys.argv)<2 or k in sys.argv[1:]: build(k,s)
