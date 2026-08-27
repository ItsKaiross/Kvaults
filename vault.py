import secrets
import string
import tkinter as tk
from tkinter import ttk, messagebox
from storage import unlock, save, save_entry, delete_entry
from logo_service import LogoService

# ── Design Tokens ─────────────────────────────────────────────────────────────
BG        = "#0B0D12"
CARD      = "#121620"
CARD2     = "#1A2030"
BORDER    = "#252C3D"
ACCENT    = "#7C6FF7"
ACCENT_H  = "#9388FF"
ACCENT_DIM= "#342F6B"
FG        = "#F4F6FB"
FG_SUB    = "#A6AFC3"
FG_DIM    = "#69738A"
SUCCESS   = "#2CB67D"
DANGER    = "#FF6B7A"
WARN      = "#F5B942"

FONT      = "Segoe UI"

# ── Utilities ─────────────────────────────────────────────────────────────────
def generate_password(length=20):
    alpha = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
    return "".join(secrets.choice(alpha) for _ in range(length))

def copy_to_clipboard(root, text, clear_after=30):
    root.clipboard_clear()
    root.clipboard_append(text)
    root.after(clear_after * 1000, lambda: _clear_clipboard(root, text))

def _clear_clipboard(root, original):
    try:
        current = root.clipboard_get()
        if current == original:
            root.clipboard_clear()
    except Exception:
        pass

def password_strength(pw):
    score = 0
    if len(pw) >= 8:  score += 1
    if len(pw) >= 14: score += 1
    if any(c.isupper() for c in pw): score += 1
    if any(c.isdigit() for c in pw): score += 1
    if any(c in "!@#$%^&*()-_=+" for c in pw): score += 1
    labels = ["", "Weak", "Fair", "Good", "Strong", "Very Strong"]
    colors = ["", DANGER, WARN, WARN, SUCCESS, SUCCESS]
    return score, labels[score], colors[score]

# ── Reusable Widgets ──────────────────────────────────────────────────────────
def mk_label(parent, text, size=10, color=FG, bold=False, bg=None, **kw):
    weight = "bold" if bold else "normal"
    return tk.Label(parent, text=text, bg=bg or BG, fg=color,
                    font=(FONT, size, weight), **kw)

def mk_btn(parent, text, cmd, style="primary", width=None, **kw):
    styles = {
        "primary": (ACCENT,    ACCENT_H,  "#fff"),
        "ghost":   (CARD,      CARD2,     FG_SUB),
        "danger":  ("#3a1a1a", "#5a2020", DANGER),
        "success": ("#1a3a2a", "#1f4a35", SUCCESS),
    }
    bg, hbg, fg = styles.get(style, styles["primary"])
    cfg = dict(bg=bg, fg=fg, activebackground=hbg, activeforeground=fg,
               relief="flat", font=(FONT, 10), cursor="hand2",
               padx=14, pady=8, bd=0)
    if width:
        cfg["width"] = width
    b = tk.Button(parent, text=text, command=cmd, **cfg, **kw)
    b.bind("<Enter>", lambda _: b.config(bg=hbg))
    b.bind("<Leave>", lambda _: b.config(bg=bg))
    return b

def mk_entry(parent, show="", textvariable=None, width=None, **kw):
    cfg = dict(bg=CARD2, fg=FG, insertbackground=FG, relief="flat",
               font=(FONT, 11), highlightthickness=1,
               highlightbackground=BORDER, highlightcolor=ACCENT,
               selectbackground=ACCENT_DIM, selectforeground=FG)
    if show:      cfg["show"] = show
    if textvariable: cfg["textvariable"] = textvariable
    if width:     cfg["width"] = width
    return tk.Entry(parent, **cfg, **kw)

def mk_separator(parent, color=BORDER):
    return tk.Frame(parent, bg=color, height=1)

def rounded_frame(parent, bg=CARD, padx=0, pady=0, **kw):
    """Simulated card using a bordered frame."""
    outer = tk.Frame(parent, bg=BORDER, **kw)
    inner = tk.Frame(outer, bg=bg, padx=padx, pady=pady)
    inner.pack(fill="both", expand=True, padx=1, pady=1)
    return outer, inner

# ── ttk Styles ────────────────────────────────────────────────────────────────
def apply_styles(root):
    s = ttk.Style(root)
    s.theme_use("clam")
    s.configure("Vault.Treeview",
                background=CARD, foreground=FG,
                fieldbackground=CARD, rowheight=54,
                font=(FONT, 10), borderwidth=0, relief="flat")
    s.configure("Vault.Treeview.Heading",
                background=BG, foreground=FG_DIM,
                font=(FONT, 9, "bold"), relief="flat",
                borderwidth=0, padding=(0, 8))
    s.map("Vault.Treeview",
          background=[("selected", ACCENT_DIM)],
          foreground=[("selected", FG)])
    s.configure("Vault.Vertical.TScrollbar",
                background=CARD, troughcolor=BG,
                arrowcolor=FG_DIM, borderwidth=0, relief="flat")
    s.configure("Strength.Horizontal.TProgressbar",
                troughcolor=CARD2, borderwidth=0, relief="flat")

# ── 2FA Helpers ──────────────────────────────────────────────────────────────
TOTP_FILE = "vault_2fa.key"

def _totp_secret_exists():
    if not os.path.exists(TOTP_FILE):
        return None
    with open(TOTP_FILE, "r") as f:
        return f.read().strip()

def _save_totp_secret(secret: str):
    with open(TOTP_FILE, "w") as f:
        f.write(secret)

def _delete_totp_secret():
    if os.path.exists(TOTP_FILE):
        os.remove(TOTP_FILE)

import os

# ── Login Screen ──────────────────────────────────────────────────────────────
class LoginScreen(tk.Frame):
    def __init__(self, master, on_unlock):
        super().__init__(master, bg=BG)
        self.on_unlock = on_unlock
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        # Center column
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        center = tk.Frame(self, bg=BG)
        center.place(relx=0.5, rely=0.5, anchor="center")

        # Logo area
        logo_frame = tk.Frame(center, bg=BG)
        logo_frame.pack(pady=(0, 28))

        # Icon circle simulation
        icon_canvas = tk.Canvas(logo_frame, width=72, height=72,
                                bg=BG, highlightthickness=0)
        icon_canvas.pack()
        icon_canvas.create_oval(4, 4, 68, 68, fill=ACCENT_DIM, outline=ACCENT, width=2)
        icon_canvas.create_text(36, 36, text="🔐", font=(FONT, 22))

        mk_label(center, "Kvaults", size=26, bold=True, color=FG).pack()
        mk_label(center, "Your passwords, secured.", size=10, color=FG_DIM).pack(pady=(2, 0))

        # Card
        outer, card = rounded_frame(center, bg=CARD, padx=36, pady=32)
        outer.pack(pady=28, ipadx=0, ipady=0)

        # Master password field
        mk_label(card, "MASTER PASSWORD", size=8, color=FG_DIM, bold=True, bg=CARD).pack(anchor="w")
        tk.Frame(card, bg=CARD, height=6).pack()

        pw_row = tk.Frame(card, bg=CARD2, highlightthickness=1,
                          highlightbackground=BORDER, highlightcolor=ACCENT)
        pw_row.pack(fill="x", ipady=2)

        self.pw_var = tk.StringVar()
        self.pw_entry = tk.Entry(pw_row, textvariable=self.pw_var, show="•",
                                 bg=CARD2, fg=FG, insertbackground=FG,
                                 relief="flat", font=(FONT, 12), bd=0,
                                 selectbackground=ACCENT_DIM)
        self.pw_entry.pack(side="left", fill="x", expand=True, ipady=10, padx=(12, 0))

        self._show = False
        eye = tk.Button(pw_row, text="◑", bg=CARD2, fg=FG_DIM,
                        activebackground=CARD2, activeforeground=FG,
                        relief="flat", cursor="hand2", font=(FONT, 12), bd=0,
                        command=self._toggle_show)
        eye.pack(side="right", padx=8)

        # Focus border effect
        self.pw_entry.bind("<FocusIn>",  lambda _: pw_row.config(highlightbackground=ACCENT))
        self.pw_entry.bind("<FocusOut>", lambda _: pw_row.config(highlightbackground=BORDER))

        tk.Frame(card, bg=CARD, height=20).pack()

        # Unlock button
        self.unlock_btn = mk_btn(card, "Unlock Vault  →", self._unlock, width=24)
        self.unlock_btn.pack(fill="x", ipady=4)

        # Error label
        self.err_var = tk.StringVar()
        err_lbl = tk.Label(card, textvariable=self.err_var, bg=CARD,
                           fg=DANGER, font=(FONT, 9))
        err_lbl.pack(pady=(10, 0))

        mk_label(center, "New vault? Just enter a master password to create one.",
                 size=8, color=FG_DIM).pack()

        self.pw_entry.bind("<Return>", lambda _: self._unlock())
        self.pw_entry.focus()

        # Show auto-lock message if set
        top = self.winfo_toplevel()
        if getattr(top, "_show_toast_on_login", ""):
            self.err_var.set(top._show_toast_on_login)
            top._show_toast_on_login = ""

    def _toggle_show(self):
        self._show = not self._show
        self.pw_entry.config(show="" if self._show else "•")

    def _unlock(self):
        pw = self.pw_var.get()
        if not pw:
            self.err_var.set("⚠  Master password cannot be empty.")
            return
        self.unlock_btn.config(text="Unlocking…", state="disabled")
        self.after(80, lambda: self._do_unlock(pw))

    def _do_unlock(self, pw):
        try:
            entries, salt = unlock(pw)
            secret = _totp_secret_exists()
            if secret:
                self._verify_2fa(pw, entries, salt, secret)
            else:
                self.on_unlock(pw, entries, salt)
        except ValueError:
            self.err_var.set("✕  Wrong master password. Try again.")
            self.unlock_btn.config(text="Unlock Vault  →", state="normal")
            self.pw_entry.focus()

    def _verify_2fa(self, pw, entries, salt, secret):
        win = tk.Toplevel(self.winfo_toplevel())
        win.title("Two-Factor Authentication")
        win.configure(bg=BG)
        win.resizable(False, False)
        win.grab_set()
        win.protocol("WM_DELETE_WINDOW", lambda: [
            win.destroy(),
            self.unlock_btn.config(text="Unlock Vault  →", state="normal")
        ])

        f = tk.Frame(win, bg=BG, padx=32, pady=28)
        f.pack()
        mk_label(f, "🛡️  Two-Factor Auth", size=14, bold=True).pack()
        mk_label(f, "Enter the 6-digit code from your authenticator app.",
                 size=9, color=FG_DIM).pack(pady=(4, 16))

        code_var = tk.StringVar()
        code_entry = mk_entry(f, textvariable=code_var, width=12)
        code_entry.pack(ipady=8)
        code_entry.focus()

        err_var = tk.StringVar()
        tk.Label(f, textvariable=err_var, bg=BG, fg=DANGER,
                 font=(FONT, 9)).pack(pady=(6, 0))

        def verify():
            import pyotp
            totp = pyotp.TOTP(secret)
            if totp.verify(code_var.get().strip()):
                win.destroy()
                self.on_unlock(pw, entries, salt)
            else:
                err_var.set("✕  Invalid code. Try again.")
                code_var.set("")
                code_entry.focus()

        mk_btn(f, "Verify", verify).pack(pady=(14, 0), fill="x", ipady=4)
        code_entry.bind("<Return>", lambda _: verify())

        win.update_idletasks()
        x = self.winfo_toplevel().winfo_rootx() + (self.winfo_toplevel().winfo_width()  - win.winfo_width())  // 2
        y = self.winfo_toplevel().winfo_rooty() + (self.winfo_toplevel().winfo_height() - win.winfo_height()) // 2
        win.geometry(f"+{x}+{y}")

# ── Add / Edit Dialog ─────────────────────────────────────────────────────────
class EntryDialog(tk.Toplevel):
    def __init__(self, master, on_save, existing=None):
        super().__init__(master)
        self.on_save  = on_save
        self.existing = existing
        self.title("Edit Entry" if existing else "New Entry")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.grab_set()
        self._build()
        self._center(master)

    def _center(self, parent):
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width()  - self.winfo_width())  // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def _build(self):
        pad = tk.Frame(self, bg=BG, padx=28, pady=24)
        pad.pack()

        title = "Edit Entry" if self.existing else "New Entry"
        mk_label(pad, title, size=14, bold=True).pack(anchor="w")
        mk_label(pad, "Fill in the details below.", size=9, color=FG_DIM).pack(anchor="w", pady=(2, 16))
        mk_separator(pad).pack(fill="x", pady=(0, 16))

        self.vars = {}
        fields = [
            ("Site / App Name *", "name",  False),
            ("Username / Email *", "user", False),
            ("Password *",         "pw",   True),
            ("URL",                "url",  False),
            ("Notes",              "notes",False),
        ]
        for lbl, key, is_pw in fields:
            row = tk.Frame(pad, bg=BG)
            row.pack(fill="x", pady=(0, 12))
            mk_label(row, lbl, size=9, color=FG_SUB).pack(anchor="w", pady=(0, 4))
            v = tk.StringVar()
            self.vars[key] = v
            if is_pw:
                self._build_pw_field(row, v)
            else:
                e = mk_entry(row, textvariable=v, width=38)
                e.pack(fill="x", ipady=7)

        if self.existing:
            name, data = self.existing
            # name may be "site::user" — populate site field from data["site"] if present
            self.vars["name"].set(data.get("site", name.split("::")[0]))
            self.vars["user"].set(data.get("username", ""))
            self.vars["pw"].set(data.get("password", ""))
            self.vars["url"].set(data.get("url", ""))
            self.vars["notes"].set(data.get("notes", ""))
            self._update_strength()

        self.err_var = tk.StringVar()
        tk.Label(pad, textvariable=self.err_var, bg=BG,
                 fg=DANGER, font=(FONT, 9)).pack(anchor="w")

        mk_separator(pad).pack(fill="x", pady=(8, 16))

        btns = tk.Frame(pad, bg=BG)
        btns.pack(fill="x")
        mk_btn(btns, "Cancel", self.destroy, style="ghost").pack(side="left")
        mk_btn(btns, "Save Entry", self._save).pack(side="right")

    def _build_pw_field(self, parent, var):
        # Input row
        pw_row = tk.Frame(parent, bg=CARD2, highlightthickness=1,
                          highlightbackground=BORDER, highlightcolor=ACCENT)
        pw_row.pack(fill="x")
        self.pw_entry = tk.Entry(pw_row, textvariable=var, show="•",
                                 bg=CARD2, fg=FG, insertbackground=FG,
                                 relief="flat", font=(FONT, 11), bd=0,
                                 selectbackground=ACCENT_DIM)
        self.pw_entry.pack(side="left", fill="x", expand=True, ipady=8, padx=(10, 0))
        self.pw_entry.bind("<FocusIn>",  lambda _: pw_row.config(highlightbackground=ACCENT))
        self.pw_entry.bind("<FocusOut>", lambda _: pw_row.config(highlightbackground=BORDER))
        self.pw_entry.bind("<KeyRelease>", lambda _: self._update_strength())

        self._pw_show = False
        tk.Button(pw_row, text="◑", bg=CARD2, fg=FG_DIM,
                  activebackground=CARD2, activeforeground=FG,
                  relief="flat", cursor="hand2", font=(FONT, 11), bd=0,
                  command=self._toggle_pw).pack(side="right", padx=6)

        # Strength bar + label
        strength_row = tk.Frame(parent, bg=BG)
        strength_row.pack(fill="x", pady=(6, 0))

        self.strength_bar = ttk.Progressbar(strength_row, style="Strength.Horizontal.TProgressbar",
                                            length=200, maximum=5, value=0)
        self.strength_bar.pack(side="left")
        self.strength_lbl = mk_label(strength_row, "", size=8, color=FG_DIM)
        self.strength_lbl.pack(side="left", padx=(8, 0))

        # Generator
        gen_row = tk.Frame(parent, bg=BG)
        gen_row.pack(fill="x", pady=(8, 0))
        mk_label(gen_row, "Generate:", size=9, color=FG_DIM).pack(side="left", padx=(0, 8))
        for length in (12, 16, 20, 32):
            mk_btn(gen_row, str(length), lambda l=length: self._gen(l),
                   style="ghost").pack(side="left", padx=2)

    def _toggle_pw(self):
        self._pw_show = not self._pw_show
        self.pw_entry.config(show="" if self._pw_show else "•")

    def _gen(self, length):
        pw = generate_password(length)
        self.vars["pw"].set(pw)
        self.pw_entry.config(show="")
        self._pw_show = True
        self._update_strength()

    def _update_strength(self):
        pw = self.vars["pw"].get()
        score, label, color = password_strength(pw)
        self.strength_bar["value"] = score
        self.strength_lbl.config(text=label, fg=color)
        s = ttk.Style()
        s.configure("Strength.Horizontal.TProgressbar", background=color)

    def _save(self):
        site = self.vars["name"].get().strip()
        user = self.vars["user"].get().strip()
        pw   = self.vars["pw"].get()
        if not site:
            self.err_var.set("⚠  Site/App name is required.")
            return
        if not pw:
            self.err_var.set("⚠  Password is required.")
            return
        # Use site::username as key so multiple accounts per site are allowed
        key = f"{site}::{user}" if user else site
        data = {
            "site":     site,
            "username": user,
            "password": pw,
            "url":      self.vars["url"].get().strip(),
            "notes":    self.vars["notes"].get().strip(),
        }
        self.destroy()
        self.on_save(key, data)

# ── Vault Screen ──────────────────────────────────────────────────────────────
class VaultScreen(tk.Frame):
    IDLE_TIMEOUT = 5 * 60 * 1000  # 5 minutes in ms

    def __init__(self, master, master_pw, entries, salt):
        super().__init__(master, bg=BG)
        self.master_pw  = master_pw
        self.entries    = entries
        self.salt       = salt
        self._toast_job = None
        self._lock_job  = None
        self.logo_service = LogoService(self)
        self._tree_logos = {}
        self._detail_logo = None
        self.pack(fill="both", expand=True)
        self._build()
        self._refresh()
        self._reset_idle()
        # Reset idle timer on any mouse/key activity
        self.winfo_toplevel().bind_all("<Motion>",   lambda _: self._reset_idle())
        self.winfo_toplevel().bind_all("<KeyPress>",  lambda _: self._reset_idle())
        self.winfo_toplevel().bind_all("<Button>",    lambda _: self._reset_idle())

    def _reset_idle(self):
        if self._lock_job:
            self.after_cancel(self._lock_job)
        self._lock_job = self.after(self.IDLE_TIMEOUT, self._auto_lock)

    def _auto_lock(self):
        self.entries.clear()
        self.master_pw = ""
        top = self.winfo_toplevel()
        top._show_toast_on_login = "🔒  Auto-locked after 5 minutes of inactivity."
        for w in top.winfo_children():
            w.destroy()
        LoginScreen(top, top._on_unlock)

    def _build(self):
        # ── Sidebar ──
        sidebar = tk.Frame(self, bg=CARD, width=232)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # Logo (fixed, not scrollable)
        logo = tk.Frame(sidebar, bg=CARD, pady=24)
        logo.pack(fill="x")
        c = tk.Canvas(logo, width=36, height=36, bg=CARD, highlightthickness=0)
        c.pack()
        c.create_oval(2, 2, 34, 34, fill=ACCENT_DIM, outline=ACCENT, width=1)
        c.create_text(18, 18, text="🔐", font=(FONT, 14))
        mk_label(logo, "Kvaults", size=15, bold=True, bg=CARD).pack(pady=(6, 0))
        mk_label(logo, "Private by design", size=8, color=FG_DIM, bg=CARD).pack()

        mk_separator(sidebar, BORDER).pack(fill="x", padx=16)

        # Scrollable area for stats + actions
        sb_canvas = tk.Canvas(sidebar, bg=CARD, highlightthickness=0, bd=0)
        sb_canvas.pack(side="left", fill="both", expand=True)
        sb_scroll = ttk.Scrollbar(sidebar, orient="vertical",
                                  command=sb_canvas.yview,
                                  style="Vault.Vertical.TScrollbar")
        sb_canvas.configure(yscrollcommand=sb_scroll.set)

        sb_inner = tk.Frame(sb_canvas, bg=CARD)
        sb_win = sb_canvas.create_window((0, 0), window=sb_inner, anchor="nw")

        def _sb_resize(event):
            sb_canvas.itemconfig(sb_win, width=event.width)
        def _sb_scroll_region(event):
            sb_canvas.configure(scrollregion=sb_canvas.bbox("all"))
            # Only show scrollbar when content overflows
            if sb_inner.winfo_reqheight() > sb_canvas.winfo_height():
                sb_scroll.pack(side="right", fill="y")
            else:
                sb_scroll.pack_forget()
        sb_canvas.bind("<Configure>", _sb_resize)
        sb_inner.bind("<Configure>", _sb_scroll_region)
        sb_canvas.bind_all("<MouseWheel>", lambda e: sb_canvas.yview_scroll(
            int(-1 * (e.delta / 120)), "units") if sidebar.winfo_containing(e.x_root, e.y_root) else None)

        # Stats block
        stats = tk.Frame(sb_inner, bg=CARD, padx=16, pady=14)
        stats.pack(fill="x")

        self.count_var = tk.StringVar(value="0 passwords")
        self.weak_var  = tk.StringVar(value="")
        self.last_var  = tk.StringVar(value="")

        for var, icon, color in [
            (self.count_var, "🔑", FG),
            (self.weak_var,  "⚠️", WARN),
            (self.last_var,  "🕐", FG_DIM),
        ]:
            row = tk.Frame(stats, bg=CARD)
            row.pack(fill="x", pady=2)
            mk_label(row, icon, size=9, bg=CARD).pack(side="left", padx=(0, 6))
            tk.Label(row, textvariable=var, bg=CARD, fg=color,
                     font=(FONT, 9), anchor="w").pack(side="left", fill="x")

        mk_separator(sb_inner, BORDER).pack(fill="x", padx=16)

        # Add button
        add_btn = mk_btn(sb_inner, "+  Add Password", self._add)
        add_btn.pack(fill="x", padx=16, pady=(14, 16), ipady=4)

        mk_separator(sb_inner, BORDER).pack(fill="x", padx=16)

        # Sidebar actions
        for text, cmd in [("📋  Copy Password", self._copy_pw),
                          ("👁  Reveal Password", self._reveal_pw),
                          ("✏️  Edit Entry",       self._edit),
                          ("🗑  Delete Entry",     self._delete),
                          ("💾  Backup Vault",     self._backup),
                          ("📂  Restore Vault",    self._restore),
                          ("📊  Security Report",  self._security_report),
                          ("🛡️  Setup 2FA",         self._setup_2fa)]:
            b = tk.Button(sb_inner, text=text, command=cmd,
                          bg=CARD, fg=FG_SUB, activebackground=CARD2,
                          activeforeground=FG, relief="flat",
                          font=(FONT, 10), cursor="hand2",
                          anchor="w", padx=20, pady=10)
            b.pack(fill="x")
            b.bind("<Enter>", lambda e, w=b: w.config(bg=CARD2, fg=FG))
            b.bind("<Leave>", lambda e, w=b: w.config(bg=CARD,  fg=FG_SUB))

        # ── Main content ──
        content = tk.Frame(self, bg=BG)
        content.pack(side="left", fill="both", expand=True)

        # Top bar
        topbar = tk.Frame(content, bg=BG, padx=24)
        topbar.pack(fill="x")
        title = tk.Frame(topbar, bg=BG)
        title.pack(side="left", pady=18)
        mk_label(title, "Your vault", size=18, bold=True).pack(anchor="w")
        mk_label(title, "Search and manage every saved login", size=8,
                 color=FG_DIM).pack(anchor="w")

        # Search — same height as title, anchored center
        search_outer = tk.Frame(topbar, bg=CARD2, highlightthickness=1,
                                highlightbackground=BORDER, highlightcolor=ACCENT)
        search_outer.pack(side="right", anchor="center", pady=16)
        mk_label(search_outer, "🔍", size=10, color=FG_DIM, bg=CARD2).pack(
            side="left", padx=(10, 4))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._refresh())
        se = tk.Entry(search_outer, textvariable=self.search_var,
                      bg=CARD2, fg=FG, insertbackground=FG,
                      relief="flat", font=(FONT, 10), bd=0, width=22,
                      selectbackground=ACCENT_DIM)
        se.pack(side="left", ipady=7, padx=(0, 10))
        se.bind("<FocusIn>",  lambda _: search_outer.config(highlightbackground=ACCENT))
        se.bind("<FocusOut>", lambda _: search_outer.config(highlightbackground=BORDER))

        mk_separator(content, BORDER).pack(fill="x", padx=24)

        # Table
        self.table_frame = tk.Frame(content, bg=BG, padx=24, pady=16)
        self.table_frame.pack(fill="both", expand=True)
        table_frame = self.table_frame

        cols = ("name", "username", "url", "strength")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="tree headings",
                                 style="Vault.Treeview", selectmode="browse")

        self.tree.heading("#0", text="", anchor="center")
        self.tree.column("#0", width=58, minwidth=58, stretch=False, anchor="center")
        headers = [("name", "Service", 180),
                   ("username", "Username", 200), ("url", "URL", 200),
                   ("strength", "Strength", 100)]
        for col, head, w in headers:
            self.tree.heading(col, text=head, anchor="w")
            self.tree.column(col, width=w, anchor="w", stretch=(col == "username"), minwidth=w)

        sb = ttk.Scrollbar(table_frame, orient="vertical",
                           command=self.tree.yview,
                           style="Vault.Vertical.TScrollbar")
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.tree.bind("<Double-1>", lambda _: self._edit())
        self.tree.bind("<<TreeviewSelect>>", lambda _: self._on_select())
        self.tree.tag_configure("odd",  background=CARD)
        self.tree.tag_configure("even", background="#1e1e2c")

        # ── Detail Panel ──
        self.detail_panel = tk.Frame(content, bg=CARD, width=300)
        self.detail_panel.pack_propagate(False)
        # hidden until an entry is selected

        self._build_detail_panel()

        # Empty state (shown when no entries)
        self.empty_frame = tk.Frame(content, bg=BG)
        ec = tk.Canvas(self.empty_frame, width=64, height=64,
                       bg=BG, highlightthickness=0)
        ec.pack(pady=(60, 0))
        ec.create_oval(4, 4, 60, 60, fill=CARD, outline=BORDER, width=2)
        ec.create_text(32, 32, text="🔒", font=(FONT, 22))
        mk_label(self.empty_frame, "No passwords yet", size=13,
                 bold=True, color=FG_SUB).pack(pady=(12, 4))
        mk_label(self.empty_frame, "Click '+ Add Password' to get started.",
                 size=9, color=FG_DIM).pack()
        mk_btn(self.empty_frame, "+  Add your first password",
               self._add).pack(pady=20, ipady=4)

        # Toast — sits above everything via place()
        self.toast_frame = tk.Frame(content, bg=ACCENT_DIM, padx=20, pady=10)
        self.toast_lbl = mk_label(self.toast_frame, "", size=9,
                                  color=FG, bg=ACCENT_DIM)
        self.toast_lbl.pack()
        self._toast_y = 1.0   # for slide-up animation

    def _build_detail_panel(self):
        p = self.detail_panel

        # Header
        hdr = tk.Frame(p, bg=CARD, padx=20, pady=20)
        hdr.pack(fill="x")

        self.d_icon = tk.Canvas(hdr, width=44, height=44, bg=CARD,
                                highlightthickness=0)
        self.d_icon.pack(side="left")
        self.d_icon.create_oval(2, 2, 42, 42, fill=ACCENT_DIM,
                                outline=ACCENT, width=1, tags="circle")
        self.d_icon.create_text(22, 22, text="?", font=(FONT, 16),
                                fill=FG, tags="letter")

        title_col = tk.Frame(hdr, bg=CARD, padx=12)
        title_col.pack(side="left", fill="x", expand=True)
        self.d_name = mk_label(title_col, "", size=13, bold=True, bg=CARD)
        self.d_name.pack(anchor="w")
        self.d_sub  = mk_label(title_col, "", size=8, color=FG_DIM, bg=CARD)
        self.d_sub.pack(anchor="w", pady=(2, 0))

        close_btn = tk.Button(hdr, text="✕", bg=CARD, fg=FG_DIM,
                              activebackground=CARD, activeforeground=FG,
                              relief="flat", cursor="hand2",
                              font=(FONT, 11), bd=0,
                              command=self._close_detail)
        close_btn.pack(side="right", anchor="n")

        mk_separator(p, BORDER).pack(fill="x")

        # Fields scroll area
        dp_canvas = tk.Canvas(p, bg=CARD, highlightthickness=0, bd=0)
        dp_canvas.pack(fill="both", expand=True)
        dp_scroll = ttk.Scrollbar(p, orient="vertical",
                                  command=dp_canvas.yview,
                                  style="Vault.Vertical.TScrollbar")
        dp_canvas.configure(yscrollcommand=dp_scroll.set)

        fields_frame = tk.Frame(dp_canvas, bg=CARD, padx=20, pady=16)
        dp_win = dp_canvas.create_window((0, 0), window=fields_frame, anchor="nw")

        def _dp_resize(event):
            dp_canvas.itemconfig(dp_win, width=event.width)
        def _dp_scroll_region(event):
            dp_canvas.configure(scrollregion=dp_canvas.bbox("all"))
            if fields_frame.winfo_reqheight() > dp_canvas.winfo_height():
                dp_scroll.pack(side="right", fill="y", before=dp_canvas)
            else:
                dp_scroll.pack_forget()
        dp_canvas.bind("<Configure>", _dp_resize)
        fields_frame.bind("<Configure>", _dp_scroll_region)
        dp_canvas.bind("<MouseWheel>", lambda e: dp_canvas.yview_scroll(
            int(-1 * (e.delta / 120)), "units"))

        self.d_fields = {}
        for key, label_text in [("username", "USERNAME"),
                                 ("password", "PASSWORD"),
                                 ("url",      "URL"),
                                 ("notes",    "NOTES")]:
            row = tk.Frame(fields_frame, bg=CARD)
            row.pack(fill="x", pady=(0, 14))

            top = tk.Frame(row, bg=CARD)
            top.pack(fill="x")
            mk_label(top, label_text, size=7, color=FG_DIM, bold=True,
                     bg=CARD).pack(side="left")

            cp = tk.Button(top, text="Copy",
                           command=lambda k=key: self._copy_field(k),
                           bg=CARD, fg=ACCENT, activebackground=CARD,
                           activeforeground=ACCENT_H, relief="flat",
                           font=(FONT, 7), cursor="hand2", bd=0)
            cp.pack(side="right")

            val_lbl = mk_label(row, "—", size=10, color=FG_SUB, bg=CARD)
            val_lbl.pack(anchor="w", pady=(3, 0))
            self.d_fields[key] = val_lbl

            if key == "password":
                sbar_row = tk.Frame(row, bg=CARD)
                sbar_row.pack(fill="x", pady=(4, 0))
                self.d_strength_bar = ttk.Progressbar(
                    sbar_row, style="Strength.Horizontal.TProgressbar",
                    length=160, maximum=5, value=0)
                self.d_strength_bar.pack(side="left")
                self.d_strength_lbl = mk_label(sbar_row, "", size=8,
                                               color=FG_DIM, bg=CARD)
                self.d_strength_lbl.pack(side="left", padx=(8, 0))

            mk_separator(row, BORDER).pack(fill="x", pady=(10, 0))

        # Action buttons at bottom
        mk_separator(p, BORDER).pack(fill="x")
        act = tk.Frame(p, bg=CARD, padx=20, pady=14)
        act.pack(fill="x")
        mk_btn(act, "✏️  Edit",   self._edit,   style="ghost").pack(side="left", padx=(0, 8))
        mk_btn(act, "🗑  Delete", self._delete, style="danger").pack(side="left")

    def _on_select(self):
        name = self.tree.selection()
        if not name:
            return
        name = name[0]
        data = self.entries.get(name, {})
        self._show_detail(name, data)

    def _show_detail(self, name, data):
        site   = data.get("site", name.split("::")[0])
        letter = site[0].upper() if site else "?"
        self.d_icon.itemconfig("letter", text=letter)
        self.logo_service.request(
            site, data.get("url", ""), 40,
            lambda image, key=name: self._set_detail_logo(key, image),
        )
        self.d_name.config(text=site)
        self.d_sub.config(text=data.get("username", "") or data.get("url", "") or "No details")

        pw = data.get("password", "")
        self.d_fields["username"].config(
            text=data.get("username", "") or "—", fg=FG)
        self.d_fields["password"].config(text="••••••••••••", fg=FG_DIM)
        self.d_fields["url"].config(
            text=data.get("url", "") or "—", fg=FG)
        self.d_fields["notes"].config(
            text=data.get("notes", "") or "—", fg=FG_SUB)

        score, slabel, scolor = password_strength(pw)
        self.d_strength_bar["value"] = score
        self.d_strength_lbl.config(text=slabel, fg=scolor)
        s = ttk.Style()
        s.configure("Strength.Horizontal.TProgressbar", background=scolor)

        # Show panel if hidden
        if not self.detail_panel.winfo_ismapped():
            self.detail_panel.pack(side="right", fill="y",
                                   before=self.toast_frame)

    def _close_detail(self):
        self.detail_panel.pack_forget()
        self.tree.selection_remove(*self.tree.selection())

    def _copy_field(self, key):
        name = self.tree.selection()
        if not name:
            return
        name = name[0]
        data = self.entries.get(name, {})
        value = data.get("password" if key == "password" else key, "")
        if not value:
            self._toast(f"No {key} to copy.", DANGER)
            return
        copy_to_clipboard(self.winfo_toplevel(), value)
        self._toast(f"📋  {key.capitalize()} copied — clears in 30s.")

    def _refresh(self):
        q = self.search_var.get().lower()
        self.tree.delete(*self.tree.get_children())
        weak = 0
        last = ""
        for i, (key, data) in enumerate(self.entries.items()):
            site = data.get("site", key.split("::")[0])
            user = data.get("username", "")
            if q and q not in site.lower() and q not in user.lower():
                continue
            pw = data.get("password", "")
            score, slabel, _ = password_strength(pw)
            if score <= 2:
                weak += 1
            tag = "odd" if i % 2 else "even"
            self.tree.insert("", "end", iid=key, tags=(tag,), values=(
                site,
                user,
                data.get("url", "") or "—",
                slabel or "—",
            ))
            self.logo_service.request(
                site, data.get("url", ""), 32,
                lambda image, item=key: self._set_tree_logo(item, image),
            )
            last = site

        count = len(self.tree.get_children())
        total = len(self.entries)
        self.count_var.set(f"{total} password{'s' if total != 1 else ''}")
        self.weak_var.set(f"{weak} weak password{'s' if weak != 1 else ''}" if weak else "All passwords strong")
        self.last_var.set(f"Last: {last}" if last else "")

        # Toggle empty state
        if total == 0:
            self.table_frame.pack_forget()
            self.empty_frame.place(relx=0.5, rely=0.5, anchor="center")
        else:
            self.empty_frame.place_forget()
            self.table_frame.pack(fill="both", expand=True)

    def _set_tree_logo(self, item, image):
        if self.tree.exists(item):
            self._tree_logos[item] = image
            self.tree.item(item, image=image)

    def _set_detail_logo(self, item, image):
        selection = self.tree.selection()
        if not selection or selection[0] != item:
            return
        self._detail_logo = image
        self.d_icon.delete("logo")
        self.d_icon.create_image(22, 22, image=image, tags="logo")

    def _selected(self):
        sel = self.tree.selection()
        if not sel:
            self._toast("Select an entry first.", DANGER)
            return None
        return sel[0]

    def _toast(self, msg, color=ACCENT_DIM):
        if self._toast_job:
            self.after_cancel(self._toast_job)
        self.toast_frame.config(bg=color)
        self.toast_lbl.config(text=msg, bg=color)
        self._toast_y = 1.04
        self._animate_toast()
        self._toast_job = self.after(2800, self._hide_toast)

    def _animate_toast(self):
        if self._toast_y > 0.96:
            self._toast_y = round(self._toast_y - 0.01, 3)
            self.toast_frame.place(relx=0.5, rely=self._toast_y, anchor="s")
            self.after(16, self._animate_toast)

    def _hide_toast(self):
        self.toast_frame.place_forget()
        self._toast_job = None

    def _persist(self):
        save(self.entries, self.master_pw, self.salt)

    def _add(self):
        EntryDialog(self.winfo_toplevel(), self._on_save)

    def _edit(self):
        name = self._selected()
        if not name: return
        EntryDialog(self.winfo_toplevel(), self._on_save,
                    existing=(name, self.entries[name]))

    def _on_save(self, name, data):
        self.entries[name] = data
        save_entry(name, data, self.master_pw, self.salt)
        self._refresh()
        self._toast(f"✔  '{name}' saved.", SUCCESS)
        self._show_detail(name, data)

    def _delete(self):
        name = self._selected()
        if not name: return
        if messagebox.askyesno("Delete Entry", f"Delete '{name}'?",
                               parent=self.winfo_toplevel()):
            del self.entries[name]
            delete_entry(name)
            self._close_detail()
            self._refresh()
            self._toast(f"🗑  '{name}' deleted.", DANGER)

    def _backup(self):
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(
            title="Save Backup",
            defaultextension=".db",
            filetypes=[("Vault Backup", "*.db"), ("All Files", "*.*")],
            initialfile="kvaults_backup.db"
        )
        if not path:
            return
        try:
            from storage import backup
            backup(path)
            self._toast(f"💾  Backup saved.", SUCCESS)
        except Exception as e:
            self._toast(f"Backup failed: {e}", DANGER)

    def _restore(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            title="Select Backup File",
            filetypes=[("Vault Backup", "*.db"), ("All Files", "*.*")]
        )
        if not path:
            return
        if not messagebox.askyesno("Restore Vault",
                "This will replace your current vault with the backup.\nContinue?",
                parent=self.winfo_toplevel()):
            return
        try:
            from storage import restore, unlock as _unlock
            restore(path)
            entries, salt = _unlock(self.master_pw)
            self.entries = entries
            self.salt    = salt
            self._refresh()
            self._toast("📂  Vault restored from backup.", SUCCESS)
        except ValueError:
            self._toast("Restore failed: wrong master password for backup.", DANGER)
        except Exception as e:
            self._toast(f"Restore failed: {e}", DANGER)

    def _security_report(self):
        win = tk.Toplevel(self.winfo_toplevel())
        win.title("Security Report")
        win.configure(bg=BG)
        win.grab_set()
        win.resizable(False, False)

        f = tk.Frame(win, bg=BG, padx=28, pady=24)
        f.pack(fill="both", expand=True)

        mk_label(f, "📊  Security Report", size=14, bold=True).pack(anchor="w")
        mk_label(f, "Overview of your vault's password health.",
                 size=9, color=FG_DIM).pack(anchor="w", pady=(2, 14))
        mk_separator(f).pack(fill="x", pady=(0, 14))

        weak, reused, total = [], {}, len(self.entries)
        pw_map = {}
        for name, data in self.entries.items():
            pw = data.get("password", "")
            score, _, _ = password_strength(pw)
            if score <= 2:
                weak.append(name)
            pw_map.setdefault(pw, []).append(name)
        reused = {pw: names for pw, names in pw_map.items() if len(names) > 1}
        reused_entries = [n for names in reused.values() for n in names]

        strong = total - len(weak)
        score_pct = int((strong / total * 100)) if total else 100

        # Score circle
        score_color = SUCCESS if score_pct >= 80 else WARN if score_pct >= 50 else DANGER
        sc = tk.Canvas(f, width=90, height=90, bg=BG, highlightthickness=0)
        sc.pack(pady=(0, 14))
        sc.create_oval(5, 5, 85, 85, outline=score_color, width=6)
        sc.create_text(45, 40, text=f"{score_pct}%", font=(FONT, 18, "bold"),
                       fill=score_color)
        sc.create_text(45, 62, text="Health", font=(FONT, 8), fill=FG_DIM)

        # Stats rows
        for icon, label_text, value, color in [
            ("🔑", "Total passwords",  str(total),            FG),
            ("✅", "Strong passwords", str(strong),           SUCCESS),
            ("⚠️", "Weak passwords",   str(len(weak)),        WARN if weak   else FG_DIM),
            ("🔄", "Reused passwords", str(len(reused_entries)), DANGER if reused else FG_DIM),
        ]:
            row = tk.Frame(f, bg=CARD, padx=14, pady=10,
                           highlightthickness=1, highlightbackground=BORDER)
            row.pack(fill="x", pady=3)
            mk_label(row, icon,        size=11, bg=CARD).pack(side="left")
            mk_label(row, label_text,  size=10, bg=CARD, color=FG_SUB).pack(side="left", padx=10)
            mk_label(row, value,       size=11, bold=True, bg=CARD, color=color).pack(side="right")

        # Weak list
        if weak:
            mk_label(f, "Weak passwords:", size=9, color=WARN).pack(anchor="w", pady=(14, 4))
            for name in weak:
                mk_label(f, f"  • {name}", size=9, color=FG_SUB).pack(anchor="w")

        # Reused list
        if reused:
            mk_label(f, "Reused passwords:", size=9, color=DANGER).pack(anchor="w", pady=(10, 4))
            for pw, names in reused.items():
                mk_label(f, f"  • {', '.join(names)}", size=9, color=FG_SUB).pack(anchor="w")

        mk_separator(f).pack(fill="x", pady=(16, 12))
        mk_btn(f, "Close", win.destroy, style="ghost").pack(anchor="e")

        win.update_idletasks()
        x = self.winfo_toplevel().winfo_rootx() + (self.winfo_toplevel().winfo_width()  - win.winfo_width())  // 2
        y = self.winfo_toplevel().winfo_rooty() + (self.winfo_toplevel().winfo_height() - win.winfo_height()) // 2
        win.geometry(f"+{x}+{y}")

    def _setup_2fa(self):
        import pyotp
        existing = _totp_secret_exists()
        win = tk.Toplevel(self.winfo_toplevel())
        win.title("Setup Two-Factor Authentication")
        win.configure(bg=BG)
        win.resizable(False, False)
        win.grab_set()

        f = tk.Frame(win, bg=BG, padx=32, pady=24)
        f.pack()

        if existing:
            mk_label(f, "🛡️  2FA is Enabled", size=14, bold=True, color=SUCCESS).pack()
            mk_label(f, "Two-factor authentication is active on this vault.",
                     size=9, color=FG_DIM).pack(pady=(4, 20))
            def disable():
                _delete_totp_secret()
                win.destroy()
                self._toast("🛡️  2FA disabled.", WARN)
            mk_btn(f, "Disable 2FA", disable, style="danger").pack(fill="x", ipady=4)
            mk_btn(f, "Cancel", win.destroy, style="ghost").pack(fill="x", pady=(8, 0), ipady=4)
        else:
            secret = pyotp.random_base32()
            totp   = pyotp.TOTP(secret)
            uri    = totp.provisioning_uri(name="Kvaults", issuer_name="Kvaults")

            mk_label(f, "🛡️  Setup Two-Factor Auth", size=14, bold=True).pack()
            mk_label(f, "Scan the QR code with your authenticator app,",
                     size=9, color=FG_DIM).pack(pady=(4, 0))
            mk_label(f, "then enter the 6-digit code to confirm.",
                     size=9, color=FG_DIM).pack(pady=(0, 14))

            # QR code
            try:
                import qrcode
                from PIL import ImageTk
                qr_img = qrcode.make(uri).resize((180, 180))
                qr_tk  = ImageTk.PhotoImage(qr_img)
                qr_lbl = tk.Label(f, image=qr_tk, bg=BG)
                qr_lbl.image = qr_tk
                qr_lbl.pack(pady=(0, 10))
            except ImportError:
                pass

            # Manual key
            mk_label(f, "Or enter this key manually:", size=8, color=FG_DIM).pack()
            key_box = tk.Frame(f, bg=CARD2, padx=10, pady=6)
            key_box.pack(fill="x", pady=(4, 14))
            tk.Label(key_box, text=secret, bg=CARD2, fg=ACCENT,
                     font=("Courier New", 11), wraplength=280).pack()

            mk_label(f, "Verification code:", size=9, color=FG_SUB).pack(anchor="w")
            code_var = tk.StringVar()
            code_entry = mk_entry(f, textvariable=code_var, width=12)
            code_entry.pack(ipady=8, pady=(4, 0))
            code_entry.focus()

            err_var = tk.StringVar()
            tk.Label(f, textvariable=err_var, bg=BG, fg=DANGER,
                     font=(FONT, 9)).pack(pady=(4, 0))

            def confirm():
                if totp.verify(code_var.get().strip()):
                    _save_totp_secret(secret)
                    win.destroy()
                    self._toast("🛡️  2FA enabled successfully.", SUCCESS)
                else:
                    err_var.set("✕  Invalid code. Try again.")
                    code_var.set("")

            mk_btn(f, "Enable 2FA", confirm).pack(fill="x", ipady=4, pady=(10, 0))
            mk_btn(f, "Cancel", win.destroy, style="ghost").pack(fill="x", pady=(8, 0), ipady=4)
            code_entry.bind("<Return>", lambda _: confirm())

        win.update_idletasks()
        x = self.winfo_toplevel().winfo_rootx() + (self.winfo_toplevel().winfo_width()  - win.winfo_width())  // 2
        y = self.winfo_toplevel().winfo_rooty() + (self.winfo_toplevel().winfo_height() - win.winfo_height()) // 2
        win.geometry(f"+{x}+{y}")

    def _copy_pw(self):
        name = self._selected()
        if not name: return
        copy_to_clipboard(self.winfo_toplevel(), self.entries[name]["password"])
        self._toast("📋  Password copied — clears in 30s.")

    def _reveal_pw(self):
        name = self._selected()
        if not name: return
        pw_lbl = self.d_fields["password"]
        current = pw_lbl.cget("text")
        if "•" in current:
            pw_lbl.config(text=self.entries[name]["password"], fg=SUCCESS)
        else:
            pw_lbl.config(text="••••••••••••", fg=FG_DIM)

# ── App ───────────────────────────────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Kvaults")
        self.geometry("960x600")
        self.minsize(760, 480)
        self.configure(bg=BG)
        self._show_toast_on_login = ""
        apply_styles(self)
        LoginScreen(self, self._on_unlock)

    def _on_unlock(self, master_pw, entries, salt):
        for w in self.winfo_children():
            w.destroy()
        VaultScreen(self, master_pw, entries, salt)

if __name__ == "__main__":
    App().mainloop()
