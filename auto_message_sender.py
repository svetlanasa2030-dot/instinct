import tkinter as tk
from tkinter import ttk, messagebox
import threading, time
import pyautogui
import pyperclip

pyautogui.PAUSE = 0.08

class AutoMessageApp:
    def __init__(self, root):
        self.root=root; self.root.title("Auto Message Sender"); self.root.geometry("820x600")
        self.running=False; self.target=None; self.rows=[]; self.next_send=[]
        self.build_ui(); self.root.bind("<F8>",lambda e:self.stop()); self.root.protocol("WM_DELETE_WINDOW",self.close)

    def build_ui(self):
        main=ttk.Frame(self.root,padding=14); main.pack(fill="both",expand=True)
        ttk.Label(main,text="Автоматическая отправка сообщений",font=("Segoe UI",16,"bold")).pack(anchor="w")
        ttk.Label(main,text="При запуске каждое сообщение отправляется сразу. Затем каждое повторяется строго через заданный ему интервал.",wraplength=780).pack(anchor="w",pady=(5,12))
        f=ttk.LabelFrame(main,text="1. Точка ввода"); f.pack(fill="x",pady=(0,12))
        self.target_label=ttk.Label(f,text="Точка не выбрана"); self.target_label.pack(side="left",padx=10,pady=10)
        ttk.Button(f,text="Выбрать точку мышкой",command=self.select_target).pack(side="right",padx=10,pady=8)
        f=ttk.LabelFrame(main,text="2. Сообщения и интервалы"); f.pack(fill="both",expand=True)
        h=ttk.Frame(f); h.pack(fill="x",padx=8,pady=(8,2))
        ttk.Label(h,text="Сообщение",width=42).pack(side="left")
        ttk.Label(h,text="Интервал (мин.)",width=13).pack(side="left")
        ttk.Label(h,text="До отправки",width=15).pack(side="left")
        self.rows_frame=ttk.Frame(f); self.rows_frame.pack(fill="both",expand=True,padx=8)
        self.add_row("Сообщение 1",48); self.add_row("Сообщение 2",78); self.add_row("Сообщение 3",98)
        c=ttk.Frame(main); c.pack(fill="x",pady=(12,0))
        ttk.Button(c,text="+ Добавить сообщение",command=lambda:self.add_row("",60)).pack(side="left")
        self.start_btn=ttk.Button(c,text="▶ Запустить",command=self.start); self.start_btn.pack(side="right",padx=(8,0))
        self.stop_btn=ttk.Button(c,text="■ Остановить",command=self.stop,state="disabled"); self.stop_btn.pack(side="right")
        self.status=ttk.Label(main,text="Готово"); self.status.pack(anchor="w",pady=(8,0))
        self.global_timer=ttk.Label(main,text="Таймер до ближайшей отправки: —",font=("Segoe UI",10,"bold")); self.global_timer.pack(anchor="w")
        ttk.Label(main,text="F8 — остановить",foreground="gray").pack(anchor="w")

    def add_row(self,message="",minutes=60):
        row=ttk.Frame(self.rows_frame); row.pack(fill="x",pady=4)
        mv=tk.StringVar(value=message); iv=tk.StringVar(value=str(minutes)); tv=tk.StringVar(value="—")
        ttk.Entry(row,textvariable=mv,width=42).pack(side="left",padx=(0,8))
        ttk.Entry(row,textvariable=iv,width=13).pack(side="left",padx=(0,8))
        ttk.Label(row,textvariable=tv,width=15).pack(side="left",padx=(0,8))
        ttk.Button(row,text="Удалить",width=8,command=lambda:self.remove_row(row)).pack(side="left")
        self.rows.append((row,mv,iv,tv))

    def remove_row(self,row):
        if self.running:return
        for item in self.rows[:]:
            if item[0]==row: row.destroy(); self.rows.remove(item); break

    def select_target(self):
        self.status.config(text="Кликните в нужную точку...")
        overlay=tk.Toplevel(self.root); overlay.attributes("-fullscreen",True); overlay.attributes("-alpha",0.25); overlay.configure(bg="black"); overlay.attributes("-topmost",True)
        tk.Label(overlay,text="КЛИКНИТЕ В ТОЧКУ ВВОДА\nEsc — отмена",font=("Segoe UI",24,"bold"),fg="white",bg="black").pack(expand=True)
        def choose(e):
            self.target=(e.x,e.y); self.target_label.config(text=f"Выбрана точка: X={e.x}, Y={e.y}"); self.status.config(text="Точка выбрана"); overlay.destroy()
        overlay.bind("<Button-1>",choose); overlay.bind("<Escape>",lambda e:overlay.destroy()); overlay.focus_force()

    def get_config(self):
        result=[]
        for _,mv,iv,_ in self.rows:
            msg=mv.get().strip()
            if not msg: continue
            try:
                minutes=float(iv.get().replace(",",".")); assert minutes>0
            except Exception: raise ValueError(f"Некорректный интервал для: {msg}")
            result.append((msg,minutes*60))
        if not result: raise ValueError("Добавьте хотя бы одно сообщение.")
        if not self.target: raise ValueError("Сначала выберите точку мышкой.")
        return result

    def start(self):
        try: config=self.get_config()
        except ValueError as e: messagebox.showerror("Ошибка",str(e)); return
        self.running=True; self.start_btn.config(state="disabled"); self.stop_btn.config(state="normal"); self.status.config(text="Запущено")
        # Первичная отправка всех сообщений происходит сразу при запуске.
        self.next_send=[time.monotonic() for _ in config]
        threading.Thread(target=self.worker,args=(config,),daemon=True).start()

    def stop(self):
        self.running=False; self.start_btn.config(state="normal"); self.stop_btn.config(state="disabled"); self.status.config(text="Остановлено"); self.global_timer.config(text="Таймер до ближайшей отправки: —")
        for _,_,_,tv in self.rows: tv.set("—")

    def send_message(self,message):
        x,y=self.target
        pyautogui.click(x,y); time.sleep(0.15)
        pyperclip.copy(message)
        pyautogui.hotkey("ctrl","v"); time.sleep(0.12); pyautogui.press("enter")

    @staticmethod
    def fmt(sec):
        sec=max(0,int(sec)); h,rem=divmod(sec,3600); m,s=divmod(rem,60)
        return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

    def update_timers(self):
        if not self.running:return
        now=time.monotonic(); left=[]
        for i,(_,_,_,tv) in enumerate(self.rows):
            if i<len(self.next_send):
                v=max(0,self.next_send[i]-now); tv.set(self.fmt(v)); left.append(v)
        if left:self.global_timer.config(text=f"Таймер до ближайшей отправки: {self.fmt(min(left))}")
        self.root.after(500,self.update_timers)

    def worker(self,config):
        # Отправляем каждое сообщение один раз сразу, затем планируем повторение.
        for i,(message,interval) in enumerate(config):
            if not self.running: return
            try:self.send_message(message)
            except Exception as e:
                self.root.after(0,lambda err=str(e):messagebox.showerror("Ошибка",err)); self.root.after(0,self.stop); return
            self.next_send[i]=time.monotonic()+interval
        self.root.after(0,self.update_timers)
        while self.running:
            now=time.monotonic()
            for i,(message,interval) in enumerate(config):
                if now>=self.next_send[i]:
                    try:self.send_message(message); self.next_send[i]=time.monotonic()+interval
                    except Exception as e:
                        self.root.after(0,lambda err=str(e):messagebox.showerror("Ошибка",err)); self.root.after(0,self.stop); return
            time.sleep(0.2)

    def close(self):
        self.running=False; self.root.destroy()

if __name__=="__main__":
    root=tk.Tk(); app=AutoMessageApp(root); root.mainloop()
