"""
SmartVision AZS — Native Windows Installer Wizard for Belorusneft.
Extracts application payload, sets up shortcuts, and prepares runtime environment.
"""
import sys
import os
import shutil
import zipfile
import subprocess
import threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

APP_NAME = "SmartVision AZS"
APP_VENDOR = "Белоруснефть"
APP_VERSION = "1.2.0-LTS"
DEFAULT_INSTALL_DIR = Path(os.environ.get("LOCALAPPDATA", "C:")) / "SmartVision_AZS"


class InstallerApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Установка {APP_NAME} — {APP_VENDOR} (v{APP_VERSION})")
        self.root.geometry("620x420")
        self.root.resizable(False, False)

        # Style configuration
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        # Colors: Belorusneft Emerald Green & Dark Slate
        self.bg_color = "#0F172A"
        self.card_color = "#1E293B"
        self.accent_green = "#00843D"
        self.accent_lightgreen = "#00A84D"
        self.accent_gold = "#FFCC00"
        self.text_white = "#F8FAFC"
        self.text_gray = "#94A3B8"

        self.root.configure(bg=self.bg_color)
        
        # State variables
        self.install_dir = tk.StringVar(value=str(DEFAULT_INSTALL_DIR))
        self.create_desktop_shortcut = tk.BooleanVar(value=True)
        self.create_start_menu = tk.BooleanVar(value=True)
        self.launch_after = tk.BooleanVar(value=True)

        # Build UI stages
        self.current_step = 0
        self.step_frames = []
        self._build_header()
        self._build_steps()
        self._show_step(0)

    def _build_header(self):
        header_frame = tk.Frame(self.root, bg="#0B1120", height=65)
        header_frame.pack(fill="x", side="top")
        header_frame.pack_propagate(False)

        title_lbl = tk.Label(
            header_frame,
            text=f"БЕЛОРУСНЕФТЬ | {APP_NAME}",
            font=("Segoe UI", 13, "bold"),
            fg=self.text_white,
            bg="#0B1120",
        )
        title_lbl.pack(anchor="w", padx=20, pady=(12, 0))

        sub_lbl = tk.Label(
            header_frame,
            text="Мастер установки программного комплекса оператора АЗС",
            font=("Segoe UI", 9),
            fg=self.accent_gold,
            bg="#0B1120",
        )
        sub_lbl.pack(anchor="w", padx=20, pady=(0, 10))

    def _build_steps(self):
        self.container = tk.Frame(self.root, bg=self.bg_color)
        self.container.pack(fill="both", expand=True, padx=20, pady=15)

        # Step 0: Welcome & Features
        s0 = tk.Frame(self.container, bg=self.bg_color)
        s0_title = tk.Label(
            s0,
            text=f"Добро пожаловать в установку {APP_NAME}",
            font=("Segoe UI", 12, "bold"),
            fg=self.text_white,
            bg=self.bg_color,
        )
        s0_title.pack(anchor="w", pady=(5, 10))

        desc_text = (
            f"Программный комплекс {APP_NAME} (версия {APP_VERSION}) предназначен для "
            "автоматизации процессов обслуживания на автозаправочных станциях сети «Белоруснефть».\n\n"
            "Ключевые модули:\n"
            "• Zero-Click Drive&Pay — идентификация номеров РБ и налив без кассы\n"
            "• Автоматическая защита E-STOP — мгновенная отсечка насоса (<300мс)\n"
            "• Интерактивная финансово-экономическая модель ТЭО (ROI)\n"
            "• Локальная база данных SQLite WAL и автономная работа (Offline)\n\n"
            "Нажмите «Далее», чтобы продолжить установку."
        )
        s0_desc = tk.Label(
            s0,
            text=desc_text,
            font=("Segoe UI", 9),
            fg=self.text_gray,
            bg=self.bg_color,
            justify="left",
            wraplength=570,
        )
        s0_desc.pack(anchor="w", pady=5)
        self.step_frames.append(s0)

        # Step 1: Directory Selection & Options
        s1 = tk.Frame(self.container, bg=self.bg_color)
        s1_title = tk.Label(
            s1,
            text="Выбор папки установки",
            font=("Segoe UI", 12, "bold"),
            fg=self.text_white,
            bg=self.bg_color,
        )
        s1_title.pack(anchor="w", pady=(5, 10))

        dir_lbl = tk.Label(
            s1,
            text="Программа будет установлена в следующую директорию:",
            font=("Segoe UI", 9),
            fg=self.text_gray,
            bg=self.bg_color,
        )
        dir_lbl.pack(anchor="w", pady=(0, 5))

        dir_frame = tk.Frame(s1, bg=self.bg_color)
        dir_frame.pack(fill="x", pady=5)

        dir_entry = tk.Entry(
            dir_frame,
            textvariable=self.install_dir,
            font=("Segoe UI", 9),
            bg="#1E293B",
            fg=self.text_white,
            insertbackground="white",
            relief="flat",
            highlightthickness=1,
            highlightcolor=self.accent_green,
            highlightbackground="#334155",
        )
        dir_entry.pack(side="left", fill="x", expand=True, ipady=4, padx=(0, 10))

        browse_btn = tk.Button(
            dir_frame,
            text="Обзор...",
            command=self._browse_dir,
            font=("Segoe UI", 9),
            bg="#334155",
            fg=self.text_white,
            activebackground="#475569",
            activeforeground="white",
            relief="flat",
            padx=10,
        )
        browse_btn.pack(side="right")

        opts_frame = tk.LabelFrame(
            s1,
            text=" Дополнительные ярлыки ",
            font=("Segoe UI", 9, "bold"),
            bg=self.bg_color,
            fg=self.text_white,
            padx=10,
            pady=10,
        )
        opts_frame.pack(fill="x", pady=15)

        cb1 = tk.Checkbutton(
            opts_frame,
            text="Создать ярлык на Рабочем столе",
            variable=self.create_desktop_shortcut,
            font=("Segoe UI", 9),
            bg=self.bg_color,
            fg=self.text_white,
            selectcolor="#1E293B",
            activebackground=self.bg_color,
            activeforeground=self.text_white,
        )
        cb1.pack(anchor="w", pady=2)

        cb2 = tk.Checkbutton(
            opts_frame,
            text="Создать ярлык в меню «Пуск»",
            variable=self.create_start_menu,
            font=("Segoe UI", 9),
            bg=self.bg_color,
            fg=self.text_white,
            selectcolor="#1E293B",
            activebackground=self.bg_color,
            activeforeground=self.text_white,
        )
        cb2.pack(anchor="w", pady=2)

        self.step_frames.append(s1)

        # Step 2: Progress
        s2 = tk.Frame(self.container, bg=self.bg_color)
        s2_title = tk.Label(
            s2,
            text="Установка файлов программы...",
            font=("Segoe UI", 12, "bold"),
            fg=self.text_white,
            bg=self.bg_color,
        )
        s2_title.pack(anchor="w", pady=(5, 10))

        self.progress_lbl = tk.Label(
            s2,
            text="Подготовка к установке...",
            font=("Segoe UI", 9),
            fg=self.text_gray,
            bg=self.bg_color,
        )
        self.progress_lbl.pack(anchor="w", pady=(10, 5))

        self.progress_bar = ttk.Progressbar(s2, mode="determinate", maximum=100)
        self.progress_bar.pack(fill="x", pady=10)

        self.step_frames.append(s2)

        # Step 3: Finish
        s3 = tk.Frame(self.container, bg=self.bg_color)
        s3_title = tk.Label(
            s3,
            text="Установка успешно завершена!",
            font=("Segoe UI", 13, "bold"),
            fg=self.accent_lightgreen,
            bg=self.bg_color,
        )
        s3_title.pack(anchor="w", pady=(10, 15))

        s3_desc = tk.Label(
            s3,
            text=f"Программный комплекс {APP_NAME} установлен и готов к работе на станции.\n\n"
                 "Вы можете запускать приложение через созданный ярлык или из директории установки.",
            font=("Segoe UI", 9),
            fg=self.text_white,
            bg=self.bg_color,
            justify="left",
            wraplength=570,
        )
        s3_desc.pack(anchor="w", pady=5)

        cb_launch = tk.Checkbutton(
            s3,
            text=f"Запустить {APP_NAME} прямо сейчас",
            variable=self.launch_after,
            font=("Segoe UI", 9, "bold"),
            bg=self.bg_color,
            fg=self.accent_gold,
            selectcolor="#1E293B",
            activebackground=self.bg_color,
            activeforeground=self.accent_gold,
        )
        cb_launch.pack(anchor="w", pady=20)

        self.step_frames.append(s3)

        # Bottom Action Bar
        bottom_bar = tk.Frame(self.root, bg="#0B1120", height=50)
        bottom_bar.pack(fill="x", side="bottom")
        bottom_bar.pack_propagate(False)

        self.btn_cancel = tk.Button(
            bottom_bar,
            text="Отмена",
            command=self.root.destroy,
            font=("Segoe UI", 9),
            bg="#334155",
            fg=self.text_white,
            activebackground="#475569",
            activeforeground="white",
            relief="flat",
            padx=15,
        )
        self.btn_cancel.pack(side="left", padx=20, pady=10)

        self.btn_next = tk.Button(
            bottom_bar,
            text="Далее >",
            command=self._next_step,
            font=("Segoe UI", 9, "bold"),
            bg=self.accent_green,
            fg="white",
            activebackground=self.accent_lightgreen,
            activeforeground="white",
            relief="flat",
            padx=20,
        )
        self.btn_next.pack(side="right", padx=20, pady=10)

    def _browse_dir(self):
        chosen = filedialog.askdirectory(initialdir=self.install_dir.get())
        if chosen:
            self.install_dir.set(str(Path(chosen) / "SmartVision_AZS"))

    def _show_step(self, step_idx):
        for idx, f in enumerate(self.step_frames):
            if idx == step_idx:
                f.pack(fill="both", expand=True)
            else:
                f.pack_forget()
        self.current_step = step_idx

        if step_idx == 0:
            self.btn_next.config(text="Далее >", state="normal")
        elif step_idx == 1:
            self.btn_next.config(text="Установить", state="normal")
        elif step_idx == 2:
            self.btn_next.config(state="disabled")
            self.btn_cancel.config(state="disabled")
            threading.Thread(target=self._run_installation, daemon=True).start()
        elif step_idx == 3:
            self.btn_cancel.pack_forget()
            self.btn_next.config(text="Завершить", state="normal", command=self._finish)

    def _next_step(self):
        if self.current_step < len(self.step_frames) - 1:
            self._show_step(self.current_step + 1)

    def _create_shortcut(self, target_path: Path, shortcut_path: Path, icon_path: Path, description: str):
        """Create Windows shortcut (.lnk) using PowerShell WScript.Shell."""
        try:
            ps_cmd = (
                f'$ws = New-Object -ComObject WScript.Shell; '
                f'$s = $ws.CreateShortcut("{shortcut_path}"); '
                f'$s.TargetPath = "{target_path}"; '
                f'$s.WorkingDirectory = "{target_path.parent}"; '
                f'$s.Description = "{description}"; '
                f'$s.IconLocation = "{icon_path},0"; '
                f'$s.Save()'
            )
            subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, check=False)
        except Exception:
            pass

    def _run_installation(self):
        target_dir = Path(self.install_dir.get())
        try:
            self.progress_lbl.config(text="Создание директории установки...")
            self.progress_bar["value"] = 10
            target_dir.mkdir(parents=True, exist_ok=True)

            # Source directory (bundle or local workspace)
            base_dir = Path(__file__).resolve().parent.parent
            include_dirs = ["api", "core", "database", "static", "tools", "vision"]
            include_files = [
                "desktop_app.py",
                "main.py",
                "config.py",
                "requirements.txt",
                "desktop_icon.ico",
                "README.md",
            ]

            total_items = len(include_dirs) + len(include_files)
            done = 0

            for d in include_dirs:
                src_d = base_dir / d
                dst_d = target_dir / d
                if src_d.exists():
                    self.progress_lbl.config(text=f"Копирование модуля {d}...")
                    if dst_d.exists():
                        shutil.rmtree(dst_d)
                    shutil.copytree(src_d, dst_d, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
                done += 1
                self.progress_bar["value"] = 10 + int((done / total_items) * 60)

            for f in include_files:
                src_f = base_dir / f
                dst_f = target_dir / f
                if src_f.exists():
                    self.progress_lbl.config(text=f"Копирование файла {f}...")
                    shutil.copy2(src_f, dst_f)
                done += 1
                self.progress_bar["value"] = 10 + int((done / total_items) * 60)

            # Create Launcher Batch
            bat_path = target_dir / "SmartVision_AZS_Launcher.bat"
            with open(bat_path, "w", encoding="cp1251") as bf:
                bf.write(f"@echo off\ncd /d \"{target_dir}\"\npython desktop_app.py\n")

            icon_path = target_dir / "desktop_icon.ico"

            # Shortcuts
            self.progress_lbl.config(text="Создание ярлыков Windows...")
            self.progress_bar["value"] = 85

            if self.create_desktop_shortcut.get():
                desktop = Path(os.environ.get("USERPROFILE", "C:")) / "Desktop"
                if desktop.exists():
                    lnk = desktop / "SmartVision AZS (Белоруснефть).lnk"
                    self._create_shortcut(bat_path, lnk, icon_path, f"{APP_NAME} — {APP_VENDOR}")

            if self.create_start_menu.get():
                start_menu = Path(os.environ.get("APPDATA", "C:")) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
                if start_menu.exists():
                    lnk = start_menu / "SmartVision AZS.lnk"
                    self._create_shortcut(bat_path, lnk, icon_path, f"{APP_NAME} — {APP_VENDOR}")

            self.progress_bar["value"] = 100
            self.progress_lbl.config(text="Завершено.")
            self.root.after(500, lambda: self._show_step(3))

        except Exception as e:
            messagebox.showerror("Ошибка установки", f"Не удалось выполнить установку:\n{e}")
            self.root.destroy()

    def _finish(self):
        if self.launch_after.get():
            target_dir = Path(self.install_dir.get())
            bat_path = target_dir / "SmartVision_AZS_Launcher.bat"
            if bat_path.exists():
                subprocess.Popen(["cmd.exe", "/c", str(bat_path)], cwd=str(target_dir), creationflags=subprocess.CREATE_NEW_CONSOLE)
        self.root.destroy()


def main():
    root = tk.Tk()
    app = InstallerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
