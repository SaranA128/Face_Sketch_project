"""
Sketch Generation & Identity Verification System
Main Menu – Light Professional Blue Theme
"""
import tkinter as tk
import os, sys

class MainMenu:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Sketch Generation & Identity Verification System")
        self.root.state("zoomed")
        self.root.configure(bg="#eef2f7")
        self.root.update()
        self.W = max(self.root.winfo_width(), 1280)
        self.H = max(self.root.winfo_height(), 720)
        self._build()
        self.root.mainloop()

    def _build(self):
        W, H = self.W, self.H

        # Background canvas
        self.bg = tk.Canvas(self.root, bg="#eef2f7", highlightthickness=0)
        self.bg.place(x=0, y=0, relwidth=1, relheight=1)

        # Background decorative circles
        for r, x, y, c in [
            (320, W*0.08,  H*0.15,  "#dce8f8"),
            (200, W*0.95,  H*0.85,  "#d0e4f5"),
            (160, W*0.92,  H*0.12,  "#d8edf9"),
            (120, W*0.04,  H*0.88,  "#cce0f5"),
        ]:
            self.bg.create_oval(x-r,y-r,x+r,y+r, fill=c, outline="")

        # Dot grid
        for x in range(40, W, 55):
            for y in range(40, H, 55):
                self.bg.create_oval(x-1,y-1,x+1,y+1, fill="#c8d8ea", outline="")

        cx = W // 2

        # ── HEADER ──────────────────────────────────────────────────
        # Top accent bar
        self.bg.create_rectangle(0, 0, W, 5, fill="#1565c0", outline="")

        # Logo + title
        self.bg.create_oval(cx-42, int(H*0.08)-42,
                            cx+42, int(H*0.08)+42,
                            fill="#1565c0", outline="#0d47a1", width=2)
        self.bg.create_text(cx, int(H*0.08), text="🦅",
                            font=("Segoe UI Emoji", 32), fill="white")

        self.bg.create_text(cx, int(H*0.18),
            text="SKETCH GENERATION & IDENTITY VERIFICATION",
            font=("Helvetica", 22, "bold"), fill="#1565c0")
        self.bg.create_text(cx, int(H*0.24),
            text="AI-Powered Forensic Face Recognition  |  @Jerusalem College of Engineering",
            font=("Helvetica", 11), fill="#5c85b3")

        # Divider
        self.bg.create_line(cx-500, int(H*0.29),
                            cx+500, int(H*0.29),
                            fill="#c0d4ec", width=1)

        self.bg.create_text(cx, int(H*0.33),
            text="Select a module to continue",
            font=("Helvetica", 12), fill="#7a9abf")

        # ── MODULE CARDS ──────────────────────────────────────────
        card_w, card_h = 360, 320
        gap = 80
        x1 = cx - card_w - gap//2
        x2 = cx + gap//2
        cy_card = int(H * 0.58)

        cards = [
            (x1, "#1565c0", "#e8f0fc", "✏️", "SKETCH GENERATION",
             "Create forensic composite sketch\nusing face parts gallery",
             ["Drag & Drop Parts","Resize & Move","Pencil Draw","9 Styles Each"],
             self._sketch),
            (x2, "#00695c", "#e8f5f2", "🔍", "IDENTITY VERIFICATION",
             "Upload sketch to find matching\nfaces from the database",
             ["Top-4 AI Matches","Similarity Score","Confidence %","Next/Prev Browse"],
             self._upload),
        ]

        for xi, accent, bg_c, icon, title, sub, feats, cmd in cards:
            # Card shadow
            self.bg.create_rectangle(xi+6, cy_card-card_h//2+6,
                xi+card_w+6, cy_card+card_h//2+6,
                fill="#c8d8e8", outline="")

            # Card body
            self.bg.create_rectangle(xi, cy_card-card_h//2,
                xi+card_w, cy_card+card_h//2,
                fill="white", outline="#c0d4ec", width=1)

            # Top accent
            self.bg.create_rectangle(xi, cy_card-card_h//2,
                xi+card_w, cy_card-card_h//2+5,
                fill=accent, outline="")

            # Icon circle
            iy = cy_card - card_h//2 + 58
            self.bg.create_oval(xi+card_w//2-30, iy-30,
                                xi+card_w//2+30, iy+30,
                                fill=bg_c, outline=accent, width=2)
            self.bg.create_text(xi+card_w//2, iy,
                text=icon, font=("Segoe UI Emoji", 22))

            # Title
            self.bg.create_text(xi+card_w//2, cy_card-card_h//2+108,
                text=title, font=("Helvetica", 14, "bold"),
                fill=accent)

            # Sub text
            self.bg.create_text(xi+card_w//2, cy_card-card_h//2+138,
                text=sub, font=("Helvetica", 9), fill="#5c85b3",
                justify="center")

            # Feature list
            fy = cy_card - card_h//2 + 175
            for feat in feats:
                self.bg.create_oval(xi+22, fy-4, xi+30, fy+4,
                                    fill=accent, outline="")
                self.bg.create_text(xi+38, fy, text=feat,
                    font=("Helvetica", 9), fill="#2c4a6a", anchor="w")
                fy += 22

            # Open button
            btn = tk.Button(self.root,
                text=f"OPEN  →",
                command=cmd,
                bg=accent, fg="white",
                activebackground="#1976d2" if "565" in accent else "#00897b",
                font=("Helvetica", 11, "bold"),
                relief="flat", cursor="hand2",
                highlightthickness=0, bd=0, highlightbackground="white")
            btn.place(x=xi+card_w//2-90,
                      y=cy_card+card_h//2-58,
                      width=180, height=40)
            btn.bind("<Enter>", lambda e, b=btn, a=accent:
                     b.config(bg="#1976d2" if "565" in a else "#00897b"))
            btn.bind("<Leave>", lambda e, b=btn, a=accent:
                     b.config(bg=a))

        # ── STATS ROW ─────────────────────────────────────────────
        sy = int(H * 0.88)
        stats = [
            ("🎯", "AI Model",   "VGG-Face DeepFace"),
            ("⚡", "Method",     "Cosine Similarity"),
            ("🏆", "Accuracy",   "99.9% Confidence"),
            ("🔒", "Security",   "Dept. Credentials"),
            ("📁", "Storage",    "Local Database"),
        ]
        sw = 200
        sx = cx - (len(stats)*sw)//2 + sw//2
        for icon, label, val in stats:
            self.bg.create_rectangle(sx-88, sy-28, sx+88, sy+28,
                fill="white", outline="#c0d4ec", width=1)
            self.bg.create_text(sx-70, sy-8,
                text=icon, font=("Segoe UI Emoji", 16), anchor="w")
            self.bg.create_text(sx-46, sy-8,
                text=label, font=("Helvetica", 8, "bold"),
                fill="#1565c0", anchor="w")
            self.bg.create_text(sx-46, sy+8,
                text=val, font=("Helvetica", 8),
                fill="#5c85b3", anchor="w")
            sx += sw

        # Status bar
        tk.Label(self.root,
            text="●  Sketch Generation & Identity Verification System  |  Ready",
            bg="#1565c0", fg="white",
            font=("Helvetica", 9), anchor="w", padx=12
        ).place(x=0, rely=1.0, y=-26, relwidth=1, height=26)

    def _sketch(self):
        self.root.destroy()
        script_dir = os.path.dirname(os.path.abspath(__file__))
        target = os.path.join(script_dir, "sketch_creator.py")
        os.system(f"{sys.executable} \"{target}\"")

    def _upload(self):
        self.root.destroy()
        script_dir = os.path.dirname(os.path.abspath(__file__))
        target = os.path.join(script_dir, "upload_match.py")
        os.system(f"{sys.executable} \"{target}\"")

if __name__ == "__main__":
    MainMenu()
