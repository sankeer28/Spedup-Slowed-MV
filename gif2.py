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
import time

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
        self.api_key = tk.StringVar(value="")  # Default key
        
        # Add GIF search UI at the top
        self.setup_gif_search()
        
        # Create a container for the GIF grid that's separate from the search UI
        self.gif_container = ctk.CTkFrame(self, fg_color="transparent")
        self.gif_container.grid(row=1, column=0, sticky="nsew", padx=0, pady=(10, 0))
        self.gif_container.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Try to load API key from cache
        self.load_api_key()
        
    def load_api_key(self):
        """Try to load saved API key from cache file"""
        try:
            if os.path.exists("tenor_api.key"):
                with open("tenor_api.key", "r") as f:
                    key = f.read().strip()
                    if key:
                        self.api_key.set(key)
        except Exception as e:
            print(f"Error loading API key: {e}")
    
    def save_api_key(self, key):
        """Save API key to cache file"""
        try:
            with open("tenor_api.key", "w") as f:
                f.write(key)
        except Exception as e:
            print(f"Error saving API key: {e}")
        
    def setup_gif_search(self):
        search_frame = ctk.CTkFrame(self)
        search_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        search_frame.grid_columnconfigure(1, weight=1)  # Make the entry expand
        
        search_label = ctk.CTkLabel(search_frame, text="Search GIFs:")
        search_label.grid(row=0, column=0, padx=5, pady=5)
        
        self.gif_search_entry = ctk.CTkEntry(search_frame, width=300)
        self.gif_search_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        search_button = ctk.CTkButton(
            search_frame,
            text="Search",
            command=self.search_gifs
        )
        search_button.grid(row=0, column=2, padx=5, pady=5)
        
        # Add API Key input frame
        api_frame = ctk.CTkFrame(self)
        api_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        api_frame.grid_columnconfigure(1, weight=1)
        
        api_label = ctk.CTkLabel(api_frame, text="Tenor API Key:")
        api_label.grid(row=0, column=0, padx=5, pady=5)
        
        self.api_key_entry = ctk.CTkEntry(api_frame, width=300, textvariable=self.api_key)
        self.api_key_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        save_button = ctk.CTkButton(
            api_frame,
            text="Save Key",
            command=lambda: self.save_api_key(self.api_key.get())
        )
        save_button.grid(row=0, column=2, padx=5, pady=5)
        
    def search_gifs(self):
        search_query = self.gif_search_entry.get()
        if search_query:
            self.load_gifs(search_query)
        
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
        # Clear existing GIFs from the container
        for frame in self.gif_frames:
            frame.destroy()
        self.gif_frames.clear()
        
        # Get current API key
        TENOR_API_KEY = self.api_key.get()
        
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
            
            gif_frame = ctk.CTkFrame(self.gif_container)
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
                # Ensure the new row is properly configured
                self.gif_container.grid_rowconfigure(row, weight=0)

    def select_gif(self, url):
        self.selected_gif_url = url
        CTkMessagebox(title="Success", message="GIF selected successfully!")

class ImageSelectorFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.selected_image_url = None
        self.image_frames = []
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
        self.api_choice = tk.StringVar(value="0")
        self.current_page = 1
        self.is_loading = False
        self.preview_cache = {}
        self.last_scroll_time = 0
        self.scroll_debounce_ms = 500  # Increase debounce time to reduce scroll triggers
        
        # Add a flag to track if image preloading should happen
        self.preload_enabled = True
        
        # Batch fetching to avoid too many API calls at once
        self.batch_size = 6  # Fetch images in smaller batches
        
        # Add visual indicator for selected image
        self.selected_frame = None
        
        self.setup_image_sources()
        
    def setup_image_sources(self):
        sources_frame = ctk.CTkFrame(self)
        sources_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        sources_label = ctk.CTkLabel(sources_frame, text="Select Image Source:")
        sources_label.pack(padx=5, pady=5)
        
        # Create a callback command for all radio buttons
        def on_source_change():
            self.clear_images()
            self.current_page = 1
            self.toggle_pexels_visibility()
            if self.api_choice.get() != "3":  # Not Pexels
                self.load_initial_images()
        
        anime_option = ctk.CTkRadioButton(
            sources_frame, 
            text="Anime Wallpaper", 
            variable=self.api_choice,
            value="0",
            command=on_source_change
        )
        anime_option.pack(anchor="w", padx=5, pady=2)
        
        cat_option = ctk.CTkRadioButton(
            sources_frame, 
            text="Cat Wallpaper", 
            variable=self.api_choice,
            value="1",
            command=on_source_change
        )
        cat_option.pack(anchor="w", padx=5, pady=2)
        
        random_option = ctk.CTkRadioButton(
            sources_frame, 
            text="Random Wallpaper", 
            variable=self.api_choice,
            value="2",
            command=on_source_change
        )
        random_option.pack(anchor="w", padx=5, pady=2)
        
        pexels_option = ctk.CTkRadioButton(
            sources_frame, 
            text="Pexels Image", 
            variable=self.api_choice,
            value="3",
            command=on_source_change
        )
        pexels_option.pack(anchor="w", padx=5, pady=2)
        
        # Create Pexels search frame
        self.pexels_frame = ctk.CTkFrame(sources_frame)
        self.pexels_frame.pack(fill="x", padx=5, pady=5)
        
        search_label = ctk.CTkLabel(self.pexels_frame, text="Search Pexels:")
        search_label.pack(side="left", padx=5, pady=5)
        
        self.search_entry = ctk.CTkEntry(self.pexels_frame, width=150)
        self.search_entry.pack(side="left", padx=5, pady=5)
        
        search_button = ctk.CTkButton(
            self.pexels_frame,
            text="Search",
            command=lambda: self.search_pexels(reset_page=True)
        )
        search_button.pack(side="left", padx=5, pady=5)
        
        # Hide Pexels frame initially since default is anime (0)
        self.pexels_frame.pack_forget()
        
        # Create a container for the image grid
        self.image_container = ctk.CTkFrame(self, fg_color="transparent")
        self.image_container.grid(row=1, column=0, sticky="nsew", padx=0, pady=(10, 0))
        self.image_container.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Status label
        self.status_label = ctk.CTkLabel(self, text="")
        self.status_label.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        
        # Loading indicator (initially hidden)
        self.loading_indicator = ctk.CTkLabel(self, text="Loading more images...", fg_color="transparent")
        self.loading_indicator.grid(row=3, column=0, sticky="ew", padx=5, pady=5)
        self.loading_indicator.grid_remove()
        
        # Load initial images
        self.load_initial_images()
        
        # Use after method to set up scroll binding after initialization
        self.after(100, self.setup_scroll_binding)
        
    def setup_scroll_binding(self):
        """Set up scroll event binding after widget is initialized"""
        # Use the canvas's view change command to detect scrolling
        self._parent_canvas.configure(yscrollcommand=self.on_scroll_view_change)
    
    def on_scroll_view_change(self, *args):
        """Handle scroll position changes"""
        # Check if we're near the bottom and should load more
        if self.is_loading:
            return
            
        # Get current time to implement debounce
        current_time = int(time.time() * 1000)
        if (current_time - self.last_scroll_time) < self.scroll_debounce_ms:
            return
            
        # Get scroll position
        try:
            start, end = args
            if float(end) > 0.8:  # If scrolled more than 80% down
                self.last_scroll_time = current_time
                self.load_more_images()
        except Exception:
            pass  # Ignore any parsing errors
    
    def toggle_pexels_visibility(self):
        """Show or hide the Pexels search UI based on current selection"""
        if self.api_choice.get() == "3":
            self.pexels_frame.pack(fill="x", padx=5, pady=5, after=self.winfo_children()[0])
        else:
            self.pexels_frame.pack_forget()
    
    def load_initial_images(self):
        """Load enough images to fill the initial view"""
        # Estimate rows needed based on frame height
        frame_height = self.winfo_height()
        
        # If height is not available yet, use a default
        if frame_height <= 1:
            frame_height = 400  # Default assumption
        
        # Each image row is approximately 230px high (image + padding + button)
        rows_needed = max(2, frame_height // 230)
        images_needed = rows_needed * 3  # 3 images per row
        
        # Load initial batch of images
        self.load_multiple_images(count=images_needed)
        
    def load_more_images(self):
        """Load the next page of images"""
        if self.is_loading:
            return
            
        # Always load more of the current type of images
        current_api_choice = self.api_choice.get()
        
        self.loading_indicator.grid()  # Show loading indicator
        self.current_page += 1
        
        if current_api_choice == "3" and self.search_entry.get():
            self.search_pexels(reset_page=False)
        else:
            self.load_multiple_images(append=True)
    
    def clear_images(self):
        """Clear all images from the container"""
        for frame in self.image_frames:
            frame.destroy()
        self.image_frames.clear()
        
    def fetch_multiple_images(self, api_choice, count=9, page=1, search_query=None):
        """Fetch multiple images from the selected API"""
        images = []
        seen_urls = set()  # Track URLs to avoid duplicates
        
        try:
            if api_choice == "0":  # Anime
                # Try multiple ways to get different anime images
                try_count = 0
                max_attempts = count * 3  # Allow for multiple attempts to get unique images
                
                while len(images) < count and try_count < max_attempts:
                    try_count += 1
                    
                    # Alternate between different anime image sources
                    if try_count % 3 == 0:
                        response = requests.get("https://pic.re/image")
                    elif try_count % 3 == 1:
                        # Try another anime API
                        response = requests.get("https://api.waifu.pics/sfw/waifu")
                        if response.status_code == 200:
                            data = response.json()
                            if 'url' in data:
                                url = data['url']
                                if url not in seen_urls:
                                    seen_urls.add(url)
                                    images.append(url)
                                continue
                    else:
                        # Third option - use a different category
                        response = requests.get("https://api.waifu.pics/sfw/neko")
                        if response.status_code == 200:
                            data = response.json()
                            if 'url' in data:
                                url = data['url']
                                if url not in seen_urls:
                                    seen_urls.add(url)
                                    images.append(url)
                                continue
                    
                    # For pic.re and any fallbacks
                    if response.status_code == 200:
                        url = response.url
                        if url not in seen_urls:
                            seen_urls.add(url)
                            images.append(url)
                            
                    # Small delay to avoid rate limiting
                    time.sleep(0.15)
                    
            elif api_choice == "1":  # Cat
                # The Cat API can return multiple images
                params = {'limit': count, 'page': page - 1}  # Cat API uses 0-based pagination
                response = requests.get("https://api.thecatapi.com/v1/images/search", params=params)
                response.raise_for_status()
                data = response.json()
                for item in data:
                    if 'url' in item:
                        url = item['url']
                        if url not in seen_urls:
                            seen_urls.add(url)
                            images.append(url)
                    
            elif api_choice == "2":  # Random
                # Make multiple calls to get different random images
                for _ in range(count):
                    response = requests.get("https://random.imagecdn.app/v1/image?width=500&height=500&format=json")
                    response.raise_for_status()
                    data = response.json()
                    if 'url' in data:
                        url = data['url']
                        if url not in seen_urls:
                            seen_urls.add(url)
                            images.append(url)
                    # Add small delay between requests to avoid rate limiting
                    time.sleep(0.1)
                    
            elif api_choice == "3" and search_query:  # Pexels
                headers = {
                    'Authorization': '4xnfarO5xIrjF7DfQnn7vx9GIDTxmfic8rYPZqkgzrAVcdGEkpTBfioF'
                }
                params = {
                    'query': search_query,
                    'per_page': count,
                    'page': page
                }
                response = requests.get('https://api.pexels.com/v1/search', headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
                
                if data['photos']:
                    for photo in data['photos']:
                        url = photo['src']['large']
                        if url not in seen_urls:
                            seen_urls.add(url)
                            images.append(url)
            
            return images
            
        except Exception as e:
            print(f"Error fetching images: {e}")
            return images  # Return any images we managed to get before the error
    
    def load_multiple_images(self, count=9, append=False):
        """Load multiple images and display them in a grid"""
        def fetch_and_display(append_images=False):
            self.is_loading = True
            self.status_label.configure(text="Loading images...")
            api_choice = self.api_choice.get()
            
            # Clear existing images if not appending
            if not append_images:
                self.clear_images()
            
            # For non-Pexels options, fetch all images at once to avoid visual loading waves
            if api_choice != "3":
                # For anime specifically, increase the count to ensure we get enough unique images
                actual_count = count * 2 if api_choice == "0" else count
                images = self.fetch_multiple_images(api_choice, count=actual_count, page=self.current_page)
                
                if images:
                    # Just take what we need
                    images = images[:count]
                    self.display_images(images, append_images)
                    self.status_label.configure(text=f"Loaded {len(images)} images")
                else:
                    self.status_label.configure(text="Failed to load images")
            
            self.is_loading = False
            self.loading_indicator.grid_remove()  # Hide loading indicator
        
        threading.Thread(target=fetch_and_display, args=(append,), daemon=True).start()
    
    def search_pexels(self, reset_page=True):
        """Search Pexels API for images"""
        def fetch_and_display_pexels():
            self.is_loading = True
            search_query = self.search_entry.get()
            if not search_query:
                self.status_label.configure(text="Please enter a search term")
                self.is_loading = False
                self.loading_indicator.grid_remove()
                return
            
            # Reset page count if this is a new search
            if reset_page:
                self.current_page = 1
                self.clear_images()
                
            self.status_label.configure(text=f"Searching for '{search_query}'...")
            
            # Calculate how many images to get based on window size for initial load
            count = 9
            if reset_page:
                frame_height = self.winfo_height()
                if frame_height > 1:
                    rows_needed = max(2, frame_height // 230)
                    count = rows_needed * 3
            
            # Fetch in smaller batches to improve scrolling
            images = []
            remaining = count
            while remaining > 0 and self.preload_enabled:
                batch_size = min(self.batch_size, remaining)
                batch = self.fetch_multiple_images("3", count=batch_size, page=self.current_page, 
                                            search_query=search_query)
                
                if batch:
                    images.extend(batch)
                    self.display_images(batch, not reset_page or remaining < count)
                    remaining -= len(batch)
                    # Update progress
                    self.status_label.configure(text=f"Found {len(images)} images for '{search_query}'")
                else:
                    if not images:
                        self.status_label.configure(text="No images found")
                    break
            
            self.is_loading = False
            self.loading_indicator.grid_remove()
        
        threading.Thread(target=fetch_and_display_pexels, daemon=True).start()
    
    def fetch_image_preview(self, url):
        """Fetch and return image data for preview"""
        try:
            response = requests.get(url)
            return response.content
        except Exception as e:
            print(f"Error fetching image preview: {e}")
            return None
    
    def display_images(self, image_urls, append=False):
        """Display images in a grid layout"""
        # Calculate starting position for grid
        start_row = len(self.image_frames) // 3 if append else 0
        
        # First, create all frames and placeholders in the grid at once
        frames_to_load = []
        
        # Place each image in the grid
        for i, url in enumerate(image_urls):
            # Skip if we already have this image (check URL to avoid duplicates)
            if any(url == frame.url for frame in self.image_frames if hasattr(frame, 'url')):
                continue
                
            row = start_row + (i // 3)
            col = i % 3
            
            # Create frame for this image
            image_frame = ctk.CTkFrame(self.image_container)
            image_frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            image_frame.url = url  # Store URL with the frame for reference
            
            # Create placeholder (with fixed size to prevent layout jumping)
            placeholder = ctk.CTkLabel(image_frame, text="", width=150, height=150)
            placeholder.pack(padx=5, pady=5)
            
            # Add loading indicator
            load_indicator = ctk.CTkProgressBar(image_frame, width=100)
            load_indicator.pack(padx=5, pady=0)
            load_indicator.set(0.15)  # Show some initial progress
            
            # Create a closure to capture the correct URL
            def create_command(img_url, frame):
                return lambda: self.select_image(img_url, frame)
                
            # Select button
            select_btn = ctk.CTkButton(
                image_frame,
                text="Select",
                command=create_command(url, image_frame)
            )
            select_btn.pack(padx=5, pady=5)
            
            # Store frame reference
            self.image_frames.append(image_frame)
            frames_to_load.append((url, placeholder, load_indicator))
        
        # Now load all images in parallel instead of sequentially
        for url, placeholder, load_indicator in frames_to_load:
            self.executor.submit(self.load_image_preview, url, placeholder, load_indicator)
        
    def load_image_preview(self, image_url, label, progress=None):
        """Load and display image preview"""
        try:
            # Check if this image is already in cache
            if image_url in self.preview_cache:
                img_data = self.preview_cache[image_url]
                # Skip network request and use cached data
                if progress and progress.winfo_exists():
                    progress.set(0.7)  # Jump ahead in progress
            else:
                # Update progress 
                if progress and progress.winfo_exists():
                    progress.set(0.3)
                    
                # Fetch image
                img_data = self.fetch_image_preview(image_url)
                
                if progress and progress.winfo_exists():
                    progress.set(0.7)
                    
                # Cache the image data
                if img_data:
                    self.preview_cache[image_url] = img_data
            
            if img_data:
                # Use a separate thread for image processing to avoid UI lag
                def process_image():
                    try:
                        img = Image.open(io.BytesIO(img_data))
                        img = img.resize((150, 150), Image.Resampling.LANCZOS)
                        
                        # Create photo image
                        photo = ctk.CTkImage(light_image=img, dark_image=img, size=(150, 150))
                        
                        # Update UI in main thread
                        if label.winfo_exists():
                            label.after(0, lambda: label.configure(image=photo, text=""))
                            label.image = photo  # Keep reference
                            
                        if progress and progress.winfo_exists():
                            progress.after(0, lambda: progress.set(1.0))
                            # Remove progress bar after a short delay
                            progress.after(200, lambda: progress.pack_forget() if progress.winfo_exists() else None)
                    except Exception as e:
                        print(f"Error processing image: {e}")
                        
                # Start image processing in another thread to keep UI responsive  
                threading.Thread(target=process_image, daemon=True).start()
        except Exception as e:
            if label.winfo_exists():
                label.configure(text="Error loading")
            if progress and progress.winfo_exists():
                progress.pack_forget()
    
    def select_image(self, url, frame=None):
        """Select an image by its URL"""
        # Update the selected URL
        self.selected_image_url = url
        
        # If we have the image data cached, store it for faster access
        if url in self.preview_cache:
            self.current_image_data = self.preview_cache[url]
        
        # Visual indication of selected image
        if frame:
            # Remove highlight from previously selected frame
            if self.selected_frame:
                self.selected_frame.configure(border_width=0)
            
            # Highlight the newly selected frame
            frame.configure(border_width=2, border_color="#3a7ebf")
            self.selected_frame = frame
            
        CTkMessagebox(title="Success", message="Image selected successfully!")
        
    def pause_preloading(self):
        """Pause preloading images during scrolling to improve performance"""
        self.preload_enabled = False
        
    def resume_preloading(self):
        """Resume preloading images when scrolling stops"""
        self.preload_enabled = True

class VideoProcessor(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Spedup-Slowed-MV")  # Changed app title
        self.geometry("900x800")
        
        self.main_container = ctk.CTkFrame(self)
        self.main_container.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Check if hardware acceleration is available
        self.has_hw_accel = self.check_nvidia_gpu()
        
        # Left panel setup
        self.setup_left_panel()
        
        # Right panel setup
        self.setup_right_panel()
    
    def check_nvidia_gpu(self):
        """Check if NVIDIA GPU is available for hardware acceleration."""
        try:
            # Check if the NVENC encoder is available
            result = subprocess.run(
                ['ffmpeg', '-hide_banner', '-encoders'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Look for NVIDIA hardware encoders in the output
            if 'h264_nvenc' in result.stdout:
                print("NVIDIA hardware acceleration available")
                return True
            else:
                print("NVIDIA hardware acceleration not detected")
                return False
        except Exception as e:
            print(f"Error checking for hardware acceleration: {e}")
            return False
        
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
        
        # Media type selection
        self.media_type_frame = ctk.CTkFrame(self.left_panel)
        self.media_type_frame.pack(padx=5, pady=5, fill="x")
        
        self.media_type_label = ctk.CTkLabel(self.media_type_frame, text="Background Type:")
        self.media_type_label.pack(padx=5, pady=5)
        
        self.media_type_var = tk.StringVar(value="gif")
        
        self.gif_option = ctk.CTkRadioButton(
            self.media_type_frame,
            text="Animated GIF",
            variable=self.media_type_var,
            value="gif",
            command=self.toggle_media_type
        )
        self.gif_option.pack(padx=5, pady=2)
        
        self.image_option = ctk.CTkRadioButton(
            self.media_type_frame,
            text="Static Image",
            variable=self.media_type_var,
            value="image",
            command=self.toggle_media_type
        )
        self.image_option.pack(padx=5, pady=2)
        
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
        
        # Create tab view for GIF/Image selection
        self.tab_view = ctk.CTkTabview(self.right_panel)
        self.tab_view.pack(expand=True, fill="both", padx=5, pady=5)
        
        # Create tabs
        self.gif_tab = self.tab_view.add("GIF Selection")
        self.image_tab = self.tab_view.add("Image Selection")
        
        # Add GIF selector to GIF tab
        self.gif_selector = GifSelectorFrame(self.gif_tab, width=800, height=400)
        self.gif_selector.pack(expand=True, fill="both", padx=5, pady=5)
        
        # Add Image selector to Image tab
        self.image_selector = ImageSelectorFrame(self.image_tab, width=800, height=400)
        self.image_selector.pack(expand=True, fill="both", padx=5, pady=5)
        
        # Set default tab
        self.tab_view.set("GIF Selection")
        
    def toggle_media_type(self):
        if self.media_type_var.get() == "gif":
            self.tab_view.set("GIF Selection")
        else:
            self.tab_view.set("Image Selection")
        
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
        
    def create_video(self):
        if not self.validate_inputs():
            return
            
        self.setup_progress_window()
        threading.Thread(target=self.process_video, daemon=True).start()
        
    def validate_inputs(self):
        if not self.url_entry.get():
            CTkMessagebox(title="Error", message="Please enter a YouTube URL")
            return False
            
        media_type = self.media_type_var.get()
        if media_type == "gif" and not self.gif_selector.selected_gif_url:
            CTkMessagebox(title="Error", message="Please select a GIF first")
            return False
        elif media_type == "image" and not self.image_selector.selected_image_url:
            CTkMessagebox(title="Error", message="Please select an image first")
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
        
        media_type = self.media_type_var.get()
        if media_type == "gif":
            bg_filename = "background.gif"
            # Make sure to get the most current GIF URL
            bg_url = self.gif_selector.selected_gif_url
            print(f"Using GIF URL: {bg_url}")
        else:
            bg_filename = "background.jpg"
            # Make sure to get the most current image URL
            bg_url = self.image_selector.selected_image_url
            print(f"Using image URL: {bg_url}")
        
        # Download selected background
        self.progress_label.configure(text=f"Downloading {'GIF' if media_type == 'gif' else 'Image'}...")
        self.progress_bar.set(0.1)
        
        try:
            # Try to use cached image data if available for static images
            if media_type == "image" and hasattr(self.image_selector, 'current_image_data'):
                bg_data = self.image_selector.current_image_data
            else:
                bg_data = requests.get(bg_url).content
                
            with open(bg_filename, 'wb') as f:
                f.write(bg_data)
        except Exception as e:
            raise Exception(f"Failed to download background: {str(e)}")
        
        # Get video info and create output filename
        video_url = self.url_entry.get()
        self.progress_label.configure(text="Getting video info...")
        self.progress_bar.set(0.2)
        video_info = yt_dlp.YoutubeDL().extract_info(video_url, download=False)
        
        # Create appropriate filename based on speed choice
        if self.speed_var.get() == "1":  # Slow down
            prefix = "slowed_down_"
        else:  # Speed up
            prefix = "nightcore_"
            
        video_title = prefix + re.sub(r'[\\/:*?"<>|]', '', video_info['title'].replace(" ", "_"))
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
        
        # Use hardware acceleration for decoding if available
        hwaccel_input = "-hwaccel cuda " if self.has_hw_accel else ""
        command = f'ffmpeg {hwaccel_input}-i "{video_filename}" -vn -af "asetrate=44100*{pitch},aresample=44100" -acodec libmp3lame "{audio_filename}"'
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
        
        # Process based on media type
        if media_type == "gif":
            # Create video from GIF
            temp_video = "looped_video.mp4"
            
            # Use hardware encoding if available
            video_encoder = "-c:v h264_nvenc -preset p4 -tune hq -b:v 5M" if self.has_hw_accel else "-c:v libx264"
            command = f'ffmpeg -stream_loop -1 -i "{bg_filename}" -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" -t {audio_duration} -pix_fmt yuv420p {video_encoder} -r 30 "{temp_video}"'
            
            try:
                subprocess.run(command, shell=True, check=True)
            except subprocess.CalledProcessError:
                # Fallback to software encoding if hardware acceleration fails
                command = f'ffmpeg -stream_loop -1 -i "{bg_filename}" -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" -t {audio_duration} -pix_fmt yuv420p -c:v libx264 -r 30 "{temp_video}"'
                os.system(command)
                
        else:
            try:
                # Create video from static image with text
                temp_video = "image_video.mp4"
                
                # Resize image first
                resized_image = "resized_background.jpg"
                resize_command = f'ffmpeg -i "{bg_filename}" -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" "{resized_image}" -y'
                subprocess.run(resize_command, shell=True, check=True)
                
                # Add text to image - Fix the filename to avoid double extension
                text_image = "background_with_text.jpg"
                
                # Sanitize the title for ffmpeg
                title_text = video_info['title']
                title_text = title_text.replace("_", " ").replace("nightcore", "").replace("(Official Audio)", "")
                title_text = title_text.replace("slowed down", "").replace("(Official Lyric Video)", "")
                title_text = title_text.replace("(Lyrics)", "").replace("(Official Video)", "")
                title_text = title_text.replace("(Official Music Video)", "").strip()
                
                # Escape single quotes and other special characters
                title_text = title_text.replace("'", "\\'").replace('"', '\\"')
                title_text = re.sub(r'[\\/:*?"<>|]', '', title_text)
                
                # Use simpler text overlay command to avoid issues
                text_command = f'ffmpeg -i "{resized_image}" -vf "drawtext=text=\'{title_text}\':fontcolor=white:fontsize=24:box=1:boxcolor=black@0.5:boxborderw=5:x=(w-text_w)/2:y=h-th-30" "{text_image}" -y'
                subprocess.run(text_command, shell=True, check=True)
                
                # Create video from image with text - use hardware acceleration if available
                video_encoder = "-c:v h264_nvenc -preset p4 -tune hq -b:v 5M" if self.has_hw_accel else "-c:v libx264"
                video_command = f'ffmpeg -loop 1 -i "{text_image}" {video_encoder} -t {audio_duration} -pix_fmt yuv420p -r 30 "{temp_video}"'
                
                try:
                    subprocess.run(video_command, shell=True, check=True)
                except subprocess.CalledProcessError:
                    # Fallback to software encoding
                    video_command = f'ffmpeg -loop 1 -i "{text_image}" -c:v libx264 -t {audio_duration} -pix_fmt yuv420p -r 30 "{temp_video}"'
                    subprocess.run(video_command, shell=True, check=True)
                
                # Clean up temporary image files
                if os.path.exists(resized_image):
                    os.remove(resized_image)
                if os.path.exists(text_image):
                    os.remove(text_image)
                    
            except Exception as e:
                # If the image processing fails, fall back to using the original image without text
                self.progress_label.configure(text="Image processing failed, using plain image...")
                temp_video = "image_video.mp4"
                
                # Use hardware acceleration for fallback also
                video_encoder = "-c:v h264_nvenc -preset p4 -tune hq -b:v 5M" if self.has_hw_accel else "-c:v libx264"
                fallback_command = f'ffmpeg -loop 1 -i "{bg_filename}" {video_encoder} -t {audio_duration} -pix_fmt yuv420p -r 30 "{temp_video}"'
                
                try:
                    subprocess.run(fallback_command, shell=True, check=True)
                except subprocess.CalledProcessError:
                    # Final fallback to software encoding
                    fallback_command = f'ffmpeg -loop 1 -i "{bg_filename}" -c:v libx264 -t {audio_duration} -pix_fmt yuv420p -r 30 "{temp_video}"'
                    os.system(fallback_command)
        
        # Combine video and audio
        self.progress_label.configure(text="Combining video and audio...")
        self.progress_bar.set(0.8)
        
        # Use hardware acceleration for final encoding
        if self.has_hw_accel:
            command = f'ffmpeg -i "{temp_video}" -i "{audio_filename}" -c:v h264_nvenc -preset p4 -tune hq -b:v 5M -c:a aac -strict experimental -b:a 192k -shortest "{output_video}"'
            try:
                subprocess.run(command, shell=True, check=True)
            except subprocess.CalledProcessError:
                # Fallback to copy if hardware encoding fails
                command = f'ffmpeg -i "{temp_video}" -i "{audio_filename}" -c:v copy -c:a aac -strict experimental -b:a 192k -shortest "{output_video}"'
                os.system(command)
        else:
            command = f'ffmpeg -i "{temp_video}" -i "{audio_filename}" -c:v copy -c:a aac -strict experimental -b:a 192k -shortest "{output_video}"'
            os.system(command)
        
        # Clean up temporary files
        self.progress_label.configure(text="Cleaning up...")
        self.progress_bar.set(0.9)
        os.remove(video_filename)
        os.remove(audio_filename)
        os.remove(bg_filename)
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
