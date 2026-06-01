#!/usr/bin/env python3
"""Launcher — single click GUI for Local AI Orchestrator.

Uses tkinter (Python standard library). No extra dependencies.
"""

from __future__ import annotations

import os
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter.scrolledtext import ScrolledText

ROOT = Path(__file__).resolve().parent
SCRIPT_DIR = ROOT / "scripts"
IS_WIN = sys.platform == "win32"
IS_MAC = sys.platform == "darwin"


def _quote(path):
    return str(path)


def run_script(script_name: str, log_widget: ScrolledText):
    """Run a shell/bat/python script and stream output to log widget."""
    log_widget.configure(state="normal")
    log_widget.insert(tk.END, f"\n────────── {script_name} ──────────\n\n")
    log_widget.see(tk.END)
    log_widget.configure(state="disabled")

    if script_name.startswith("bash "):
        cmd = ["bash", script_name[5:]]
    elif script_name.endswith(".sh"):
        cmd = ["bash", str(SCRIPT_DIR / script_name)]
    elif script_name.endswith(".ps1"):
        cmd = [
            "powershell",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(SCRIPT_DIR / script_name),
        ]
    elif script_name.endswith(".py") or " " in script_name:
        cmd = [sys.executable] + script_name.split()
    else:
        cmd = [sys.executable, str(SCRIPT_DIR / script_name)]

    try:
        proc = subprocess.Popen(
            cmd,
            cwd=str(ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            shell=False,
        )
        for line in proc.stdout or []:
            log_widget.configure(state="normal")
            log_widget.insert(tk.END, line)
            log_widget.see(tk.END)
            log_widget.configure(state="disabled")
        proc.wait()
    except Exception as exc:
        log_widget.configure(state="normal")
        log_widget.insert(tk.END, f"ERROR: {exc}\n")
        log_widget.see(tk.END)
        log_widget.configure(state="disabled")

    log_widget.configure(state="normal")
    log_widget.insert(tk.END, "\n────────── Done ──────────\n")
    log_widget.see(tk.END)
    log_widget.configure(state="disabled")


def launch(log_widget: ScrolledText, script_name: str):
    threading.Thread(
        target=run_script, args=(script_name, log_widget), daemon=True
    ).start()


def open_url(url: str):
    import webbrowser

    webbrowser.open(url)


def open_folder(path: str):
    if IS_MAC:
        subprocess.run(["open", str(ROOT / path)])
    elif IS_WIN:
        os.startfile(str(ROOT / path))
    else:
        subprocess.run(["xdg-open", str(ROOT / path)])


def main():
    root = tk.Tk()
    root.title("Local AI Orchestrator Launcher")
    root.geometry("720x600")
    root.configure(bg="#1e1e2e")

    # Title
    title = tk.Label(
        root,
        text="🧠 Local AI Orchestrator",
        font=("Helvetica", 18, "bold"),
        bg="#1e1e2e",
        fg="#cdd6f4",
    )
    title.pack(pady=(16, 4))
    subtitle = tk.Label(
        root,
        text="点击按钮启动对应功能 — 输出见下方日志",
        font=("Helvetica", 11),
        bg="#1e1e2e",
        fg="#a6adc8",
    )
    subtitle.pack(pady=(0, 10))

    # Button grid
    btn_frame = tk.Frame(root, bg="#1e1e2e")
    btn_frame.pack(pady=4)

    btn_style = {
        "font": ("Helvetica", 10),
        "bg": "#313244",
        "fg": "#cdd6f4",
        "activebackground": "#45475a",
        "activeforeground": "#cdd6f4",
        "relief": "flat",
        "width": 22,
        "height": 1,
        "bd": 0,
        "highlightthickness": 0,
    }

    setup_script = "local_setup_mac.sh" if not IS_WIN else "local_setup_windows.ps1"
    start_script = "start_local.sh" if not IS_WIN else "start_local_windows.ps1"

    buttons = [
        ("🔧 安装环境", setup_script),
        ("🩺 运行体检", "doctor.py"),
        ("🚀 启动项目", start_script),
        ("🌐 打开 Web UI", ""),
        ("🔄 初始化 ChatGPT 登录", "init_web_ai_profile.py --provider chatgpt"),
        ("🧪 测试 ChatGPT", "test_web_ai_chatgpt.py"),
        ("✏️ 初始化 Claude 登录", "init_web_ai_profile.py --provider claude"),
        ("🧪 测试 Claude", "test_web_ai_claude.py"),
        ("🔧 运行修复矩阵", "e2e_agent_driven_repair_matrix.py"),
    ]

    # Log area
    log = ScrolledText(
        root,
        height=16,
        font=("Courier", 9),
        bg="#1e1e2e",
        fg="#a6adc8",
        insertbackground="#cdd6f4",
        state="disabled",
    )
    log.pack(fill=tk.BOTH, expand=True, padx=12, pady=(4, 2))

    for i, (label_text, script) in enumerate(buttons):
        row = i // 3
        col = i % 3
        f = tk.Frame(btn_frame, bg="#1e1e2e")
        f.grid(row=row, column=col, padx=3, pady=2, sticky="ew")
        if script:
            btn = tk.Button(
                f,
                text=label_text,
                command=lambda s=script: launch(log, s),
                **btn_style,
            )
        elif label_text == "🌐 打开 Web UI":
            btn = tk.Button(
                f,
                text=label_text,
                command=lambda: open_url("http://localhost:8422"),
                **btn_style,
            )
        else:
            btn = tk.Button(f, text=label_text, **btn_style)
        btn.pack(fill=tk.X)

    # Bottom row
    bottom = tk.Frame(root, bg="#1e1e2e")
    bottom.pack(fill=tk.X, padx=12, pady=6)
    tk.Button(
        bottom,
        text="📂 查看测试报告",
        command=lambda: open_folder("runtime/test_reports"),
        font=("Helvetica", 9),
        bg="#45475a",
        fg="#cdd6f4",
        relief="flat",
    ).pack(side=tk.LEFT, padx=2)
    tk.Button(
        bottom,
        text="📖 打开 README",
        command=lambda: open_folder("README.md"),
        font=("Helvetica", 9),
        bg="#45475a",
        fg="#cdd6f4",
        relief="flat",
    ).pack(side=tk.LEFT, padx=2)

    root.mainloop()


if __name__ == "__main__":
    main()
