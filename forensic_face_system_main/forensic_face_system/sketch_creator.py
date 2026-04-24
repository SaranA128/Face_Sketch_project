"""
Forensic Face Sketch Builder – v6
• Realistic parts (head, hair, eyes, brows, nose, lips, mustache, beard)
• Each part is a separate object on canvas
• Select → move anywhere / resize with corner handle / delete
• Pencil draw on top for final details
• Undo / Redo / Save
"""
import tkinter as tk
from tkinter import messagebox, filedialog
import os, sys, math, random, copy, json, base64, io
from PIL import Image, ImageDraw, ImageFilter, ImageTk


# ─────────────────────────────────────────────────────────────────
# IMAGE-FILE BASED PART LOADER
# Loads real sketch images from  Face Sketch Elements/<cat>/ folder
# Files named: 01.png, 02.png, ... or Group 41.png, Group 42.png ...
# ─────────────────────────────────────────────────────────────────

def _sorted_images(folder):
    """Return sorted list of image paths in a folder."""
    if not os.path.isdir(folder):
        return []
    exts = {".png", ".jpg", ".jpeg", ".bmp", ".gif"}
    files = [f for f in os.listdir(folder)
             if os.path.splitext(f)[1].lower() in exts]
    # Sort: numbered first (01,02..), then Group XX
    def sort_key(name):
        stem = os.path.splitext(name)[0].strip()
        try:
            return (0, int(stem))
        except ValueError:
            # "Group 41" etc
            parts = stem.split()
            try:
                return (1, int(parts[-1]))
            except (ValueError, IndexError):
                return (2, stem)
    files.sort(key=sort_key)
    return [os.path.join(folder, f) for f in files]

# Map category name → subfolder name (matches your folder names)
CAT_FOLDER = {
    "Head":     "head",
    "Hair":     "hair",
    "Eyes":     "eyes",
    "Eyebrows": "eyebrows",
    "Nose":     "nose",
    "Lips":     "lips",
    "Mustache": "mustach",   # folder is "mustach" not "mustache"
    "Beard":    "more",      # beard-like items in "more" folder
}

# Cache: cat → list of PIL images (loaded on first use)
_IMG_CACHE = {}

def load_cat_images(cat):
    """Load all images for a category, return list of PIL RGBA images."""
    if cat in _IMG_CACHE:
        return _IMG_CACHE[cat]
    folder_name = CAT_FOLDER.get(cat, cat.lower())
    folder = os.path.join(ELEMENTS_DIR, folder_name)
    paths = _sorted_images(folder)
    imgs = []
    for p in paths:
        try:
            im = Image.open(p).convert("RGBA")
            imgs.append(im)
        except Exception:
            pass
    _IMG_CACHE[cat] = imgs
    return imgs

def load_image_part(cat, idx, W, H):
    """Load image part at index, resize to W×H, return PIL RGBA."""
    imgs = load_cat_images(cat)
    if not imgs:
        # Fallback: blank placeholder with label
        img = Image.new("RGBA", (W, H), (220, 220, 220, 255))
        return img
    img = imgs[idx % len(imgs)].copy()
    # Fit inside W×H preserving aspect ratio, on transparent bg
    img.thumbnail((W, H), Image.LANCZOS)
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ox = (W - img.width) // 2
    oy = (H - img.height) // 2
    canvas.paste(img, (ox, oy), img)
    return canvas

def count_cat_images(cat):
    """Return number of images available for a category."""
    imgs = load_cat_images(cat)
    return max(1, len(imgs))

BASE         = os.path.dirname(os.path.abspath(__file__))
SKETCH       = os.path.join(BASE, "sketches")
ELEMENTS_DIR = os.path.join(BASE, "Face Sketch Elements")
os.makedirs(SKETCH, exist_ok=True)

CW, CH  = 480, 600   # canvas dimensions
THUMB   = 90
random.seed(3)

# ─────────────────────────────────────────────────────────────────
# REALISTIC PART DRAWING FUNCTIONS
# Each returns PIL RGBA image
# ─────────────────────────────────────────────────────────────────
def _img(w, h):
    return Image.new("RGBA", (w, h), (0,0,0,0))

def _d(img):
    return ImageDraw.Draw(img)

def _arc(cx, cy, rx, ry, a0, a1, n=72):
    pts = []
    for i in range(n+1):
        t = math.radians(a0 + (a1-a0)*i/n)
        pts.append((int(cx+rx*math.cos(t)), int(cy+ry*math.sin(t))))
    return pts

INK = (22, 14, 6, 255)

# ══════════════ HEAD ══════════════
def draw_head(idx=0, W=260, H=340):
    img = _img(W, H); d = _d(img)
    cx = W//2; cy = H//2
    # shape table: (rx_ratio, ry_top, ry_bot, chin_narrow)
    S = [(0.42,0.44,0.46,0.04),(0.46,0.40,0.43,0.10),(0.37,0.45,0.47,0.02),
         (0.45,0.38,0.41,0.16),(0.43,0.42,0.44,0.05),(0.48,0.38,0.40,0.14),
         (0.35,0.46,0.48,0.01),(0.43,0.40,0.44,0.09),(0.40,0.43,0.47,0.18)]
    rxr,ryt,ryb,cn = S[idx%9]
    rx=int(W*rxr); ryt2=int(H*ryt); ryb2=int(H*ryb)

    # skin fill row by row for gradient
    for row in range(cy-ryt2, cy+ryb2):
        t = (row-cy+ryt2)/max(1,ryt2+ryb2)
        if t<0.5:
            frac=(t/0.5); hw=int(rx*(1-cn*(frac**2)*0.1))
        else:
            frac=((t-0.5)/0.5); hw=int(rx*(1-cn*(frac**2)))
        lx=cx-hw; rx2=cx+hw
        gv = int(228-t*22)
        d.line([(lx,row),(rx2,row)], fill=(gv, gv-10, gv-22, 255))

    # side shading
    for row in range(cy-ryt2, cy+ryb2):
        t=(row-cy+ryt2)/max(1,ryt2+ryb2)
        if t<0.5: hw=int(rx*(1-cn*(t/0.5)**2*0.1))
        else:     hw=int(rx*(1-cn*((t-0.5)/0.5)**2))
        for s in range(18):
            a=int(44*(1-s/18))
            d.point((cx-hw+s, row), fill=(145,118,88,a))
            d.point((cx+hw-s, row), fill=(145,118,88,a))

    # forehead highlight
    for row in range(cy-ryt2, cy-ryt2+int(ryt2*0.30)):
        t=(row-cy+ryt2)/(ryt2*0.30)
        hw=int(rx*0.28*(1-t))
        d.line([(cx-hw,row),(cx+hw,row)], fill=(255,250,242,int(22*(1-t))))

    # face outline – 3 layered strokes for pencil feel
    top_pts = _arc(cx,cy,rx,ryt2,180,360,90)
    bot_pts = _arc(cx,cy,rx,ryb2,0,180,90)
    for off,alpha,wid in [(0,255,2),(1,120,1),(-1,80,1)]:
        ox=random.randint(-1,1); oy=random.randint(-1,1)
        d.line([(x+ox,y+oy) for x,y in top_pts], fill=(22,14,6,alpha), width=wid)
        d.line([(x+ox,y+oy) for x,y in bot_pts], fill=(22,14,6,alpha), width=wid)

    # ears
    ey=cy-int(ryt2*0.06); eh=int(ryt2*0.42)
    for ex,sd in [(cx-rx,1),(cx+rx,-1)]:
        for a,aw in [(0,2),(1,1)]:
            pts_e=_arc(ex+sd*(7+a),ey, 10-a,eh-a*2, 90+35*sd,270+35*sd,28)
            d.line(pts_e, fill=(22,14,6,220-a*60), width=1)
        # inner
        d.arc([ex+sd*5-5,ey+eh//4,ex+sd*5+5,ey+3*eh//4],
              100+20*sd,260+20*sd, fill=(80,62,40,160), width=1)

    # neck
    nw=int(rx*0.40); ny=cy+ryb2-6
    for off in range(3):
        a2=[255,140,70][off]
        d.line([(cx-nw+off,ny),(cx-nw+off,H-2)], fill=(22,14,6,a2), width=1)
        d.line([(cx+nw-off,ny),(cx+nw-off,H-2)], fill=(22,14,6,a2), width=1)
    # collar shadow
    d.line([(cx-nw+4,H-14),(cx+nw-4,H-14)], fill=(80,62,40,100), width=1)

    return img

# ══════════════ HAIR ══════════════
def draw_hair(idx=0, W=300, H=200):
    img = _img(W, H); d = _d(img)
    cx = W//2
    HC  = (22,16,8,255)
    HC2 = (22,16,8,190)

    if idx == 0:  # side part classic
        # main mass
        d.arc([14,4,W-14,H+28], 180,360, fill=HC[:3], width=38)
        # hair strands sweeping to one side
        for x in range(16,W-16,5):
            t=(x-16)/(W-32)
            ys=int(6+14*math.sin(t*math.pi))+4
            ye=min(int(H*0.55), ys+int(62*abs(t-0.45)))
            ex=x+int(32*(t-0.5))+random.randint(-5,5)
            d.line([(x,ys),(ex,ye)], fill=(*HC[:3],185), width=1)
        # part line
        d.line([(cx-6,6),(cx-12,H*2//5)], fill=(248,244,238), width=3)

    elif idx == 1:  # short textured crop
        d.arc([14,4,W-14,H+20], 180,360, fill=HC[:3], width=30)
        for x in range(FCX2(W)-W//3*2, FCX2(W)+W//3*2, 4) if False else range(16,W-16,4):
            yt=int(4+8*abs(math.sin(x/W*math.pi*2)))
            for ll in range(0,20,4):
                dx2=random.randint(-3,3)
                d.line([(x,yt+ll),(x+dx2,yt+ll+4)], fill=(*HC[:3],200-ll*8), width=1)

    elif idx == 2:  # long flowing
        # mass
        d.arc([12,4,W-12,H+22], 180,360, fill=HC[:3], width=26)
        # long side strands
        for x in range(12,32,4):
            for y in range(H//3,H-4,5):
                d.point((x+random.randint(-1,2),y), fill=(*HC[:3],200))
        for x in range(W-32,W-12,4):
            for y in range(H//3,H-4,5):
                d.point((x+random.randint(-2,1),y), fill=(*HC[:3],200))
        # top strand lines
        for x in range(14,W-14,5):
            t=(x-14)/(W-28)
            ys=int(6+6*math.sin(t*math.pi))
            d.line([(x,ys),(x+random.randint(-4,4),H-6)], fill=(*HC[:3],170), width=1)

    elif idx == 3:  # wavy
        for i,bx in enumerate(range(6,W-6,48)):
            cy2=8+i*6
            d.arc([bx,cy2,bx+52,cy2+52], 180,360, fill=HC[:3], width=18)
        for x in range(10,W-10,5):
            t=(x-10)/(W-20)
            ys=8+int(14*math.sin(t*math.pi*2.5))
            d.line([(x,ys),(x+random.randint(-3,3),ys+int(52*math.sin(t*math.pi)))],
                   fill=(*HC[:3],182), width=1)

    elif idx == 4:  # spiky
        for i in range(9):
            bx=16+i*W//9; ty=6+i%3*12; sw=W//9-4
            d.polygon([(bx,H//2+6),(bx+sw//2,ty),(bx+sw,H//2+6)], fill=HC[:3])
            d.line([(bx+sw//2,H//2+4),(bx+sw//2,ty+4)], fill=(*HC[:3],180), width=1)

    elif idx == 5:  # curly
        for bx in range(14,W-14,24):
            for by in range(6,60,22):
                r=11+random.randint(-2,2)
                for a3 in range(0,360,10):
                    rad=math.radians(a3)
                    px=bx+int(r*math.cos(rad))+random.randint(-1,1)
                    py=by+int(r*math.sin(rad))+random.randint(-1,1)
                    d.point((px,py), fill=HC[:3])

    elif idx == 6:  # slicked back
        pts=[(14,H*2//5)]
        for x in range(14,W-14,4):
            t=(x-14)/(W-28); y=8+int(18*t*t)
            pts.append((x+random.randint(-1,1),y+random.randint(-1,1)))
        pts.append((W-14,H*2//5))
        d.polygon(pts, fill=HC[:3])
        for x in range(16,W-16,5):
            t=(x-16)/(W-32); y=8+int(18*t*t)
            d.line([(x,y),(x+int(46*t)+random.randint(-4,4),H*2//5-2)],
                   fill=(*HC[:3],150), width=1)

    elif idx == 7:  # bun / updo
        d.arc([14,4,W-14,H+16], 180,360, fill=HC[:3], width=18)
        d.ellipse([cx-24,2,cx+24,42], fill=HC[:3])
        for a4 in range(0,360,16):
            r2=20; rad=math.radians(a4)
            d.line([(cx+int(r2*.7*math.cos(rad)),21+int(r2*.5*math.sin(rad))),
                    (cx+int(r2*math.cos(rad)),21+int(r2*math.sin(rad)))],
                   fill=(*HC[:3],175), width=1)

    else:  # idx 8 – fade / undercut
        d.arc([18,6,W-18,H+10], 183,357, fill=(75,60,44), width=8)
        d.arc([14,4,W-14,H+14], 184,356, fill=HC[:3], width=22)
        for x in range(cx-40,cx+41,5):
            t=(x-cx+40)/80; ys=8+int(12*abs(t-0.5)*8)
            d.line([(x,ys),(x+random.randint(-2,2),H*2//5-2)],
                   fill=(*HC[:3],168), width=1)

    return img

def FCX2(W): return W//2

# ══════════════ EYES ══════════════
def draw_eyes(idx=0, W=260, H=80):
    img = _img(W, H); d = _d(img)
    cy = H//2 + 2
    lx, rx = W//2-58, W//2+58
    EWS=[38,40,36,44,38,46,34,40,36]
    EHS=[16,18,13,20,16,22,13,18,15]
    EW=EWS[idx%9]; EH=EHS[idx%9]

    for ex in [lx, rx]:
        # ── eye white shape ──
        top_pts = _arc(ex,cy, EW//2,EH//2, 180,360, 40)
        bot_pts = _arc(ex,cy, EW//2-2,EH//2+2, 0,180, 30)
        all_pts = top_pts + bot_pts
        d.polygon(all_pts, fill=(252,249,244,255))

        # corner shadow
        for s2 in range(10):
            a5=int(28*(1-s2/10))
            d.ellipse([ex-EW//2+s2-3,cy-EH//2+1,ex-EW//2+s2+3,cy+EH//2-1],
                      fill=(168,144,118,a5))
            d.ellipse([ex+EW//2-s2-3,cy-EH//2+1,ex+EW//2-s2+3,cy+EH//2-1],
                      fill=(168,144,118,a5))

        # iris gradient
        IR = max(5, int(EH*0.47))
        for r2 in range(IR,0,-1):
            t=(IR-r2)/IR
            gc=int(60+t*20); rc=int(50+t*15)
            d.ellipse([ex-r2,cy-r2,ex+r2,cy+r2],
                      fill=(rc,gc-10,gc-25,255))

        # iris lines
        for a6 in range(0,360,22):
            rad=math.radians(a6); r1=IR*.48; r2=IR*.88
            d.line([(int(ex+r1*math.cos(rad)),int(cy+r1*math.sin(rad))),
                    (int(ex+r2*math.cos(rad)),int(cy+r2*math.sin(rad)))],
                   fill=(38,26,12,88), width=1)

        # pupil
        PR=max(3,IR-5)
        d.ellipse([ex-PR,cy-PR,ex+PR,cy+PR], fill=(6,3,1,255))

        # catchlight
        d.ellipse([ex-PR+2,cy-PR+1,ex-PR+7,cy-PR+6], fill=(255,255,255,255))
        d.ellipse([ex+PR-4,cy+PR-3,ex+PR-1,cy+PR-1], fill=(200,200,200,110))

        # upper lid crease
        cr_pts=_arc(ex,cy, EW//2+4,EH//2+5, 195,345, 30)
        d.line(cr_pts, fill=(45,32,16,72), width=1)

        # upper lid – thick dark line
        for wpass,alpha,oy in [(3,255,0),(2,180,1),(1,90,2)]:
            lid=_arc(ex,cy, EW//2+1,EH//2+2, 192,348, 50)
            d.line([(x+random.randint(-1,1),y+oy) for x,y in lid],
                   fill=(18,10,4,alpha), width=wpass)

        # lower lid
        d.line(_arc(ex,cy, EW//2-1,EH//2, 8,172, 32),
               fill=(72,55,36,155), width=1)

        # eyelashes upper
        for i,ang in enumerate(range(196,346,13)):
            rad=math.radians(ang)
            ll=6+int(3*math.sin(math.radians(i*20)))
            x1e=int(ex+(EW//2+1)*math.cos(rad))
            y1e=int(cy+(EH//2+2)*math.sin(rad)*0.65)
            x2e=int(x1e+ll*math.cos(rad-math.radians(12)))
            y2e=int(y1e+ll*math.sin(rad-math.radians(12)))
            d.line([(x1e,y1e),(x2e,y2e)], fill=(14,8,2,225), width=1)

        # lower lashes
        for i,ang in enumerate(range(5,175,22)):
            rad=math.radians(ang); ll=3
            x1e=int(ex+(EW//2)*math.cos(rad))
            y1e=int(cy+(EH//2+1)*math.sin(rad))
            d.line([(x1e,y1e),(x1e+int(ll*math.cos(rad+math.radians(20))),
                                y1e+int(ll*math.sin(rad+math.radians(20))))],
                   fill=(55,40,22,160), width=1)

    return img

# ══════════════ EYEBROWS ══════════════
def draw_eyebrows(idx=0, W=260, H=55):
    img = _img(W, H); d = _d(img)
    cy=H-10; lx,rx=W//2-58,W//2+58
    BWS=[38,42,34,46,38,44,34,44,38]
    TKS=[4,5,3,6,4,5,3,5,4]
    BW=BWS[idx%9]; TK=TKS[idx%9]
    STYS=["arch","flat","thick","thin","angled","high","bushy","straight","peaked"]
    sty=STYS[idx%9]
    LIFTS={"arch":15,"flat":2,"thick":15,"thin":12,"angled":12,"high":24,"bushy":16,"straight":3,"peaked":20}
    lift=LIFTS.get(sty,14)

    for bx in [lx,rx]:
        tk2 = TK+3 if sty in("thick","bushy") else 1 if sty=="thin" else TK
        # main shape strokes
        for p in range(tk2+3):
            a7=int(225*(1-p/(tk2+4))); oy=p//2
            if sty in("flat","straight"):
                pts=[(bx-BW,cy-4+oy),(bx+BW,cy-4+oy)]
            elif sty=="angled":
                iy=cy-2 if bx<W//2 else cy-13
                oy2=cy-13 if bx<W//2 else cy-2
                pts=[(bx-BW,iy+oy),(bx+BW,oy2+oy)]
            else:
                pts=[]
                for x in range(bx-BW,bx+BW+1,3):
                    t=(x-(bx-BW))/(2*BW)
                    y=cy-int(lift*math.sin(t*math.pi))+oy
                    pts.append((x+random.randint(-1,1), y+random.randint(-1,1)))
            if len(pts)>1: d.line(pts, fill=(26,18,8,a7), width=1)

        # individual hair strokes
        for x in range(bx-BW, bx+BW, 3):
            t=(x-bx+BW)/(2*BW)
            if sty in("flat","straight"): by2=cy-4
            elif sty=="angled":
                by2=(cy-2 if bx<W//2 else cy-13)+ int(t*(10 if bx<W//2 else -10))
            else:
                by2=cy-int(lift*math.sin(t*math.pi))
            dx3=int(2*(t-0.5)*2)
            d.line([(x,by2),(x+dx3,by2-random.randint(3,7))],
                   fill=(26,18,8,random.randint(155,228)), width=1)

    return img

# ══════════════ NOSE ══════════════
def draw_nose(idx=0, W=110, H=130):
    img = _img(W, H); d = _d(img)
    cx,cy=W//2,H//2
    BWS=[26,30,20,22,26,32,20,20,30]
    BHS=[58,52,64,46,60,44,66,48,56]
    BW=BWS[idx%9]; BH=BHS[idx%9]
    ny=cy+BH//2-22
    LC=(95,76,56,195)

    # Bridge shading
    for row in range(cy-BH//2,ny):
        t=(row-(cy-BH//2))/max(1,ny-(cy-BH//2))
        sh=int(16*math.sin(t*math.pi))
        for sd,sx in [(-1,cx-8),(1,cx+8)]:
            for s3 in range(5):
                d.point((sx+sd*s3,row), fill=(90,70,48,int(sh*(1-s3/5))))

    # Bridge lines – multiple strokes
    for sd,sx in [(-1,cx-3),(1,cx+3)]:
        for pw in range(3):
            a8=[200,110,55][pw]; ox=pw-1
            bl=[]
            for y in range(cy-BH//2,ny,3):
                t=(y-(cy-BH//2))/max(1,ny-(cy-BH//2))
                fl=int(t*t*BW*.16)
                bl.append((sx+sd*fl+ox+random.randint(-1,1),y))
            d.line(bl, fill=(*LC[:3],a8), width=1)

    # tip arc
    for pw in range(3):
        oy=pw
        d.arc([cx-BW//2-3,ny-8+oy,cx+BW//2+3,ny+10+oy],
              180,360, fill=(*LC[:3],200-pw*55), width=1)

    # nostrils
    for sd,nx in [(-1,cx-BW//2-5),(1,cx+BW//2+5)]:
        # shadow fill
        d.ellipse([nx-7,ny+1,nx+7,ny+15], fill=(128,100,74,90))
        # outline arcs
        for pw in range(2):
            d.arc([nx-8+sd,ny+pw,nx+6+sd,ny+17+pw],
                  12+sd*162,202+sd*158, fill=(*LC[:3],195-pw*55), width=1)
        # ala curve
        pts_a=_arc(nx-sd*2,ny+2,5,8,215+sd*88,308+sd*88,14)
        d.line(pts_a, fill=(*LC[:3],168), width=1)

    # base line
    d.line([(cx-BW-2,ny+13),(cx+BW+2,ny+13)], fill=(*LC[:3],100), width=1)

    return img

# ══════════════ LIPS ══════════════
def draw_lips(idx=0, W=160, H=80):
    img = _img(W, H); d = _d(img)
    cx,cy=W//2,H//2+2
    UWS=[50,54,44,58,48,52,46,56,42]
    LWS=[44,48,38,52,42,46,40,50,36]
    UHS=[12,14,10,15,12,14,10,15,10]
    LHS=[13,15,11,17,13,15,11,17,12]
    UW=UWS[idx%9]; LW=LWS[idx%9]; UH=UHS[idx%9]; LH=LHS[idx%9]
    LC=(148,82,82,228); DC=(115,48,48,255)
    FU=(185,112,108,172); FL=(192,120,112,190)

    # fill upper
    upts=[]
    for x in range(cx-UW,cx+UW+1,3):
        t=(x-cx+UW)/(2*UW)
        y=cy-int(UH*math.sin(t*math.pi)*(1-abs(2*t-1)*0.14))
        upts.append((x,y))
    upts+=[(cx+UW,cy),(cx-UW,cy)]
    if len(upts)>3: d.polygon(upts, fill=FU)

    # fill lower
    lpts=[(cx-LW,cy)]
    for x in range(cx-LW,cx+LW+1,3):
        t=(x-cx+LW)/(2*LW)
        y=cy+int(LH*math.sin(t*math.pi))
        lpts.append((x,y))
    lpts.append((cx+LW,cy))
    if len(lpts)>3: d.polygon(lpts, fill=FL)

    # lower highlight
    for x in range(cx-LW//3,cx+LW//3,2):
        t=(x-cx+LW//3)/(2*LW//3)
        y=cy+int(LH*.48*math.sin(t*math.pi))
        d.line([(x,y),(x,y+2)], fill=(255,228,218,int(54*(1-abs(2*t-1)))))

    # outline – multiple strokes
    for pw,alpha,oy in [(3,255,0),(2,155,1),(1,75,2)]:
        ul=[(x,cy-int(UH*math.sin((x-cx+UW)/UW*math.pi))+oy+random.randint(-1,1))
            for x in range(cx-UW,cx+1,3)]
        ur=[(x,cy-int(UH*math.sin((cx+UW-x)/UW*math.pi))+oy+random.randint(-1,1))
            for x in range(cx,cx+UW+1,3)]
        la=[(x,cy+int(LH*math.sin((x-cx+LW)/(2*LW)*math.pi))+oy+random.randint(-1,1))
            for x in range(cx-LW,cx+LW+1,3)]
        if len(ul)>1: d.line(ul, fill=(*DC[:3],alpha), width=pw)
        if len(ur)>1: d.line(ur, fill=(*DC[:3],alpha), width=pw)
        if len(la)>1: d.line(la, fill=(*DC[:3],alpha), width=pw)

    # center line + philtrum
    d.line([(cx-UW+5,cy+1),(cx+UW-5,cy+1)], fill=(*DC[:3],175), width=1)
    for sd2 in [-1,1]:
        d.line([(cx+sd2*5,cy-UH-8),(cx+sd2*3,cy-1)], fill=(85,66,44,110), width=1)

    return img

# ══════════════ MUSTACHE ══════════════
def draw_mustache(idx=0, W=170, H=70):
    img = _img(W, H); d = _d(img)
    cx,cy=W//2,H//2+5
    DK=(25,16,8,255)
    STYS=["chevron","handlebar","pencil","walrus","fu_manchu",
          "english","painter","natural","imperial"]
    sty=STYS[idx%9]

    def ms(pts,ww=2,al=218):
        if len(pts)>1:
            d.line([(x+random.randint(-1,1),y+random.randint(-1,1)) for x,y in pts],
                   fill=(*DK[:3],al), width=ww)

    if sty=="chevron":
        for sg in [-1,1]:
            pts=[(cx,cy)]+[(cx+sg*(4+i*4),cy-int(10*math.sin(i/12*math.pi)))
                           for i in range(1,13)]
            for ww in [5,3,1]: ms(pts,ww,int(215*(6-ww)/6))
    elif sty=="handlebar":
        for sg in [-1,1]:
            pts=[(cx,cy)]+[(cx+sg*(4+i*4),cy-int(8*math.sin(i/10*math.pi)))
                           for i in range(1,11)]
            pts+=[(pts[-1][0]+sg*4,pts[-1][1]+6),(pts[-1][0]+sg*4,pts[-1][1]+6)]
            for ww in [4,2,1]: ms(pts,ww)
    elif sty=="pencil":
        ms([(cx-46,cy-1),(cx+46,cy-1)],3)
        ms([(cx-44,cy+2),(cx+44,cy+2)],2,130)
    elif sty=="walrus":
        for thick in range(12,0,-2):
            pts=[(cx-44+i*4,cy-int(8*math.sin(i/22*math.pi))) for i in range(22)]
            ms(pts,thick,int(205*(thick/12)))
    elif sty=="fu_manchu":
        for sg in [-1,1]:
            pts=[(cx,cy)]+[(cx+sg*(4+i*4),cy-int(6*math.sin(i/11*math.pi)))
                           for i in range(1,11)]
            pts+=[(pts[-1][0],pts[-1][1]+i*4) for i in range(1,6)]
            for ww in [3,2,1]: ms(pts,ww)
    else:  # english, painter, natural, imperial
        pts=[(cx-44+i*4,cy-int(10*math.sin(i/22*math.pi))) for i in range(22)]
        for ww in [5,4,3,2,1]: ms(pts,ww,int(215*(6-ww)/6))

    # hair strokes on top
    for x in range(cx-42,cx+43,4):
        t=(x-cx+42)/84
        by3=cy-int(10*math.sin(t*math.pi)) if sty!="pencil" else cy
        d.line([(x,by3),(x+random.randint(-2,2),by3-random.randint(3,6))],
               fill=(*DK[:3],random.randint(140,215)), width=1)

    return img

# ══════════════ BEARD ══════════════
def draw_beard(idx=0, W=240, H=180):
    img = _img(W, H); d = _d(img)
    cx=W//2; DK=(28,20,10,220)
    STYS=["full","goatee","stubble","chin_strap","van_dyke",
          "circle","anchor","short_box","long_full"]
    sty=STYS[idx%9]

    def ht(x0,y0,x1,y1):
        for x in range(x0,x1,5):
            for y in range(y0,y1,5):
                dx4=(x-cx); dy4=(y-22)
                if dx4*dx4/78**2+dy4*dy4/62**2<1:
                    d.line([(x,y),(x+random.randint(-3,3),y+random.randint(4,9))],
                           fill=(*DK[:3],random.randint(128,212)), width=1)

    if sty=="full":
        p1=_arc(cx,0,int(W*.44),8,180,360,60)
        p2=_arc(cx,H-16,int(W*.44),H-16,0,180,60)
        if len(p1)>2 and len(p2)>2:
            d.polygon(p1+list(reversed(p2)), fill=(*DK[:3],196))
        ht(18,6,W-18,H-18); d.line(p1,fill=INK,width=2); d.line(p2,fill=INK,width=2)
    elif sty=="goatee":
        d.ellipse([cx-26,8,cx+26,92], fill=(*DK[:3],196))
        ht(cx-24,10,cx+24,90); d.line(_arc(cx,50,26,42,0,360,40),fill=INK,width=2)
    elif sty=="stubble":
        random.seed(idx*11+3)
        for _ in range(500):
            x=random.randint(14,W-14); y=random.randint(6,H-22)
            if (x-cx)**2/76**2+(y-28)**2/60**2<1:
                d.ellipse([x,y,x+2,y+4], fill=(*DK[:3],random.randint(78,158)))
    elif sty=="chin_strap":
        for sk in range(10):
            a9=int(205*(1-sk/11))
            d.line(_arc(cx,0,int(W*.44)-sk,H-10-sk,0,180,50),
                   fill=(*DK[:3],a9), width=2)
    elif sty=="van_dyke":
        d.ellipse([cx-26,6,cx+26,58], fill=(*DK[:3],196)); ht(cx-24,8,cx+24,56)
        d.ellipse([cx-15,56,cx+15,116], fill=(*DK[:3],196)); ht(cx-13,58,cx+13,114)
        d.line(_arc(cx,32,26,26,0,360,30),fill=INK,width=2)
        d.line(_arc(cx,86,15,30,0,360,30),fill=INK,width=2)
    elif sty in("circle","anchor"):
        d.line(_arc(cx,28,28,28,0,360,40),fill=INK,width=3)
        for sk in range(10):
            d.line(_arc(cx,28,28+sk,28+sk,0,360,36), fill=(*DK[:3],int(180*(1-sk/11))), width=1)
    elif sty=="short_box":
        p1b=_arc(cx,0,int(W*.44),10,0,180,50)
        for sk in range(10):
            d.line(_arc(cx,0,int(W*.44)-sk,10+sk,2,178,48),
                   fill=(*DK[:3],int(195*(1-sk/11))), width=1)
        d.ellipse([cx-30,8,cx+30,62], fill=(*DK[:3],196)); ht(cx-28,10,cx+28,60)
    else:  # long_full
        p1c=_arc(cx,0,int(W*.46),8,180,360,60)
        p2c=_arc(cx,H-8,int(W*.44),H-8,0,180,60)
        if len(p1c)>2 and len(p2c)>2:
            d.polygon(p1c+list(reversed(p2c)), fill=(*DK[:3],205))
        ht(16,4,W-16,H-10); d.line(p1c,fill=INK,width=2); d.line(p2c,fill=INK,width=2)

    return img

# ─────────────────────────────────────────────────────────────────
# CATALOGUE
# ─────────────────────────────────────────────────────────────────
# CATS now uses image-file loader.
# Count is dynamic (from actual folder contents).
# draw function is load_image_part (universal).
# Sizes chosen to match typical sketch proportions.
CATS = [
    ("Head",     load_image_part, count_cat_images("Head"),     260, 340),
    ("Hair",     load_image_part, count_cat_images("Hair"),     280, 220),
    ("Eyes",     load_image_part, count_cat_images("Eyes"),     260,  90),
    ("Eyebrows", load_image_part, count_cat_images("Eyebrows"), 260,  70),
    ("Nose",     load_image_part, count_cat_images("Nose"),     130, 160),
    ("Lips",     load_image_part, count_cat_images("Lips"),     180,  90),
    ("Mustache", load_image_part, count_cat_images("Mustache"), 180,  90),
    ("Beard",    load_image_part, count_cat_images("Beard"),    240, 180),
]
ICON = {"Head":"👤","Hair":"💇","Eyes":"👁","Eyebrows":"〰",
        "Nose":"👃","Lips":"👄","Mustache":"🥸","Beard":"🧔"}

# Default positions on canvas (cx_frac, cy_frac)
DEFAULT_POS = {
    "Head":     (0.50, 0.50),
    "Hair":     (0.50, 0.17),
    "Eyes":     (0.50, 0.44),
    "Eyebrows": (0.50, 0.37),
    "Nose":     (0.50, 0.57),
    "Lips":     (0.50, 0.69),
    "Mustache": (0.50, 0.63),
    "Beard":    (0.50, 0.81),
}

def make_thumb(cat_name, fn, idx):
    """Generate thumbnail — uses image file loader for real sketches."""
    imgs = load_cat_images(cat_name)
    if imgs:
        pil = imgs[idx % len(imgs)].copy()
        pil.thumbnail((THUMB, THUMB), Image.LANCZOS)
        bg = Image.new("RGB", (THUMB, THUMB), (248, 244, 238))
        if pil.mode == "RGBA":
            bg.paste(pil, ((THUMB-pil.width)//2, (THUMB-pil.height)//2), pil)
        else:
            bg.paste(pil, ((THUMB-pil.width)//2, (THUMB-pil.height)//2))
    else:
        # Fallback programmatic
        pil = fn(cat_name, idx, THUMB, THUMB)
        bg = Image.new("RGB", (THUMB, THUMB), (248, 244, 238))
        if pil.mode == "RGBA":
            bg.paste(pil, (0, 0), pil)
        else:
            bg.paste(pil)
    return ImageTk.PhotoImage(bg)

# ─────────────────────────────────────────────────────────────────
# APP
# ─────────────────────────────────────────────────────────────────
class SketchApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Sketch Generation – Forensic Face Sketch Builder")
        self.root.configure(bg="#eef2f7")
        self.root.state("zoomed")

        # objects: list of dict {cat,idx,fn,x,y,w,h,alpha,fliph,pil}
        self.objects    = []
        self.sel        = -1
        self.undo_stack = []
        self.redo_stack = []
        self.tool       = "select"
        self.draw_pts   = []
        self.draw_size  = 2
        self.draw_color = (20,12,4)
        self._drag_obj  = -1
        self._drag_ox   = 0
        self._drag_oy   = 0
        self._resizing  = False
        self._res_start = None
        self._tcache    = {}
        self.cur_cat    = "Head"
        self._face_tk   = None

        self._build()
        self._show_gal("Head")
        self._render()
        self.root.mainloop()

    # ── UI ──────────────────────────────────────────────────────
    def _build(self):
        # SIDEBAR
        side = tk.Frame(self.root, bg="#f0f5fc", width=84)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)

        # Sidebar header
        tk.Label(side, text="PARTS", bg="#f0f5fc", fg="#1565c0",
                 font=("Courier",8,"bold")).pack(pady=(8,4))
        tk.Frame(side,bg="#00ff33",height=1).pack(fill="x",padx=4)

        for cname,fn,n,dw,dh in CATS:
            fr = tk.Frame(side, bg="#f0f5fc", cursor="hand2")
            fr.pack(fill="x", pady=1, padx=2)
            lbl_icon=tk.Label(fr,text=ICON[cname],bg="#f0f5fc",
                     font=("Segoe UI Emoji",18))
            lbl_icon.pack()
            lbl_txt=tk.Label(fr,text=cname,bg="#f0f5fc",fg="#1565c0",
                     font=("Courier",7))
            lbl_txt.pack()
            for w in [fr,lbl_icon,lbl_txt]:
                w.bind("<Button-1>",lambda e,c=cname:self._show_gal(c))
                w.bind("<Enter>",lambda e,f=fr:f.configure(bg="#0d1f10"))
                w.bind("<Leave>",lambda e,f=fr:f.configure(bg="#f0f5fc"))

        # TOOLBAR - Two Row Layout to fit all buttons
        tb_bg = "#f0f5fc"
        tb = tk.Frame(self.root, bg=tb_bg)
        tb.pack(side="top", fill="x")
        
        tbr1 = tk.Frame(tb, bg=tb_bg)
        tbr1.pack(side="top", fill="x")
        tbr2 = tk.Frame(tb, bg=tb_bg)
        tbr2.pack(side="top", fill="x")
        
        tk.Frame(tb, bg="#00cc55", height=2).pack(side="bottom", fill="x")

        def B(parent, t, cmd, bg2="#e8f0fc", fg2="#00cc55", **kw):
            # On macOS, standard Button background is tricky; we use highlightbackground to remove the border 'halo'
            b = tk.Button(parent, text=t, command=cmd, bg=bg2, fg=fg2,
                         activebackground="#1a3a1a", font=("Courier", 9, "bold"),
                         relief="flat", padx=8, pady=4, cursor="hand2",
                         highlightthickness=0, bd=0, highlightbackground=tb_bg, **kw)
            b.pack(side="left", padx=4, pady=4)
            b.bind("<Enter>", lambda e, btn=b, ob=bg2: btn.configure(bg="#d0e4f8"))
            b.bind("<Leave>", lambda e, btn=b, ob=bg2: btn.configure(bg=ob))
            return b

        def SEP(parent): 
            tk.Frame(parent, bg="#00ff33", width=1).pack(side="left", fill="y", pady=6, padx=4)

        # Row 1: Tools & Basic Actions
        B(tbr1, "← Menu", self._back_menu, bg2="#f5f9ff", fg2="#546e7a")
        SEP(tbr1)
        self.bsel = B(tbr1, "↖ Select", lambda: self._set_tool("select"))
        self.bpen = B(tbr1, "✏ Pencil",  lambda: self._set_tool("pencil"))
        self.bers = B(tbr1, "◻ Eraser",  lambda: self._set_tool("eraser"))
        SEP(tbr1)
        B(tbr1, "↩ Undo", self._undo)
        B(tbr1, "↪ Redo", self._redo)
        SEP(tbr1)
        B(tbr1, "↑ Front", self._front)
        B(tbr1, "↓ Back", self._back_z)
        B(tbr1, "⇄ Flip H", self._flip)
        SEP(tbr1)
        B(tbr1, "🗑 Del", self._delete, bg2="#ffebee", fg2="#c62828")
        B(tbr1, "Clear", self._clear, bg2="#fff3e0", fg2="#e65100")

        # Row 2: Controls & Project Management
        tk.Label(tbr2, text="Brush:", bg=tb_bg, fg="#1565c0",
                 font=("Courier", 8)).pack(side="left", padx=(10, 1))
        self.sz = tk.IntVar(value=2)
        tk.Scale(tbr2, variable=self.sz, from_=1, to=28, orient="horizontal",
                 bg=tb_bg, fg="#1565c0", troughcolor="#e8f0fc",
                 highlightthickness=0, length=100, showvalue=True,
                 command=lambda v: setattr(self, "draw_size", int(v))
                 ).pack(side="left")
        
        tk.Label(tbr2, text="Opacity:", bg=tb_bg, fg="#1565c0",
                 font=("Courier", 8)).pack(side="left", padx=(15, 1))
        self.op = tk.IntVar(value=100)
        tk.Scale(tbr2, variable=self.op, from_=10, to=100, orient="horizontal",
                 bg=tb_bg, fg="#1565c0", troughcolor="#e8f0fc",
                 highlightthickness=0, length=100,
                 command=self._op_change).pack(side="left")
        
        SEP(tbr2)
        B(tbr2, "📂 Open", self._open_saved, bg2="#e3f2fd", fg2="#0288d1")
        B(tbr2, "💾 Save", self._save, bg2="#e8f5e9", fg2="#2e7d32")
        SEP(tbr2)
        B(tbr2, "📥 Load Draft", self._load_draft, bg2="#fff9c4", fg2="#fbc02d")
        B(tbr2, "📤 Save Draft", self._save_draft, bg2="#e1f5fe", fg2="#0288d1")
        SEP(tbr2)
        B(tbr2, "🔍 Match", self._compare, bg2="#e8eaf6", fg2="#0288d1")

        self._upd_btns()

        # CANVAS
        cf = tk.Frame(self.root,bg="#eef2f7")
        cf.pack(side="left",fill="both",expand=True,padx=6,pady=6)

        # canvas title
        tk.Label(cf,text="◉  SKETCH CANVAS  — Select parts, adjust, then pencil draw",
            bg="#eef2f7",fg="#2c6aa0",font=("Courier",9)).pack(anchor="w",pady=(0,4))

        self.cv = tk.Canvas(cf, width=CW, height=CH,
                            bg="#f7f3ec",
                            highlightthickness=2,
                            highlightbackground="#00cc55",
                            cursor="arrow")
        self.cv.pack(expand=True)
        self.cv.bind("<ButtonPress-1>",   self._press)
        self.cv.bind("<B1-Motion>",       self._drag)
        self.cv.bind("<ButtonRelease-1>", self._release)
        self.cv.bind("<Motion>",          self._motion)

        # GALLERY
        rp = tk.Frame(self.root,bg="#eef2f7",width=310)
        rp.pack(side="left",fill="y"); rp.pack_propagate(False)

        self.cv_lbl=tk.StringVar(value="HEAD STYLES")
        tk.Label(rp,textvariable=self.cv_lbl,bg="#eef2f7",fg="#1565c0",
                 font=("Courier",10,"bold")).pack(pady=(8,1))
        tk.Label(rp,text="Click to add  •  Drag onto canvas",
                 bg="#eef2f7",fg="#224433",font=("Courier",7)).pack()

        gf=tk.Frame(rp,bg="#f0f5fc",relief="flat",bd=1)
        gf.pack(fill="both",expand=True,padx=6,pady=4)
        self.gcv=tk.Canvas(gf,bg="#f0f5fc",highlightthickness=0)
        sb=tk.Scrollbar(gf,orient="vertical",command=self.gcv.yview,
                        bg="#f0f5fc",troughcolor="#e8f0fc")
        self.gcv.configure(yscrollcommand=sb.set)
        sb.pack(side="right",fill="y"); self.gcv.pack(side="left",fill="both",expand=True)
        self.gi=tk.Frame(self.gcv,bg="#f0f5fc")
        self.gcv.create_window((0,0),window=self.gi,anchor="nw")
        self.gi.bind("<Configure>",lambda e:self.gcv.configure(scrollregion=self.gcv.bbox("all")))

        self.sv=tk.StringVar(value="● Select parts from gallery  •  Drag to move  •  Corner handle to resize  •  Pencil to draw")
        tk.Label(self.root,textvariable=self.sv,bg="#1565c0",fg="#2c6aa0",
                 font=("Courier",8),anchor="w").pack(side="bottom",fill="x",ipady=3)

    def _set_tool(self,t):
        self.tool=t; self._upd_btns()
        self.cv.configure(cursor="crosshair" if t in("pencil","eraser") else "arrow")
        self.sv.set(f"Tool: {t.capitalize()}")

    def _upd_btns(self):
        for b,n in [(self.bsel,"select"),(self.bpen,"pencil"),(self.bers,"eraser")]:
            b.configure(bg="#1565c0" if self.tool==n else "#e8f0fc")

    # ── GALLERY ──────────────────────────────────────────────────
    def _show_gal(self,cat):
        self.cur_cat=cat
        self.cv_lbl.set(f"{cat.upper()} STYLES")
        for w in self.gi.winfo_children(): w.destroy()
        cat_info=next((x for x in CATS if x[0]==cat),None)
        if not cat_info: return
        cname,fn,n,dw,dh=cat_info

        for idx in range(n):
            key=(cat,idx)
            if key not in self._tcache:
                self._tcache[key]=make_thumb(cat,fn,idx)
            ti=self._tcache[key]
            lb=tk.Label(self.gi,image=ti,bg="#ddeaf8",relief="flat",bd=2,
                        highlightbackground="#00cc55",
                        highlightthickness=1,cursor="hand2")
            lb.grid(row=idx//3,column=idx%3,padx=3,pady=3)
            lb.bind("<Button-1>",lambda e,c=cat,i=idx:self._add(c,i))
            lb.bind("<ButtonPress-1>",lambda e,c=cat,i=idx:self._gal_drag(e,c,i))
            lb.bind("<Enter>",lambda e,l=lb:l.configure(highlightbackground="#00ff66"))
            lb.bind("<Leave>",lambda e,l=lb:l.configure(highlightbackground="#00cc55"))

    # ── ADD (click) ───────────────────────────────────────────────
    def _add(self,cat,idx):
        self._snap()
        cat_info=next((x for x in CATS if x[0]==cat),None)
        if not cat_info: return
        cname,fn,n,dw,dh=cat_info
        cx_f,cy_f=DEFAULT_POS.get(cat,(0.5,0.5))
        pil=fn(cat,idx,dw,dh)
        ox=int(cx_f*CW)-dw//2; oy=int(cy_f*CH)-dh//2
        self.objects.append(dict(cat=cat,idx=idx,fn=fn,
            x=ox,y=oy,w=dw,h=dh,alpha=100,fliph=False,pil=pil))
        self.sel=len(self.objects)-1
        self.op.set(100); self._render()
        self.sv.set(f"Added {cat} style {idx+1}  •  Drag to reposition")

    # ── DRAG FROM GALLERY ─────────────────────────────────────────
    def _gal_drag(self,e,cat,idx):
        key=(cat,idx)
        ghost=tk.Toplevel(self.root)
        ghost.overrideredirect(True)
        ghost.attributes("-topmost",True)
        ghost.attributes("-alpha",0.68)
        tk.Label(ghost,image=self._tcache[key],bg="white").pack()
        ghost.geometry(f"+{e.x_root-THUMB//2}+{e.y_root-THUMB//2}")
        def mv(ev): ghost.geometry(f"+{ev.x_root-THUMB//2}+{ev.y_root-THUMB//2}")
        def up(ev):
            ghost.destroy()
            self.root.unbind("<B1-Motion>"); self.root.unbind("<ButtonRelease-1>")
            cx0=self.cv.winfo_rootx(); cy0=self.cv.winfo_rooty()
            if cx0<=ev.x_root<=cx0+self.cv.winfo_width() and \
               cy0<=ev.y_root<=cy0+self.cv.winfo_height():
                dx=ev.x_root-cx0; dy=ev.y_root-cy0
                self._snap()
                cat_info=next((x for x in CATS if x[0]==cat),None)
                if not cat_info: return
                cname,fn,n,dw,dh=cat_info
                pil=fn(cat,idx,dw,dh)
                self.objects.append(dict(cat=cat,idx=idx,fn=fn,
                    x=dx-dw//2,y=dy-dh//2,w=dw,h=dh,
                    alpha=100,fliph=False,pil=pil))
                self.sel=len(self.objects)-1
                self.op.set(100); self._render()
        self.root.bind("<B1-Motion>",mv)
        self.root.bind("<ButtonRelease-1>",up)

    # ── CANVAS EVENTS ─────────────────────────────────────────────
    def _press(self,e):
        x,y=e.x,e.y
        if self.tool=="select":
            # check resize handle
            if 0<=self.sel<len(self.objects):
                o=self.objects[self.sel]
                if abs(x-o["x"]-o["w"])<=10 and abs(y-o["y"]-o["h"])<=10:
                    self._resizing=True
                    self._res_start=(x,y,o["w"],o["h"]); return
            # hit test top→bottom
            hit=-1
            for i in range(len(self.objects)-1,-1,-1):
                o=self.objects[i]
                if o["x"]<=x<=o["x"]+o["w"] and o["y"]<=y<=o["y"]+o["h"]:
                    hit=i; break
            self.sel=hit
            if hit>=0:
                o=self.objects[hit]
                self._drag_obj=hit
                self._drag_ox=x-o["x"]; self._drag_oy=y-o["y"]
                self.op.set(o["alpha"])
            self._render()
        elif self.tool in("pencil","eraser"):
            self._snap(); self.draw_pts=[(x,y)]

    def _drag(self,e):
        x,y=e.x,e.y
        if self.tool=="select":
            if self._resizing and 0<=self.sel<len(self.objects):
                o=self.objects[self.sel]
                sx,sy,sw,sh=self._res_start
                nw=max(30,sw+(x-sx)); nh=max(30,sh+(y-sy))
                # regenerate PIL at new size (if fn available), else just resize
                if o.get("fn"):
                    o["pil"]=o["fn"](o["cat"],o["idx"],nw,nh)
                o["w"]=nw; o["h"]=nh; self._render()
            elif self._drag_obj>=0:
                o=self.objects[self._drag_obj]
                o["x"]=x-self._drag_ox; o["y"]=y-self._drag_oy
                self._render()
        elif self.tool in("pencil","eraser"):
            self.draw_pts.append((x,y))
            # live preview
            col="white" if self.tool=="eraser" else "#140e06"
            sz=self.draw_size*3 if self.tool=="eraser" else self.draw_size
            self.cv.create_line(self.draw_pts,fill=col,width=sz,
                                smooth=True,capstyle="round",joinstyle="round")

    def _release(self,e):
        if self._resizing: self._resizing=False; return
        if self._drag_obj>=0: self._drag_obj=-1; return
        if self.tool in("pencil","eraser") and len(self.draw_pts)>1:
            col=(255,255,255) if self.tool=="eraser" else self.draw_color
            sz=self.draw_size*3 if self.tool=="eraser" else self.draw_size
            self.objects.append(dict(cat="stroke",idx=0,fn=None,
                pts=list(self.draw_pts),color=col,size=sz,
                x=0,y=0,w=CW,h=CH,alpha=100,fliph=False,pil=None))
            self.draw_pts=[]; self._render()

    def _motion(self,e):
        if 0<=self.sel<len(self.objects):
            o=self.objects[self.sel]
            if abs(e.x-o["x"]-o["w"])<=10 and abs(e.y-o["y"]-o["h"])<=10:
                self.cv.configure(cursor="sizing"); return
        self.cv.configure(cursor="crosshair" if self.tool in("pencil","eraser") else "arrow")

    # ── RENDER ───────────────────────────────────────────────────
    def _composite(self,show_sel=True):
        base=Image.new("RGBA",(CW,CH),(247,243,237,255))
        d2=ImageDraw.Draw(base)

        for obj in self.objects:
            if obj["cat"]=="stroke":
                pts=obj.get("pts",[])
                if len(pts)>1:
                    d2.line(pts,fill=(*obj["color"],255),width=obj["size"])
                    r=obj["size"]//2
                    for pt in pts:
                        d2.ellipse([pt[0]-r,pt[1]-r,pt[0]+r,pt[1]+r],
                                   fill=(*obj["color"],255))
                continue
            pil=obj.get("pil")
            if pil is None: continue
            disp=pil.copy()
            if obj["fliph"]: disp=disp.transpose(Image.FLIP_LEFT_RIGHT)
            disp=disp.resize((obj["w"],obj["h"]),Image.LANCZOS)
            if disp.mode!="RGBA": disp=disp.convert("RGBA")
            if obj["alpha"]<100:
                r3,g3,b3,a3=disp.split()
                a3=a3.point(lambda v:int(v*obj["alpha"]/100))
                disp=Image.merge("RGBA",(r3,g3,b3,a3))
            base.paste(disp,(obj["x"],obj["y"]),disp)

        # selection box
        if show_sel and 0<=self.sel<len(self.objects):
            o=self.objects[self.sel]
            x0,y0=o["x"],o["y"]; x1,y1=x0+o["w"],y0+o["h"]
            for i in range(0,x1-x0,8):
                d2.line([(x0+i,y0),(min(x0+i+4,x1),y0)],fill=(0,145,255,200),width=1)
                d2.line([(x0+i,y1),(min(x0+i+4,x1),y1)],fill=(0,145,255,200),width=1)
            for i in range(0,y1-y0,8):
                d2.line([(x0,y0+i),(x0,min(y0+i+4,y1))],fill=(0,145,255,200),width=1)
                d2.line([(x1,y0+i),(x1,min(y0+i+4,y1))],fill=(0,145,255,200),width=1)
            # resize handle
            d2.rectangle([x1-10,y1-10,x1,y1],fill=(0,145,255,255))
            # label
            d2.text((x0+2,y0-13),o.get("cat",""),fill=(0,145,255,200))

        return base.convert("RGB")

    def _render(self):
        pil=self._composite()
        self._face_tk=ImageTk.PhotoImage(pil)
        self.cv.delete("all"); self.cv.create_image(0,0,image=self._face_tk,anchor="nw")

    # ── OBJECT OPS ───────────────────────────────────────────────
    def _op_change(self,v):
        if 0<=self.sel<len(self.objects):
            self.objects[self.sel]["alpha"]=int(float(v)); self._render()
    def _flip(self):
        if 0<=self.sel<len(self.objects):
            self.objects[self.sel]["fliph"]=not self.objects[self.sel]["fliph"]; self._render()
    def _front(self):
        if 0<=self.sel<len(self.objects)-1:
            o=self.objects.pop(self.sel); self.objects.append(o)
            self.sel=len(self.objects)-1; self._render()
    def _back_z(self):
        if self.sel>0:
            o=self.objects.pop(self.sel); self.objects.insert(0,o)
            self.sel=0; self._render()
    def _delete(self):
        if 0<=self.sel<len(self.objects):
            self._snap(); self.objects.pop(self.sel)
            self.sel=min(self.sel,len(self.objects)-1); self._render()
    def _clear(self):
        if self.objects and messagebox.askyesno("Clear","Remove all objects?"):
            self._snap(); self.objects=[]; self.sel=-1; self._render()

    # ── UNDO / REDO ──────────────────────────────────────────────
    def _snap(self):
        self.undo_stack.append(copy.deepcopy(self.objects))
        if len(self.undo_stack)>40: self.undo_stack.pop(0)
        self.redo_stack.clear()
    def _undo(self):
        if self.undo_stack:
            self.redo_stack.append(copy.deepcopy(self.objects))
            self.objects=self.undo_stack.pop()
            self.sel=min(self.sel,len(self.objects)-1); self._render()
    def _redo(self):
        if self.redo_stack:
            self.undo_stack.append(copy.deepcopy(self.objects))
            self.objects=self.redo_stack.pop()
            self.sel=min(self.sel,len(self.objects)-1); self._render()

    # ── SAVE ─────────────────────────────────────────────────────
    def _save(self):
        bak=self.sel; self.sel=-1
        pil=self._composite(show_sel=False)
        self.sel=bak; self._render()
        path=filedialog.asksaveasfilename(initialdir=SKETCH,defaultextension=".png",
            filetypes=[("PNG","*.png"),("JPEG","*.jpg")],title="Save Sketch")
        if path:
            pil.save(path); messagebox.showinfo("Saved",f"Saved:\n{path}")

    def _save_draft(self):
        """Save the current canvas state as a re-editable .sketch draft."""
        path = filedialog.asksaveasfilename(
            initialdir=SKETCH, defaultextension=".sketch",
            filetypes=[("Sketch Draft", "*.sketch")], title="Save Draft"
        )
        if not path: return

        serializable_objects = []
        for obj in self.objects:
            # Create a copy of the object without non-serializable fields
            obj_copy = {k: v for k, v in obj.items() if k not in ('fn', 'pil')}
            
            if obj["cat"] == "image":
                # Convert PIL image to base64
                buffered = io.BytesIO()
                obj["pil"].save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
                obj_copy["image_base64"] = img_str
            
            serializable_objects.append(obj_copy)
            
        try:
            with open(path, "w") as f:
                json.dump(serializable_objects, f)
            messagebox.showinfo("Saved", f"Draft saved:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save draft: {e}")

    def _load_draft(self):
        """Load a previously saved .sketch draft back onto the canvas."""
        path = filedialog.askopenfilename(
            initialdir=SKETCH, title="Load Draft",
            filetypes=[("Sketch Draft", "*.sketch")]
        )
        if not path: return
        
        try:
            with open(path, "r") as f:
                serializable_objects = json.load(f)
            
            self._snap() # Save state before loading for undo
            self.objects = []
            
            for obj_data in serializable_objects:
                cat = obj_data["cat"]
                # Ensure coordinate/size data are integers for Tkinter/PIL compatibility
                for key in ["x", "y", "w", "h"]:
                    if key in obj_data:
                        obj_data[key] = int(obj_data[key])

                if cat == "stroke":
                    self.objects.append(obj_data)
                elif cat == "image":
                    img_data = base64.b64decode(obj_data["image_base64"])
                    pil = Image.open(io.BytesIO(img_data)).convert("RGBA")
                    obj_data["pil"] = pil
                    self.objects.append(obj_data)
                else:
                    # It's a face part
                    # Re-assign load_image_part function and regenerate PIL image at stored size
                    obj_data["fn"] = load_image_part
                    obj_data["pil"] = load_image_part(cat, obj_data["idx"], obj_data["w"], obj_data["h"])
                    self.objects.append(obj_data)
            
            self.sel = -1
            self._render()
            self.sv.set(f"● Loaded Draft: {os.path.basename(path)}")
            messagebox.showinfo("Loaded", f"Draft loaded:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load draft: {e}")

    def _open_saved(self):
        """Load a previously saved sketch PNG back onto the canvas as an image object."""
        path=filedialog.askopenfilename(
            initialdir=SKETCH,title="Open Saved Sketch",
            filetypes=[("PNG","*.png"),("JPEG","*.jpg *.jpeg"),("All","*.*")])
        if not path: return
        try:
            pil=Image.open(path).convert("RGBA")
            self._snap()
            self.objects.append(dict(
                cat="image",idx=0,fn=None,
                x=0,y=0,w=min(pil.width,CW),h=min(pil.height,CH),
                alpha=100,fliph=False,pil=pil))
            self.sel=len(self.objects)-1
            self._render()
            self.sv.set(f"● Opened: {os.path.basename(path)}  — Now add more parts on top")
        except Exception as ex:
            messagebox.showerror("Error",str(ex))

    def _back_menu(self):
        self.root.destroy()
        script_dir = os.path.dirname(os.path.abspath(__file__))
        target = os.path.join(script_dir, "main_menu.py")
        os.system(f"{sys.executable} \"{target}\"")

    def _compare(self):
        self.root.destroy()
        script_dir = os.path.dirname(os.path.abspath(__file__))
        target = os.path.join(script_dir, "upload_match.py")
        os.system(f"{sys.executable} \"{target}\"")

if __name__=="__main__":
    SketchApp()
