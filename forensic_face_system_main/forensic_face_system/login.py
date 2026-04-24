"""
Sketch Generation & Identity Verification System
Login Page – Light Professional Blue Theme
"""
import tkinter as tk
from tkinter import messagebox
import os, sys, socket, uuid, math, random

USERS = {"admin": "admin123", "officer": "police123", "dept": "dept2024"}

def get_net():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80)); ip = s.getsockname()[0]; s.close()
    except: ip = "192.168.1.1"
    mac = ':'.join(('%012X' % uuid.getnode())[i:i+2] for i in range(0,12,2))
    return ip, mac

class LoginWindow:
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

        # ── BACKGROUND canvas ──────────────────────────────────────
        self.bg = tk.Canvas(self.root, bg="#eef2f7", highlightthickness=0)
        self.bg.place(x=0, y=0, relwidth=1, relheight=1)

        # Decorative circles (background)
        for r, x, y, c in [
            (280, W*0.12, H*0.22, "#dce8f8"),
            (180, W*0.18, H*0.78, "#d0e4f5"),
            (220, W*0.88, H*0.18, "#d8edf9"),
            (150, W*0.82, H*0.82, "#cce0f5"),
            (80,  W*0.50, H*0.08, "#e0ecf8"),
        ]:
            self.bg.create_oval(x-r,y-r,x+r,y+r, fill=c, outline="")

        # Dots grid (subtle)
        for x in range(40, W, 50):
            for y in range(40, H, 50):
                self.bg.create_oval(x-1,y-1,x+1,y+1, fill="#c8d8ea", outline="")

        # ── LEFT SIDE content ──────────────────────────────────────
        lx = int(W * 0.10)

        # Badge
        self.bg.create_oval(lx-36, int(H*0.18)-36,
                            lx+36, int(H*0.18)+36,
                            fill="#1565c0", outline="#0d47a1", width=2)
        self.bg.create_text(lx, int(H*0.18), text="🦅",
                            font=("Segoe UI Emoji", 28), fill="white")

        # Title block
        self.bg.create_text(lx+50, int(H*0.18)-14,
            text="SKETCH GENERATION &",
            font=("Helvetica", 20, "bold"), fill="#1565c0", anchor="w")
        self.bg.create_text(lx+50, int(H*0.18)+14,
            text="IDENTITY VERIFICATION SYSTEM",
            font=("Helvetica", 20, "bold"), fill="#1976d2", anchor="w")

        # Sub
        self.bg.create_text(lx+50, int(H*0.18)+42,
            text="AI-Powered Forensic Face Recognition Platform",
            font=("Helvetica", 11), fill="#5c85b3", anchor="w")

        # Divider
        self.bg.create_line(lx, int(H*0.30), int(W*0.45), int(H*0.30),
                            fill="#b8cfe8", width=1)

        # Feature list
        features = [
            ("🎨", "Composite Sketch Creation", "Build forensic face from feature parts"),
            ("🔍", "AI Face Matching",           "DeepFace VGG-Face similarity engine"),
            ("📊", "Top-4 Result Display",       "Ranked matches with confidence scores"),
            ("✏️",  "Freehand Drawing Tools",     "Pencil, eraser & adjustment controls"),
        ]
        fy = int(H * 0.35)
        for icon, title, sub in features:
            # icon circle
            self.bg.create_oval(lx-14, fy-14, lx+14, fy+14,
                                fill="#1565c0", outline="")
            self.bg.create_text(lx, fy, text=icon,
                                font=("Segoe UI Emoji", 12))
            self.bg.create_text(lx+24, fy-7, text=title,
                                font=("Helvetica", 11, "bold"),
                                fill="#1a3a5c", anchor="w")
            self.bg.create_text(lx+24, fy+9, text=sub,
                                font=("Helvetica", 9),
                                fill="#5c85b3", anchor="w")
            fy += 62

        # Network info box
        ip, mac = get_net()
        ny = int(H * 0.82)
        self.bg.create_rectangle(lx-10, ny-10,
                                  lx+380, ny+62,
                                  fill="#ddeaf8", outline="#b0ccec", width=1)
        self.bg.create_text(lx, ny+8,
            text=f"MAC : {mac}", font=("Courier", 9),
            fill="#2c5f8a", anchor="w")
        self.bg.create_text(lx, ny+26,
            text=f"IP  : {ip}", font=("Courier", 9),
            fill="#2c5f8a", anchor="w")
        self.bg.create_text(lx, ny+44,
            text="Interface : wlan0  (802.11n Network Adapter)",
            font=("Courier", 9), fill="#4a7aa0", anchor="w")

        # College
        self.bg.create_text(W//2, H-18,
            text="© Jerusalem College of Engineering  |  Computer Vision Department",
            font=("Helvetica", 9), fill="#7aa0be")

        # ── RIGHT: Login Card ──────────────────────────────────────
        cx = int(W * 0.72)
        cy = int(H * 0.50)
        cw, ch = 420, 440

        # Card shadow
        for off in [8, 5, 3]:
            self.bg.create_rectangle(
                cx-cw//2+off, cy-ch//2+off,
                cx+cw//2+off, cy+ch//2+off,
                fill=f"#{'c8d8ea' if off==8 else 'd0dcec' if off==5 else 'd8e4f0'}",
                outline="")

        # Card
        self.bg.create_rectangle(cx-cw//2, cy-ch//2,
                                  cx+cw//2, cy+ch//2,
                                  fill="white", outline="#c0d4ec", width=1)

        # Card top color bar
        self.bg.create_rectangle(cx-cw//2, cy-ch//2,
                                  cx+cw//2, cy-ch//2+5,
                                  fill="#1565c0", outline="")

        # Avatar circle
        av_y = cy - ch//2 + 54
        self.bg.create_oval(cx-32, av_y-32, cx+32, av_y+32,
                            fill="#e3eef8", outline="#b8d0ec", width=2)
        self.bg.create_text(cx, av_y, text="🔐",
                            font=("Segoe UI Emoji", 22))

        # Card title
        self.bg.create_text(cx, cy-ch//2+102,
            text="SECURE LOGIN", font=("Helvetica", 17, "bold"),
            fill="#1565c0")
        self.bg.create_text(cx, cy-ch//2+124,
            text="Enter your department credentials",
            font=("Helvetica", 9), fill="#7a9abf")

        # ── Entry fields ──
        ey1 = cy - ch//2 + 160
        ey2 = cy - ch//2 + 238

        # Username label + field
        self.bg.create_text(cx-cw//2+28, ey1-14,
            text="USERNAME", font=("Helvetica", 8, "bold"),
            fill="#1565c0", anchor="w")
        self.user_var = tk.StringVar()
        self.user_entry = tk.Entry(self.root,
            textvariable=self.user_var,
            font=("Helvetica", 13), bg="#f5f9ff",
            fg="#1a3a5c", insertbackground="#1565c0",
            relief="flat", highlightthickness=2,
            highlightbackground="#c0d4ec",
            highlightcolor="#1565c0", width=24)
        self.user_entry.place(x=cx-cw//2+28, y=ey1, height=44)
        self.user_entry.bind("<Return>", lambda e: self.pass_entry.focus())
        self.user_entry.bind("<FocusIn>",
            lambda e: self.user_entry.config(highlightbackground="#1565c0"))
        self.user_entry.bind("<FocusOut>",
            lambda e: self.user_entry.config(highlightbackground="#c0d4ec"))

        # Password label + field
        self.bg.create_text(cx-cw//2+28, ey2-14,
            text="PASSWORD", font=("Helvetica", 8, "bold"),
            fill="#1565c0", anchor="w")
        self.pass_var = tk.StringVar()
        self.pass_entry = tk.Entry(self.root,
            textvariable=self.pass_var,
            font=("Helvetica", 13), bg="#f5f9ff",
            fg="#1a3a5c", insertbackground="#1565c0",
            show="●", relief="flat", highlightthickness=2,
            highlightbackground="#c0d4ec",
            highlightcolor="#1565c0", width=24)
        self.pass_entry.place(x=cx-cw//2+28, y=ey2, height=44)
        self.pass_entry.bind("<Return>", lambda e: self._login())
        self.pass_entry.bind("<FocusIn>",
            lambda e: self.pass_entry.config(highlightbackground="#1565c0"))
        self.pass_entry.bind("<FocusOut>",
            lambda e: self.pass_entry.config(highlightbackground="#c0d4ec"))

        # Error label
        self.err_var = tk.StringVar()
        tk.Label(self.root, textvariable=self.err_var,
            bg="white", fg="#e53935",
            font=("Helvetica", 9)
        ).place(x=cx-cw//2+28, y=ey2+52, width=cw-56)

        # Login Button
        self.login_btn = tk.Button(self.root,
            text="  SIGN IN  →",
            command=self._login,
            bg="#1565c0", fg="white",
            activebackground="#1976d2", activeforeground="white",
            font=("Helvetica", 12, "bold"),
            relief="flat", cursor="hand2",
            width=22, height=2)
        self.login_btn.place(x=cx-cw//2+28, y=ey2+76)
        self.login_btn.bind("<Enter>",
            lambda e: self.login_btn.config(bg="#1976d2"))
        self.login_btn.bind("<Leave>",
            lambda e: self.login_btn.config(bg="#1565c0"))

        # Hint
        self.bg.create_text(cx, cy+ch//2-20,
            text="admin/admin123  •  officer/police123  •  dept/dept2024",
            font=("Helvetica", 8), fill="#aabdd4")

        # ── Status bar ──
        self.status_var = tk.StringVar(value="●  System Ready  |  Sketch Generation & Identity Verification")
        tk.Label(self.root, textvariable=self.status_var,
            bg="#1565c0", fg="white",
            font=("Helvetica", 9), anchor="w", padx=12
        ).place(x=0, rely=1.0, y=-26, relwidth=1, height=26)

        # Focus
        self.user_entry.focus()

    def _login(self):
        u = self.user_var.get().strip()
        p = self.pass_var.get().strip()
        self.err_var.set("")
        if not u or not p:
            self.err_var.set("⚠  Please enter username and password")
            return
        if USERS.get(u) == p:
            self.status_var.set("●  Authenticated — Loading system...")
            self.login_btn.config(bg="#388e3c", text="  AUTHENTICATED ✓")
            self.root.update()
            self.root.after(400, self._launch)
        else:
            self.err_var.set("✗  Invalid credentials. Access denied.")
            self.pass_var.set("")
            self.pass_entry.focus()

    def _launch(self):
        self.root.destroy()
        os.system(f"{sys.executable} main_menu.py")

if __name__ == "__main__":
    LoginWindow()
