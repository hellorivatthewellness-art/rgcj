# Full-bleed 9:16 (1080x1920) versions of the virtuoso topic clips.
# Each shot is reframed: a 272x484 window (9:16) is taken from the picture area every shot
# shares (y 144-627) and positioned per shot (pans follow moving subjects).
# The end cards are too wide for that window, so they are shown whole on black.
# Burned-in subtitles are lifted from the letterbox bar and overlaid near the bottom.
import subprocess, sys
X=0.5
W,H,Y0=272,484,144
# (shot start, shot end, centre x at start, centre x at end) in source pixels / seconds
SHOTS=[(0,1.2,440,440),(1.2,3.0,720,720),(3.0,4.6,660,660),(4.6,5.4,640,640),
 (5.4,6.1,940,700),(6.1,6.8,680,680),(6.8,7.8,880,680),(7.8,8.8,880,900),(8.8,9.73,700,700),
 (9.73,10.93,740,740),(10.93,11.33,640,640),(11.33,12.33,360,360),(12.33,13.2,520,520),
 (13.2,14.0,600,600),(14.0,14.37,420,420),(14.37,15.17,900,900),(15.17,15.87,960,960),
 (15.87,16.47,640,640),(16.47,16.77,400,400),(16.77,17.37,340,340),(17.37,17.93,640,640),
 (17.93,18.4,680,680),(18.4,18.93,620,620),(18.93,19.2,640,640),(19.2,19.67,640,640),
 (19.67,20.13,780,780),(20.13,20.53,360,360),(20.53,20.93,640,640),(20.93,21.17,820,820),
 (21.17,21.53,640,640),(21.53,21.87,400,400),(21.87,22.47,640,640),(22.47,22.77,480,480),
 (22.77,23.57,640,640),(23.57,25.9,540,540),(25.9,27.9,700,700),(27.9,30.3,500,500),
 (30.3,32.7,420,420),(32.7,36.0,440,390)]
SUB="crop=520:40:380:650"; SW,SH=1040,80; SX,SY=(1080-SW)//2,1440
CARD="crop=680:536:300:92,scale=1080:851:flags=lanczos,pad=1080:1920:0:534:black"   # card text spans x 372-908
CLIPS={
 "clip1_virtuoso_full916":    [(0.00,10.93,None),(40.60,44.70,"all")],
 "clip2_giving-hope_full916": [(17.93,31.40,None),(40.60,44.70,"all")],
 "clip3_without-him_full916": [(11.33,17.37,None),(31.10,44.70,35.5)],
}
def xexpr(a):
    # crop x as a function of filter time t (source time = t + a)
    e="640"
    for s,f,c0,c1 in reversed(SHOTS):
        T=f"(t+{a})"
        cx=f"{c0}" if c0==c1 else f"({c0}+({c1}-{c0})*({T}-{s})/{f-s})"
        e=f"if(lt({T},{f}),{cx},{e})"
    return f"max(0,min({1280-W},{e}-{W//2}))"
def build(name,segs):
    n=len(segs); durs=[b-a for a,b,_ in segs]; total=sum(durs)-X*(n-1)
    inp=[];fc=[]
    for i,(a,b,card) in enumerate(segs):
        inp+=["-ss",f"{a}","-t",f"{b-a}","-i","src.mp4"]
        fc.append(f"[{i}:v]settb=AVTB,setpts=PTS-STARTPTS,fps=30,format=yuv420p,split=3[c{i}][k{i}][s{i}]")
        pic=f"crop=w={W}:h={H}:x='{xexpr(a)}':y={Y0},scale=1080:1920:flags=lanczos,setsar=1"
        if card=="all":
            fc.append(f"[c{i}]{CARD},setsar=1[p{i}];[k{i}]nullsink")
        elif card is None:
            fc.append(f"[c{i}]{pic}[p{i}];[k{i}]nullsink")
        else:
            fc.append(f"[c{i}]{pic}[pp{i}];[k{i}]{CARD},setsar=1[kk{i}];[pp{i}][kk{i}]overlay=0:0:enable='gte(t,{card-a:.2f})'[p{i}]")
        fc.append(f"[s{i}]{SUB},scale={SW}:{SH}:flags=lanczos,format=gray[m{i}]")
        fc.append(f"[{i}:a]asetpts=PTS-STARTPTS[a{i}]")
    v,m,a,off="p0","m0","a0",0
    for i in range(1,n):
        off+=durs[i-1]-X
        fc.append(f"[{v}][p{i}]xfade=transition=fade:duration={X}:offset={off:.3f}[vx{i}]")
        fc.append(f"[{m}][m{i}]xfade=transition=fade:duration={X}:offset={off:.3f}[mx{i}]")
        fc.append(f"[{a}][a{i}]acrossfade=d={X}:c1=qsin:c2=qsin[ax{i}]"); v,m,a=f"vx{i}",f"mx{i}",f"ax{i}"
    fc.append(f"[{m}]split[m1][m2]")
    fc.append(f"color=white:s={SW}x{SH}:r=30,format=rgba[w];[w][m1]alphamerge[txt]")
    fc.append(f"color=black:s={SW}x{SH}:r=30,format=rgba[bk];[m2]boxblur=6:2,lut=y='min(255,val*2.2)'[mb];[bk][mb]alphamerge,colorchannelmixer=aa=0.85[sh]")
    fc.append(f"[{v}][sh]overlay={SX}:{SY}:shortest=1[t1];[t1][txt]overlay={SX}:{SY}:shortest=1,format=yuv420p[v]")
    fc.append(f"[{a}]afade=t=in:d=0.05,afade=t=out:st={total-0.8:.2f}:d=0.8[au]")
    subprocess.run(["ffmpeg","-v","error","-y",*inp,"-filter_complex",";".join(fc),"-map","[v]","-map","[au]",
        "-c:v","libx264","-preset","slow","-crf","18","-profile:v","high","-r","30","-c:a","aac","-b:a","192k",
        "-ar","48000","-movflags","+faststart","-t",f"{total:.3f}",f"{name}.mp4"],check=True)
    print(name,f"{total:.2f}s")
for k,s in CLIPS.items():
    if len(sys.argv)<2 or k in sys.argv[1:]: build(k,s)
