import subprocess
import customtkinter as ctk
import tkinter as tk
from PIL import Image, ImageTk
import requests
import io
import os
import threading
import yt_dlp
import re
from CTkMessagebox import CTkMessagebox
from functools import lru_cache
import concurrent.futures

class GifSelectorFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.selected_gif_url = None
        self.gif_frames = []
        self.preview_cache = {}
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
        self.animation_frames = {}
        self.current_frame = {}
        
    def fetch_image(self, url):
        response = requests.get(url)
        return response.content
        
    def update_gif_frame(self, label, frames, frame_index=0):
        if label.winfo_exists():
            current_frame = frames[frame_index]
            photo = ctk.CTkImage(light_image=current_frame, dark_image=current_frame, size=(150, 150))
            label.configure(image=photo)
            label.image = photo
            
            next_frame = (frame_index + 1) % len(frames)
            label.after(50, lambda: self.update_gif_frame(label, frames, next_frame))

    def load_preview(self, preview_url, label):
        try:
            img_data = self.fetch_image(preview_url)
            gif = Image.open(io.BytesIO(img_data))
            
            frames = []
            for frame in range(0, gif.n_frames):
                gif.seek(frame)
                frame_image = gif.copy().resize((150, 150), Image.Resampling.LANCZOS)
                frames.append(frame_image)
            
            self.animation_frames[label] = frames
            self.update_gif_frame(label, frames)
            
        except Exception as e:
            print(f"Error loading preview: {e}")





    def load_gifs(self, search_query):
        for frame in self.gif_frames:
            frame.destroy()
        self.gif_frames.clear()
        
        TENOR_API_KEY = ''
        params = {
            'q': search_query,
            'key': TENOR_API_KEY,
            'limit': 30,
            'media_filter': 'minimal',
            'contentfilter': 'high'
        }
        
        response = requests.get('https://tenor.googleapis.com/v2/search', params=params)
        data = response.json()
        
        row = 0
        col = 0
        max_cols = 3
        
        for result in data['results']:
            gif_url = result['media_formats']['gif']['url']
            preview_url = result['media_formats']['tinygif']['url']
            
            gif_frame = ctk.CTkFrame(self)
            gif_frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            
            label = ctk.CTkLabel(gif_frame, text="", width=150, height=150)
            label.pack(padx=5, pady=5)
            
            # Load preview in separate thread
            self.executor.submit(self.load_preview, preview_url, label)
            
            btn = ctk.CTkButton(
                gif_frame,
                text="Select",
                command=lambda url=gif_url: self.select_gif(url)
            )
            btn.pack(padx=5, pady=5)
            
            self.gif_frames.append(gif_frame)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    def select_gif(self, url):
        self.selected_gif_url = url
        CTkMessagebox(title="Success", message="GIF selected successfully!")


class VideoProcessor(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Video Creator")
        self.geometry("900x800")
        
        self.main_container = ctk.CTkFrame(self)
        self.main_container.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Left panel setup
        self.setup_left_panel()
        
        # Right panel setup
        self.setup_right_panel()
    def open_outputs_folder(self):
        outputs_path = os.path.abspath("outputs")
        if not os.path.exists(outputs_path):
            os.makedirs(outputs_path)
            
        if os.name == 'nt':  # Windows
            os.startfile(outputs_path)
        else:  # macOS and Linux
            subprocess.run(['xdg-open' if os.name == 'posix' else 'open', outputs_path])
        
    def setup_left_panel(self):
        self.left_panel = ctk.CTkFrame(self.main_container)
        self.left_panel.pack(side="left", fill="y", padx=5, pady=5)
        
        # URL input
        self.url_label = ctk.CTkLabel(self.left_panel, text="YouTube URL:")
        self.url_label.pack(padx=5, pady=5)
        self.url_entry = ctk.CTkEntry(self.left_panel, width=300)
        self.url_entry.pack(padx=5, pady=5)
        
        # GIF search
        self.setup_gif_search()
        
        # Speed options
        self.setup_speed_options()
        
        # Create video button
        self.create_button = ctk.CTkButton(
            self.left_panel,
            text="Create Video",
            command=self.create_video
        )
        self.create_button.pack(padx=5, pady=20)
        self.open_outputs_button = ctk.CTkButton(
        self.left_panel,
        text="Open Outputs Folder",
        command=self.open_outputs_folder
        )
        self.open_outputs_button.pack(padx=5, pady=5)
        
    def setup_right_panel(self):
        self.right_panel = ctk.CTkFrame(self.main_container)
        self.right_panel.pack(side="right", expand=True, fill="both", padx=5, pady=5)
        
        self.gif_selector = GifSelectorFrame(self.right_panel, width=800, height=400)
        self.gif_selector.pack(expand=True, fill="both", padx=5, pady=5)
        

        
    def setup_gif_search(self):
        self.gif_search_label = ctk.CTkLabel(self.left_panel, text="Search GIFs:")
        self.gif_search_label.pack(padx=5, pady=5)
        self.gif_search_entry = ctk.CTkEntry(self.left_panel, width=300)
        self.gif_search_entry.pack(padx=5, pady=5)
        self.search_button = ctk.CTkButton(
            self.left_panel,
            text="Search GIFs",
            command=self.search_gifs
        )
        self.search_button.pack(padx=5, pady=5)
        
    def setup_speed_options(self):
        self.speed_var = tk.StringVar(value="0")
        self.speed_label = ctk.CTkLabel(self.left_panel, text="Audio Speed:")
        self.speed_label.pack(padx=5, pady=5)
        self.speed_up = ctk.CTkRadioButton(
            self.left_panel,
            text="Speed Up",
            variable=self.speed_var,
            value="0"
        )
        self.speed_up.pack(padx=5, pady=2)
        self.slow_down = ctk.CTkRadioButton(
            self.left_panel,
            text="Slow Down",
            variable=self.speed_var,
            value="1"
        )
        self.slow_down.pack(padx=5, pady=2)
        
    def search_gifs(self):
        search_query = self.gif_search_entry.get()
        if search_query:
            self.gif_selector.load_gifs(search_query)
            
    def create_video(self):
        if not self.validate_inputs():
            return
            
        self.setup_progress_window()
        threading.Thread(target=self.process_video, daemon=True).start()
        
    def validate_inputs(self):
        if not self.url_entry.get():
            CTkMessagebox(title="Error", message="Please enter a YouTube URL")
            return False
        if not self.gif_selector.selected_gif_url:
            CTkMessagebox(title="Error", message="Please select a GIF first")
            return False
        return True
        
    def setup_progress_window(self):
        self.progress_window = ctk.CTkToplevel(self)
        self.progress_window.title("Processing")
        self.progress_window.geometry("300x150")
        
        self.progress_label = ctk.CTkLabel(self.progress_window, text="Processing video...")
        self.progress_label.pack(pady=20)
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_window)
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(0)
        
    def process_video(self):
        try:
            self.download_and_process()
        except Exception as e:
            CTkMessagebox(title="Error", message=f"Error creating video: {str(e)}")
        finally:
            self.progress_window.destroy()
            
    def download_and_process(self):
        # Initialize filenames
        video_filename = "video.mp4"
        audio_filename = "audio.mp3"
        gif_filename = "background.gif"
        
        # Download selected GIF
        self.progress_label.configure(text="Downloading GIF...")
        self.progress_bar.set(0.1)
        gif_data = requests.get(self.gif_selector.selected_gif_url).content
        with open(gif_filename, 'wb') as f:
            f.write(gif_data)
        
        # Get video info and create output filename
        video_url = self.url_entry.get()
        self.progress_label.configure(text="Getting video info...")
        self.progress_bar.set(0.2)
        video_info = yt_dlp.YoutubeDL().extract_info(video_url, download=False)
        video_title = re.sub(r'[\\/:*?"<>|]', '', video_info['title'].replace(" ", "_"))
        output_video = f"{video_title}.mp4"
        
        # Download YouTube video
        self.progress_label.configure(text="Downloading video...")
        self.progress_bar.set(0.3)
        ydl_opts = {
            'outtmpl': video_filename,
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        
        # Extract and process audio
        self.progress_label.configure(text="Processing audio...")
        self.progress_bar.set(0.5)
        pitch = 0.9 if self.speed_var.get() == "1" else 1.4
        command = f'ffmpeg -i "{video_filename}" -vn -af "asetrate=44100*{pitch},aresample=44100" -acodec libmp3lame "{audio_filename}"'
        os.system(command)
        
        # Get audio duration
        self.progress_label.configure(text="Preparing final video...")
        self.progress_bar.set(0.7)
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', audio_filename],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        audio_duration = float(result.stdout)
        
        # Create video from GIF
        temp_video = "looped_video.mp4"
        command = f'ffmpeg -stream_loop -1 -i "{gif_filename}" -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" -t {audio_duration} -pix_fmt yuv420p -c:v libx264 -r 30 "{temp_video}"'
        os.system(command)
        
        # Combine video and audio
        self.progress_label.configure(text="Combining video and audio...")
        self.progress_bar.set(0.8)
        command = f'ffmpeg -i "{temp_video}" -i "{audio_filename}" -c:v copy -c:a aac -strict experimental -b:a 192k -shortest "{output_video}"'
        os.system(command)
        
        # Clean up temporary files
        self.progress_label.configure(text="Cleaning up...")
        self.progress_bar.set(0.9)
        os.remove(video_filename)
        os.remove(audio_filename)
        os.remove(gif_filename)
        os.remove(temp_video)
        
        # Move to outputs folder
        if not os.path.exists("outputs"):
            os.makedirs("outputs")
        output_path = os.path.join("outputs", output_video)
        os.rename(output_video, output_path)
        
        self.progress_bar.set(1.0)
        self.progress_label.configure(text="Complete!")
        

        
        CTkMessagebox(title="Success", message="Video created successfully!")

if __name__ == "__main__":
    app = VideoProcessor()
    app.mainloop()
