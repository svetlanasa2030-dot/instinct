import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import pyautogui
import pyperclip

pyautogui.PAUSE = 0.08

class AutoMessageApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Auto Message Sender")
        self.root.geometry("720x520")
        self.root.resizable(False, False)
        self.running = False
        self.target = None
        self.rows = []
        self.build_ui()

    def build_ui(self):
        main = ttk.Frame(self.root, padding=14)
        main.pack(fill="both", expand=True)
        ttk.Label(main, text="Автоматическая отправка сообщений", font=("Segoe UI", 16, "bold")).pack(anchor="w")
        ttk.Label(main, text="Выберите точку ввода/чата, добавьте сообщения и задайте интервал для каждого.", wraplength=680).pack(anchor="w", pady=(5, 12))

        target_frame = ttk.LabelFrame(main, text="1. Область ввода")
        target_frame.pack(fill="x", pady=(0, 12))
        self.target_label = ttk.Label(target_frame, text="Точка не выбрана")
        self.target_label.pack(side="left", padx=10, pady=10)
        ttk.Button(target_frame, text="Выбрать точку мышкой", command=self.select_target).pack(side="right", padx=10, pady=8)

        msg_frame = ttk.LabelFrame(main, text="2. Сообщения и интервалы")
        msg_frame.pack(fill="both", expand=True)
        header = ttk.Frame(msg_frame)
        header.pack(fill="x", padx=8, pady=(8, 2))
        ttk.Label(header, text="Сообщение", width=48).pack(side="left")
        ttk.Label(header, text="Интервал (мин.)", width=16).pack(side="left")
        ttk.Label(header, text="", width=8).pack(side="left")
        self.rows_frame = ttk.Frame(msg_frame)
        self.rows_frame.pack(fill="both", expand=True, padx=8)
        self.add_row("Сообщение 1", 48)
        self.add_row("Сообщение 2", 78)
        self.add_row("Сообщение 3", 98)

        buttons = ttk.Frame(main)
        buttons.pack(fill="x", pady=(12, 0))
        ttk.Button(buttons, text="+ Добавить сообщение", command=lambda: self.add_row("", 60)).pack(side="left")
        self.start_btn = ttk.Button(buttons, text="▶ Запустить", command=self.start)
        self.start_btn.pack(side="right", padx=(8, 0))
        self.stop_btn = ttk.Button(buttons, text="■ Остановить", command=self.stop, state="disabled")
        self.stop_btn.pack(side="right")
        self.status = ttk.Label(main, text="Готово", foreground="gray")
        self.status.pack(anchor="w", pady=(8, 0))
        ttk.Label(main, text="После запуска можно нажать F8 для остановки.", foreground="gray").pack(anchor="w")
        self.root.bind("<F8>", lambda e: self.stop())

    def add_row(self, message="", minutes=60):
        row = ttk.Frame(self.rows_frame)
        row.pack(fill="x", pady=4)
        msg_var = tk.StringVar(value=message)
        min_var = tk.StringVar(value=str(minutes))
        ttk.Entry(row, textvariable=msg_var, width=55).pack(side="left", padx=(0, 8))
        ttk.Entry(row, textvariable=min_var, width=14).pack(side="left", padx=(0, 8))
        ttk.Button(row, text="Удалить", width=8, command=lambda r=row: self.remove_row(r)).pack(side="left")
        self.rows.append((row, msg_var, min_var))

    def remove_row(self, row):
        for item in self.rows[:]:
            if item[0] == row:
                row.destroy()
                self.rows.remove(item)
                break

    def select_target(self):
        self.status.config(text="Кликните в нужное место...")
        self.root.update()
        overlay = tk.Toplevel(self.root)
        overlay.attributes("-fullscreen", True)
        overlay.attributes("-alpha", 0.25)
        overlay.configure(bg="black")
        overlay.attributes("-topmost", True)
        label = tk.Label(overlay, text="КЛИКНИТЕ В ТОЧКУ ВВОДА", font=("Segoe UI", 24, "bold"), fg="white", bg="black")
        label.pack(expand=True)

        def choose(event):
            self.target = (event.x, event.y)
            self.target_label.config(text=f"Выбрана точка: X={event.x}, Y={event.y}")
            self.status.config(text="Точка выбрана")
            overlay.destroy()

        overlay.bind("<Button-1>", choose)
        overlay.bind("<Escape>", lambda e: overlay.destroy())
        overlay.focus_force()

    def get_config(self):
        result = []
        for _, msg_var, min_var in self.rows:
            msg = msg_var.get().strip()
            if not msg:
                continue
            try:
                minutes = float(min_var.get().replace(",", "."))
                if minutes <= 0:
                    raise ValueError
            except ValueError:
                raise ValueError(f"Некорректный интервал для сообщения: {msg}")
            result.append((msg, minutes * 60))
        if not result:
            raise ValueError("Добавьте хотя бы одно сообщение.")
        if not self.target:
            raise ValueError("Сначала выберите точку мышкой.")
        return result

    def start(self):
        try:
            config = self.get_config()
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e))
            return
        self.running = True
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.status.config(text="Запущено")
        threading.Thread(target=self.worker, args=(config,), daemon=True).start()

    def stop(self):
        self.running = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.status.config(text="Остановлено")

    def send_message(self, message):
        x, y = self.target
        pyautogui.click(x, y)
        time.sleep(0.15)
        old_clipboard = None
        try:
            old_clipboard = pyperclip.paste()
        except Exception:
            pass
        pyperclip.copy(message)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.1)
        pyautogui.press("enter")
        if old_clipboard is not None:
            try:
                pyperclip.copy(old_clipboard)
            except Exception:
                pass

    def worker(self, config):
        next_send = [time.monotonic() + interval for _, interval in config]
        while self.running:
            now = time.monotonic()
            for i, (message, interval) in enumerate(config):
                if now >= next_send[i]:
                    try:
                        self.send_message(message)
                        next_send[i] += interval
                    except Exception as e:
                        self.root.after(0, lambda err=str(e): messagebox.showerror("Ошибка", err))
                        self.root.after(0, self.stop)
                        return
            time.sleep(0.25)

if __name__ == "__main__":
    root = tk.Tk()
    app = AutoMessageApp(root)
    root.mainloop()
