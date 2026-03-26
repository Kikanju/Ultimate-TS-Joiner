import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import re
from datetime import datetime

class UltimateJoiner:
    def __init__(self, root):
        self.root = root
        self.root.title("Ultimate Batch TS Joiner")
        self.root.geometry("650x850")
        
        self.queue = []
        self.is_running = False

        # --- 1. Queue Section ---
        queue_frame = tk.LabelFrame(root, text=" 1. Folders Queue ", padx=10, pady=10)
        queue_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        btn_box = tk.Frame(queue_frame)
        btn_box.pack(fill="x", pady=5)
        tk.Button(btn_box, text="+ Add Folder", command=self.add_to_queue, bg="#e3f2fd").pack(side="left", padx=5)
        tk.Button(btn_box, text="Clear All", command=self.clear_queue).pack(side="right")

        self.queue_listbox = tk.Listbox(queue_frame, font=("Arial", 9), height=6)
        self.queue_listbox.pack(fill="both", expand=True)

        # --- 2. Encoding Settings ---
        set_frame = tk.LabelFrame(root, text=" 2. Encoding Settings ", padx=10, pady=10)
        set_frame.pack(fill="x", padx=15, pady=5)
        
        # Codec Toggle
        tk.Label(set_frame, text="Video Format:").grid(row=0, column=0, sticky="w")
        self.codec_var = tk.StringVar(value="H.264 (Faster)")
        codec_menu = ttk.Combobox(set_frame, textvariable=self.codec_var, values=["H.264 (Faster)", "H.265 (Smaller)"], state="readonly")
        codec_menu.grid(row=0, column=1, padx=10, sticky="ew")

        # Hardware Toggle
        tk.Label(set_frame, text="Hardware Accel:").grid(row=1, column=0, sticky="w", pady=5)
        self.hw_var = tk.StringVar(value="None (CPU)")
        hw_menu = ttk.Combobox(set_frame, textvariable=self.hw_var, values=["None (CPU)", "NVIDIA (NVENC)", "AMD (AMF)", "Intel (QSV)"], state="readonly")
        hw_menu.grid(row=1, column=1, padx=10, sticky="ew")

        # Gap Detection
        tk.Label(set_frame, text="Gap Split (Mins):").grid(row=2, column=0, sticky="w")
        self.gap_var = tk.IntVar(value=15)
        tk.Scale(set_frame, from_=1, to=120, orient="horizontal", variable=self.gap_var).grid(row=2, column=1, sticky="ew")

        # --- 3. Progress & Logging ---
        prog_frame = tk.LabelFrame(root, text=" 3. Live Status ", padx=10, pady=10)
        prog_frame.pack(fill="x", padx=15, pady=5)
        
        self.current_op = tk.Label(prog_frame, text="Status: Ready", fg="blue", font=("Arial", 9, "bold"))
        self.current_op.pack(anchor="w")
        
        self.progress_val = tk.DoubleVar()
        ttk.Progressbar(prog_frame, variable=self.progress_val, maximum=100).pack(fill="x", pady=5)

        # --- 4. Controls ---
        ctrl = tk.Frame(root, pady=10)
        ctrl.pack(fill="x", padx=15)
        
        self.shutdown_var = tk.BooleanVar()
        tk.Checkbutton(ctrl, text="Shutdown PC on Finish", variable=self.shutdown_var).pack(side="left")
        
        tk.Button(ctrl, text="DRY RUN (Space Check)", command=self.dry_run, bg="#fbc02d").pack(side="right", padx=5)
        self.btn_start = tk.Button(root, text="START ALL JOBS", bg="#1b5e20", fg="white", font=("Arial", 12, "bold"), pady=15, command=self.start_batch)
        self.btn_start.pack(fill="x", padx=15, pady=10)

    def add_to_queue(self):
        folder = filedialog.askdirectory()
        if folder:
            self.queue.append(folder)
            self.queue_listbox.insert(tk.END, folder)

    def clear_queue(self):
        self.queue = []
        self.queue_listbox.delete(0, tk.END)

    def dry_run(self):
        if not self.queue: return
        total_ts_size = 0
        for folder in self.queue:
            for f in os.listdir(folder):
                if f.lower().endswith('.ts'):
                    total_ts_size += os.path.getsize(os.path.join(folder, f))
        
        size_gb = total_ts_size / (1024**3)
        messagebox.showinfo("Dry Run Report", f"Total Original Size: {size_gb:.2f} GB\nEstimated Output: ~{size_gb*0.6:.2f} GB\nEnsure destination drives have enough space!")

    def start_batch(self):
        if not self.queue or self.is_running: return
        self.is_running = True
        self.btn_start.config(state="disabled")
        threading.Thread(target=self.process_queue, daemon=True).start()

    def process_queue(self):
        # Determine Codec
        v_codec = "libx264" if "H.264" in self.codec_var.get() else "libx265"
        
        # Override with Hardware Accel if selected
        hw = self.hw_var.get()
        if hw != "None (CPU)":
            prefix = "h264_" if "H.264" in self.codec_var.get() else "hevc_"
            suffix = {"NVIDIA (NVENC)": "nvenc", "AMD (AMF)": "amf", "Intel (QSV)": "qsv"}
            v_codec = prefix + suffix[hw]

        log_path = "conversion_log.txt"
        
        with open(log_path, "a") as log:
            log.write(f"\n--- Batch Started: {datetime.now()} ---\n")

            while self.queue:
                folder = self.queue[0]
                folder_name = os.path.basename(folder)
                self.root.after(0, lambda: self.current_op.config(text=f"Processing Folder: {folder_name}"))

                try:
                    # 1. Group Files (Gap Detection)
                    groups = self.get_groups(folder)
                    for i, group in enumerate(groups):
                        out_name = f"{folder_name}_Part{i+1}.mp4"
                        out_path = os.path.join(folder, out_name)
                        
                        # 2. Run FFmpeg
                        list_p = os.path.join(folder, f"list_{i}.txt")
                        with open(list_p, "w") as f:
                            for s in group: f.write(f"file '{s.replace('\\','/')}'\n")

                        cmd = ['ffmpeg', '-f', 'concat', '-safe', '0', '-i', list_p, '-c:v', v_codec, '-crf', '23', '-c:a', 'copy', out_path, '-y']
                        process = subprocess.run(cmd, creationflags=subprocess.CREATE_NO_WINDOW)
                        
                        if os.path.exists(list_p): os.remove(list_p)
                        if process.returncode != 0:
                            raise Exception(f"FFmpeg failed on {out_name}")

                    log.write(f"SUCCESS: {folder}\n")
                except Exception as e:
                    log.write(f"FAILED: {folder} | Error: {str(e)}\n")

                self.queue.pop(0)
                self.root.after(0, lambda: self.queue_listbox.delete(0))

        self.root.after(0, self.finish_all)

    def get_groups(self, folder):
        files = sorted([os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith('.ts')],
                       key=lambda x: os.path.getctime(x))
        if not files: return []
        groups, current = [], [files[0]]
        gap = self.gap_var.get() * 60
        for i in range(1, len(files)):
            if (os.path.getctime(files[i]) - os.path.getctime(files[i-1])) > gap:
                groups.append(current); current = [files[i]]
            else: current.append(files[i])
        groups.append(current)
        return groups

    def finish_all(self):
        self.is_running = False
        self.btn_start.config(state="normal")
        if self.shutdown_var.get(): os.system("shutdown /s /t 60")
        messagebox.showinfo("Done", "Batch complete! Check conversion_log.txt for details.")

if __name__ == "__main__":
    root = tk.Tk()
    UltimateJoiner(root)
    root.mainloop()