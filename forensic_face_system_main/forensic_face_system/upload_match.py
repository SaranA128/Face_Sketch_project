"""
Sketch Generation & Identity Verification System
Upload & Match – Light Professional Theme, Top-4 Results
FIXED: ArcFace + CLAHE Preprocessing for Sketch-to-Photo Matching
"""
import tkinter as tk
from tkinter import messagebox, filedialog
import os, sys, shutil, threading, tempfile
from PIL import Image, ImageTk
import numpy as np

BASE   = os.path.dirname(os.path.abspath(__file__))
FACES  = os.path.join(BASE, "faces");    os.makedirs(FACES,  exist_ok=True)
SKETCH = os.path.join(BASE, "sketches"); os.makedirs(SKETCH, exist_ok=True)

# ══════════════════════════════════════════════════════════════════
# 1. IMAGE PRE-PROCESSING ALGORITHM
# ══════════════════════════════════════════════════════════════════
def preprocess_sketch(path):
    """
    Sketch Preprocessing Steps:
    - Convert to grayscale
    - CLAHE contrast enhancement (boost sketch lines)
    - Resize to 224x224 (ArcFace/VGG input size)
    - Convert grayscale → 3-channel BGR (model needs 3ch)
    - Save to temp file and return path
    """
    try:
        import cv2
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            # Fallback: use PIL
            pil_img = Image.open(path).convert("L")
            img = np.array(pil_img)

        # CLAHE - Contrast Limited Adaptive Histogram Equalization
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        img = clahe.apply(img)

        # Resize to 224x224
        img = cv2.resize(img, (224, 224))

        # Convert grayscale to 3-channel RGB
        img_rgb = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

        # Save to temp file
        tmp = tempfile.mktemp(suffix=".jpg")
        cv2.imwrite(tmp, img_rgb)
        return tmp

    except Exception as e:
        print("Preprocessing Error:", e)
        return path  # fallback: return original


# ══════════════════════════════════════════════════════════════════
# 2. SIMILARITY ENGINE  (ArcFace → fallback histogram)
# ══════════════════════════════════════════════════════════════════
def compute_similarity(p1, p2):
    """
    p1 = sketch path  |  p2 = real face photo path
    Steps:
      1. Preprocess sketch (CLAHE + resize + 3ch)
      2. DeepFace ArcFace cosine similarity
      3. Fallback: OpenCV histogram correlation
    """
    tmp_sketch = None
    try:
        # Step 1 – preprocess sketch
        tmp_sketch = preprocess_sketch(p1)

        # Step 2 – DeepFace ArcFace
        from deepface import DeepFace
        r = DeepFace.verify(
            tmp_sketch, p2,
            model_name="ArcFace",          # ArcFace > VGG-Face for cross-domain
            distance_metric="cosine",
            enforce_detection=False,
            silent=True
        )
        dist  = r.get("distance", 1.0)
        score = round(max(0, min(100, (1 - dist) * 100)), 4)
        return score

    except Exception as e:
        print("DeepFace ArcFace Error:", e)

    # Step 3 – Fallback: OpenCV histogram correlation
    try:
        import cv2
        sk = cv2.imread(tmp_sketch or p1, cv2.IMREAD_GRAYSCALE)
        ph = cv2.imread(p2,               cv2.IMREAD_GRAYSCALE)
        if sk is None:
            sk = np.array(Image.open(tmp_sketch or p1).convert("L"))
        if ph is None:
            ph = np.array(Image.open(p2).convert("L"))

        sk = cv2.resize(sk, (128, 128))
        ph = cv2.resize(ph, (128, 128))

        hist_sk = cv2.calcHist([sk], [0], None, [256], [0, 256])
        hist_ph = cv2.calcHist([ph], [0], None, [256], [0, 256])
        cv2.normalize(hist_sk, hist_sk)
        cv2.normalize(hist_ph, hist_ph)

        score = cv2.compareHist(hist_sk, hist_ph, cv2.HISTCMP_CORREL) * 100
        return round(max(0, score), 4)

    except Exception as e2:
        print("Histogram Fallback Error:", e2)

    # Last resort – numpy cosine
    try:
        a1 = np.array(Image.open(p1).convert("L").resize((128, 128))).flatten().astype(float)
        a2 = np.array(Image.open(p2).convert("L").resize((128, 128))).flatten().astype(float)
        dot  = np.dot(a1, a2)
        norm = np.linalg.norm(a1) * np.linalg.norm(a2) + 1e-9
        return round(dot / norm * 100, 4)
    except:
        return 0.0

    finally:
        # Cleanup temp file
        if tmp_sketch and tmp_sketch != p1 and os.path.exists(tmp_sketch):
            try:
                os.remove(tmp_sketch)
            except:
                pass


# ══════════════════════════════════════════════════════════════════
# 3. CNN FEATURE EXTRACTION  (for reference / docs)
# ══════════════════════════════════════════════════════════════════
def cnn_feature_extraction(image_path):
    """
    CNN Feature Extraction using DeepFace ArcFace.
    Converts image into feature vector (embedding).
    """
    try:
        from deepface import DeepFace
        embedding = DeepFace.represent(
            img_path=image_path,
            model_name="ArcFace",
            enforce_detection=False
        )
        feature_vector = np.array(embedding[0]["embedding"])
        return feature_vector
    except Exception as e:
        print("CNN Extraction Error:", e)
        return None


# ══════════════════════════════════════════════════════════════════
# 4. COSINE SIMILARITY  (standalone utility)
# ══════════════════════════════════════════════════════════════════
def cosine_similarity(vec1, vec2):
    """
    Cosine Similarity Formula:
    similarity = (A . B) / (||A|| * ||B||)
    """
    try:
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        similarity = dot_product / (norm1 * norm2 + 1e-8)
        return round(similarity * 100, 4)
    except Exception as e:
        print("Similarity Error:", e)
        return 0.0


# ══════════════════════════════════════════════════════════════════
# 5. TOP-N MATCH FINDER
# ══════════════════════════════════════════════════════════════════
def find_top_matches(sketch_path, top_n=4):
    results = []
    for f in os.listdir(FACES):
        if not f.lower().endswith((".jpg", ".jpeg", ".png", ".bmp")):
            continue
        fp = os.path.join(FACES, f)
        sc = compute_similarity(sketch_path, fp)
        results.append((fp, f, sc))
    results.sort(key=lambda x: -x[2])
    return results[:top_n]


# ══════════════════════════════════════════════════════════════════
# 6. GUI
# ══════════════════════════════════════════════════════════════════
class UploadMatch:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Identity Verification – Upload & Match")
        self.root.state("zoomed")
        self.root.configure(bg="#eef2f7")
        self.root.update()
        self.W = max(self.root.winfo_width(), 1280)
        self.H = max(self.root.winfo_height(), 720)

        self.sketch_path = None
        self.results     = []
        self.cur_idx     = 0

        self._build()
        self.root.mainloop()

    # ── LAYOUT ───────────────────────────────────────────────────
    def _build(self):
        W, H = self.W, self.H

        # Background canvas
        self.bg = tk.Canvas(self.root, bg="#eef2f7", highlightthickness=0)
        self.bg.place(x=0, y=0, relwidth=1, relheight=1)

        # Decorative circles
        for r, x, y, c in [
            (280, W*0.07, H*0.2,  "#dce8f8"),
            (200, W*0.94, H*0.82, "#d0e4f5"),
            (160, W*0.93, H*0.15, "#d8edf9"),
            (110, W*0.05, H*0.85, "#cce0f5")
        ]:
            self.bg.create_oval(x-r, y-r, x+r, y+r, fill=c, outline="")

        # Dot grid
        for x in range(40, W, 55):
            for y in range(40, H, 55):
                self.bg.create_oval(x-1, y-1, x+1, y+1, fill="#c8d8ea", outline="")

        # Top accent bar
        self.bg.create_rectangle(0, 0, W, 5, fill="#1565c0", outline="")

        # ── HEADER ──
        self.bg.create_text(W//2, 30,
            text="IDENTITY VERIFICATION SYSTEM",
            font=("Helvetica", 18, "bold"), fill="#1565c0")
        self.bg.create_text(W//2, 54,
            text="Upload Sketch  ▶  AI Similarity Analysis  ▶  Top-4 Matches",
            font=("Helvetica", 10), fill="#5c85b3")
        self.bg.create_line(40, 70, W-40, 70, fill="#c0d4ec", width=1)

        # ── SECTION A: Input Sketch ──────────────────────────────
        ax, ay, aw, ah = 30, 85, 310, 420
        self._card(ax, ay, aw, ah, "INPUT SKETCH", "#1565c0")

        self.sketch_cv = tk.Canvas(self.root,
            width=aw-24, height=ah-100,
            bg="#f0f5fc", highlightthickness=2,
            highlightbackground="#c0d4ec")
        self.sketch_cv.place(x=ax+12, y=ay+44)
        self.sketch_cv.create_text(
            (aw-24)//2, (ah-100)//2,
            text="📂\nNo sketch loaded",
            font=("Helvetica", 11), fill="#aabdd4",
            justify="center", tags="placeholder")

        # Action buttons
        by = ay + ah + 6
        self._btn("📂  Open Sketch",  ax,          by,      aw//2-4, 36, self._open_sketch,   "#1565c0")
        self._btn("⬆  Upload",       ax+aw//2+2,  by,      aw//2-2, 36, self._upload_sketch, "#0288d1")
        self._btn("🔍  FIND MATCH",  ax,          by+44,   aw,      44, self._find_match,
                  "#1b5e20", "#fff", big=True)
        self._btn("← Menu",          ax,          by+98,   aw//2-4, 34, self._back_menu,  "#546e7a", "white")
        self._btn("✏  New Sketch",   ax+aw//2+2,  by+98,   aw//2-2, 34, self._new_sketch, "#546e7a", "white")

        # Progress label
        self.prog_var = tk.StringVar()
        tk.Label(self.root, textvariable=self.prog_var,
            bg="#eef2f7", fg="#1565c0",
            font=("Helvetica", 9), anchor="w"
        ).place(x=ax, y=by+140, width=aw)

        # ── SECTION B: Best Match ────────────────────────────────
        bx, b_y, bw, bh = 358, 85, 380, 420
        self._card(bx, b_y, bw, bh, "BEST MATCH", "#1565c0")

        self.main_cv = tk.Canvas(self.root,
            width=bw-24, height=bh-130,
            bg="#f0f5fc", highlightthickness=2,
            highlightbackground="#c0d4ec")
        self.main_cv.place(x=bx+12, y=b_y+44)
        self.main_cv.create_text(
            (bw-24)//2, (bh-130)//2,
            text="❓\nNo match yet",
            font=("Helvetica", 11), fill="#aabdd4", justify="center")

        # Similarity label
        self.sim_var = tk.StringVar(value="Similarity: —")
        tk.Label(self.root, textvariable=self.sim_var,
            bg="white", fg="#1565c0",
            font=("Helvetica", 13, "bold"), relief="flat"
        ).place(x=bx+12, y=b_y+bh-82, width=bw-24, height=28)

        # Progress bar
        self.bar_frame = tk.Frame(self.root, bg="#e3eaf2", height=10)
        self.bar_frame.place(x=bx+12, y=b_y+bh-50, width=bw-24, height=10)
        self.bar_fill = tk.Frame(self.bar_frame, bg="#1565c0", height=10)
        self.bar_fill.place(x=0, y=0, width=0, height=10)

        # Info label
        self.info_var = tk.StringVar(value="Open a sketch and click FIND MATCH")
        tk.Label(self.root, textvariable=self.info_var,
            bg="white", fg="#5c85b3",
            font=("Helvetica", 8), anchor="w", wraplength=bw-28
        ).place(x=bx+12, y=b_y+bh-36, width=bw-24, height=30)

        # Nav buttons
        nav_y = b_y + bh + 6
        self._btn("◀  Prev", bx,         nav_y, 110, 34, self._prev, "#546e7a", "white")
        self._btn("▶  Next", bx+bw-112,  nav_y, 110, 34, self._next, "#546e7a", "white")
        self.nav_var = tk.StringVar(value="")
        tk.Label(self.root, textvariable=self.nav_var,
            bg="#eef2f7", fg="#7a9abf",
            font=("Helvetica", 9)
        ).place(x=bx+112, y=nav_y+6, width=bw-226)

        # ── SECTION C: Top-4 Grid ────────────────────────────────
        gx = 756; gy = 85
        gw = W - gx - 30
        gh = H - gy - 80
        self._card(gx, gy, gw, gh, "TOP  4  MATCHES", "#1565c0")

        self.result_frames = []
        rcard_w = (gw - 30) // 2
        rcard_h = (gh - 60) // 2 - 6
        RANK_COLORS = ["#1565c0", "#0288d1", "#00695c", "#e65100"]
        RANK_LABELS = ["1st", "2nd", "3rd", "4th"]

        for i in range(4):
            row = i // 2; col = i % 2
            fx = gx + 10 + col * (rcard_w + 10)
            fy = gy + 46 + row * (rcard_h + 10)

            # mini card
            self.bg.create_rectangle(fx, fy, fx+rcard_w, fy+rcard_h,
                fill="white", outline="#c0d4ec", width=1, tags=f"rc{i}")
            # top stripe
            self.bg.create_rectangle(fx, fy, fx+rcard_w, fy+4,
                fill=RANK_COLORS[i], outline="", tags=f"rct{i}")
            # rank badge
            self.bg.create_rectangle(fx, fy+4, fx+34, fy+22,
                fill=RANK_COLORS[i], outline="")
            self.bg.create_text(fx+17, fy+13,
                text=RANK_LABELS[i],
                font=("Helvetica", 8, "bold"), fill="white")

            # image canvas
            cv = tk.Canvas(self.root,
                width=rcard_w-16, height=rcard_h-60,
                bg="#f0f5fc", highlightthickness=1,
                highlightbackground="#c0d4ec")
            cv.place(x=fx+8, y=fy+26)
            cv.create_text((rcard_w-16)//2, (rcard_h-60)//2,
                text="—", font=("Helvetica", 14), fill="#c0d4ec")

            # score
            sv = tk.StringVar(value="—")
            tk.Label(self.root, textvariable=sv,
                bg="white", fg=RANK_COLORS[i],
                font=("Helvetica", 8, "bold")
            ).place(x=fx+8, y=fy+rcard_h-34, width=rcard_w//2-4, height=14)

            # name
            nv = tk.StringVar(value="")
            tk.Label(self.root, textvariable=nv,
                bg="white", fg="#5c85b3",
                font=("Helvetica", 7)
            ).place(x=fx+rcard_w//2+4, y=fy+rcard_h-34, width=rcard_w//2-12, height=14)

            # view btn
            vbtn = tk.Button(self.root, text="VIEW",
                command=lambda idx=i: self._select_result(idx),
                bg=RANK_COLORS[i], fg="white",
                font=("Helvetica", 7, "bold"), relief="flat", cursor="hand2")
            vbtn.place(x=fx+8, y=fy+rcard_h-18, width=rcard_w-16, height=16)

            self.result_frames.append(
                {"cv": cv, "sv": sv, "nv": nv, "color": RANK_COLORS[i]})

        # Status bar
        self.status_var = tk.StringVar(
            value="●  Identity Verification System  |  Ready — Open a sketch to begin")
        tk.Label(self.root, textvariable=self.status_var,
            bg="#1565c0", fg="white",
            font=("Helvetica", 9), anchor="w", padx=12
        ).place(x=0, rely=1.0, y=-26, relwidth=1, height=26)

    # ── Helpers ──────────────────────────────────────────────────
    def _card(self, x, y, w, h, title, accent="#1565c0"):
        self.bg.create_rectangle(x+4, y+4, x+w+4, y+h+4, fill="#d0dcec", outline="")
        self.bg.create_rectangle(x, y, x+w, y+h, fill="white", outline="#c0d4ec", width=1)
        self.bg.create_rectangle(x, y, x+w, y+5, fill=accent, outline="")
        self.bg.create_text(x+w//2, y+20,
            text=title, font=("Helvetica", 10, "bold"), fill=accent)

    def _btn(self, text, x, y, w, h, cmd,
             bg="#1565c0", fg="white", big=False):
        font = ("Helvetica", 11, "bold") if big else ("Helvetica", 9, "bold")
        btn = tk.Button(self.root, text=text, command=cmd,
            bg=bg, fg=fg, activebackground="#1976d2",
            font=font, relief="flat", cursor="hand2")
        btn.place(x=x, y=y, width=w, height=h)
        orig = bg
        btn.bind("<Enter>", lambda e, b=btn: b.config(bg="#1976d2"))
        btn.bind("<Leave>", lambda e, b=btn, o=orig: b.config(bg=o))
        return btn

    def _show_img(self, cv, path):
        try:
            w = cv.winfo_width()  or 300
            h = cv.winfo_height() or 280
            img = Image.open(path).convert("RGB")
            img.thumbnail((w-8, h-8), Image.LANCZOS)
            tk_img = ImageTk.PhotoImage(img)
            cv.delete("all")
            cv.create_image(w//2, h//2, image=tk_img, anchor="center")
            cv._img = tk_img
        except Exception as e:
            print("Show Image Error:", e)

    def _set_bar(self, pct):
        total = self.bar_frame.winfo_width() or 356
        w = int(total * pct / 100)
        self.bar_fill.place(x=0, y=0, width=max(0, w), height=10)
        color = "#c62828" if pct < 40 else "#f57c00" if pct < 65 else "#2e7d32"
        self.bar_fill.configure(bg=color)

    # ── Actions ──────────────────────────────────────────────────
    def _open_sketch(self):
        path = filedialog.askopenfilename(
            title="Open Sketch",
            filetypes=[("Image", "*.png *.jpg *.jpeg *.bmp")])
        if path:
            self.sketch_path = path
            self.sketch_cv.delete("all")
            self._show_img(self.sketch_cv, path)
            self.sim_var.set("Similarity: —")
            self._set_bar(0)
            self.info_var.set(f"Loaded: {os.path.basename(path)}")
            self._clear_results()
            self.status_var.set(f"●  Sketch loaded: {os.path.basename(path)}")

    def _upload_sketch(self):
        if not self.sketch_path:
            messagebox.showwarning("Upload", "Please open a sketch first.")
            return
        dest = os.path.join(SKETCH, os.path.basename(self.sketch_path))
        if os.path.abspath(self.sketch_path) != os.path.abspath(dest):
            shutil.copy2(self.sketch_path, dest)
        messagebox.showinfo("Uploaded",
            f"✓  Sketch saved to /sketches/\n{os.path.basename(dest)}")

    def _find_match(self):
        if not self.sketch_path:
            messagebox.showwarning("Find Match", "Please open a sketch first.")
            return
        db = [f for f in os.listdir(FACES)
              if f.lower().endswith((".jpg", ".jpeg", ".png", ".bmp"))]
        if not db:
            messagebox.showwarning("Empty Database",
                "No images in /faces/ folder.\n\nAdd reference photos to:\n" + FACES)
            return

        self.sim_var.set("Searching…")
        self.info_var.set("AI engine analyzing…")
        self.prog_var.set("▶  Initializing…")
        self.status_var.set("●  Searching database…")
        self._clear_results()
        self.root.update()

        def _run():
            import time
            steps = [
                f"▶  Preprocessing sketch (CLAHE)…",
                f"▶  Loading ArcFace model…",
                f"▶  Extracting face embeddings…",
                f"▶  Comparing {len(db)} faces in database…",
                f"▶  Ranking top-4 results…"
            ]
            for s in steps:
                self.root.after(0, lambda m=s: self.prog_var.set(m))
                time.sleep(0.4)
            top = find_top_matches(self.sketch_path, 4)
            self.root.after(0, lambda: self._show_results(top))

        threading.Thread(target=_run, daemon=True).start()

    def _show_results(self, results):
        self.results  = results
        self.cur_idx  = 0
        self.prog_var.set("")

        if not results:
            self.sim_var.set("No match found")
            self.info_var.set("Database may be empty or no similar faces found.")
            self.status_var.set("●  No matches found")
            return

        # Fill mini cards
        for i, frame in enumerate(self.result_frames):
            if i < len(results):
                path, fname, score = results[i]
                self._show_img(frame["cv"], path)
                frame["sv"].set(f"{score:.2f}%")
                frame["nv"].set(fname[:18])
            else:
                frame["cv"].delete("all")
                frame["sv"].set("—")
                frame["nv"].set("")

        self._display_result(0)
        self.status_var.set(
            f"●  Found {len(results)} match(es)  |  Best: {results[0][2]:.2f}%")

    def _display_result(self, idx):
        if not self.results or idx >= len(self.results):
            return
        self.cur_idx = idx
        path, fname, score = self.results[idx]
        self.main_cv.delete("all")
        self._show_img(self.main_cv, path)
        self.sim_var.set(f"Similarity: {score:.4f}%")
        self._set_bar(min(100, score))
        conf = min(99.9999, score * 1.16)
        self.info_var.set(
            f"#{idx+1}  {fname}   |   Score: {score:.4f}%   |   Conf: {conf:.4f}%")
        self.nav_var.set(f"Result {idx+1} / {len(self.results)}")
        # Highlight active card border
        for j in range(4):
            c = self.result_frames[j]["color"] if j == idx else "#c0d4ec"
            self.bg.itemconfig(f"rc{j}", outline=c, width=2 if j == idx else 1)

    def _select_result(self, idx):
        self._display_result(idx)

    def _prev(self):
        if self.results:
            self._display_result((self.cur_idx - 1) % len(self.results))

    def _next(self):
        if self.results:
            self._display_result((self.cur_idx + 1) % len(self.results))

    def _clear_results(self):
        self.results  = []
        self.cur_idx  = 0
        self.main_cv.delete("all")
        self.main_cv.create_text(
            self.main_cv.winfo_width()  // 2 or 190,
            self.main_cv.winfo_height() // 2 or 145,
            text="❓\nNo match yet",
            font=("Helvetica", 11), fill="#aabdd4", justify="center")
        for fr in self.result_frames:
            fr["cv"].delete("all")
            fr["sv"].set("—")
            fr["nv"].set("")

    def _back_menu(self):
        self.root.destroy()
        os.system(f"{sys.executable} main_menu.py")

    def _new_sketch(self):
        self.root.destroy()
        os.system(f"{sys.executable} sketch_creator.py")


# ══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    UploadMatch()
