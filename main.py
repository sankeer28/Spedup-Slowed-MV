import os
import yt_dlp
import requests
import re
import subprocess
import random
import shlex
import platform

def check_nvidia_gpu():
    """Check if NVIDIA GPU with NVENC support is available."""
    try:
        # Check if nvidia-smi is available
        if platform.system() == "Windows":
            result = subprocess.run(['where', 'nvidia-smi'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode != 0:
                return False
        else:  # Linux/Mac
            result = subprocess.run(['which', 'nvidia-smi'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode != 0:
                return False
        
        # Check if nvidia-smi can be executed
        result = subprocess.run(['nvidia-smi'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            return False
            
        # Check if ffmpeg supports nvenc
        result = subprocess.run(['ffmpeg', '-encoders'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if b'h264_nvenc' not in result.stdout:
            return False
            
        return True
    except:
        return False

# Global flag for hardware acceleration
HW_ACCEL_AVAILABLE = check_nvidia_gpu()

def download_video(url, output_file):
    ydl_opts = {
        'outtmpl': output_file,
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def extract_audio(video_file, output_audio, pitch=1.4, slow_down=False):
    if slow_down:
        pitch = 0.9
    
    # Add hardware acceleration for decoding
    hw_args = "-hwaccel cuda -hwaccel_output_format cuda -threads 8 " if HW_ACCEL_AVAILABLE else ""
    
    command = f'ffmpeg {hw_args}-i "{video_file}" -vn -af "asetrate=44100*{pitch},aresample=44100" -acodec libmp3lame "{output_audio}"'
    os.system(command)

def get_audio_duration(audio_file):
    result = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', audio_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    return float(result.stdout)

def download_cat_image(output_image, api_choice, search_query=None):
    try:
        if api_choice == "0":
            response = requests.get("https://pic.re/image")
            response.raise_for_status()  
            image_url = response.url
        elif api_choice == "1":
            response = requests.get("https://api.thecatapi.com/v1/images/search")
            response.raise_for_status()
            data = response.json()
            if not data or 'url' not in data[0]:
                print("Error: No image URL found in response data.")
                return
            image_url = data[0]['url']
        elif api_choice == "2":
            response = requests.get("https://random.imagecdn.app/v1/image?width=1920&height=1080&format=json")
            response.raise_for_status()
            data = response.json()
            if not data or 'url' not in data:
                print("Error: No image URL found in response data.")
                return
            image_url = data['url']
        elif api_choice == "3":
            if search_query is None:
                search_query = input("Enter search query for Pexels image: ")
            download_pexels_image(output_image, search_query)
            return
        elif api_choice == "4":
            if search_query is None:
                search_query = input("Enter search query for GIF: ")
            download_random_gif(search_query, output_image)
            return
        else:
            print("Invalid API choice.")
            return

        image_data = requests.get(image_url).content
        with open(output_image, 'wb') as f:
            f.write(image_data)
    except Exception as e:
        print(f"Error fetching image: {e}")

def download_random_gif(search_query, output_gif):
    TENOR_API_KEY = ''
    try:
        params = {
            'q': search_query,
            'key': TENOR_API_KEY,
            'limit': 50,  
            'media_filter': 'minimal',
            'contentfilter': 'high'
        }
        response = requests.get('https://tenor.googleapis.com/v2/search', params=params)
        response.raise_for_status()
        data = response.json()
        
        if not data.get('results'):
            print("No GIFs found for the given query.")
            return None
        
        # Try to get medium GIF format first, if not available fallback to gif format
        gif_urls = []
        for result in data['results']:
            if 'mediumgif' in result['media_formats']:
                gif_urls.append(result['media_formats']['mediumgif']['url'])
            elif 'gif' in result['media_formats']:
                gif_urls.append(result['media_formats']['gif']['url'])
        
        if not gif_urls:
            print("No GIF URLs found.")
            return None
        
        gif_url = random.choice(gif_urls)
        print(f"Downloading GIF from: {gif_url}")
        gif_data = requests.get(gif_url).content
        with open(output_gif, 'wb') as f:
            f.write(gif_data)
        
        # Verify the GIF can be processed
        cmd = f'ffprobe -v error "{output_gif}"'
        result = os.system(cmd)
        if result != 0:
            print("Downloaded GIF appears to be invalid. Trying another one...")
            return download_random_gif(search_query, output_gif)
            
        return output_gif
    except Exception as e:
        print(f"Error fetching GIF: {e}")
        return None

def download_pexels_image(output_image, search_query):
    try:
        headers = {
            'Authorization': '4xnfarO5xIrjF7DfQnn7vx9GIDTxmfic8rYPZqkgzrAVcdGEkpTBfioF'
        }
        params = {
            'query': search_query,
            'per_page': 1, 
            'orientation': 'landscape',
        }
        response = requests.get('https://api.pexels.com/v1/search', headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        if not data['photos']:
            print("Error: No image found for the given search query.")
            return
        image_url = data['photos'][0]['src']['large']
        image_data = requests.get(image_url).content
        with open(output_image, 'wb') as f:
            f.write(image_data)
    except Exception as e:
        print(f"Error fetching image from Pexels: {e}")

def combine_video_audio_image(image_file, audio_file, output_video, video_title=None, api_choice=None):
    try:
        # Clean up any existing temporary files first
        temp_files = ["looped_video.mp4", "temp_with_text.mp4", "resized_background.jpg", "text_overlay.jpg", "fallback_frame.jpg"]
        for file in temp_files:
            if os.path.exists(file):
                os.remove(file)
        
        # Verify input files exist
        if not os.path.exists(image_file):
            print(f"Error: Image file {image_file} not found!")
            return False
        
        if not os.path.exists(audio_file):
            print(f"Error: Audio file {audio_file} not found!")
            return False
        
        # Set hardware acceleration parameters
        # For image operations, we'll use CPU to avoid compatibility issues
        hw_decode = "-hwaccel cuda -hwaccel_output_format cuda -threads 8 " if HW_ACCEL_AVAILABLE else ""
        hw_encode = "h264_nvenc -preset p4 -tune hq " if HW_ACCEL_AVAILABLE else "libx264 "
        
        # Get audio duration for GIF looping
        try:
            audio_duration = get_audio_duration(audio_file)
            print(f"Audio duration: {audio_duration} seconds")
        except Exception as e:
            print(f"Error getting audio duration: {e}")
            audio_duration = 60  # Default to 60 seconds if we can't get duration

        # Handle GIF background
        if image_file.endswith(".gif"):
            print("Processing GIF background...")
            video_file = "looped_video.mp4"
            
            # First approach: Use -stream_loop to properly loop the GIF for the full audio duration
            print("Converting GIF to looped video...")
            command = f'ffmpeg -y {hw_decode}-stream_loop -1 -i "{image_file}" -t {audio_duration} -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" -pix_fmt yuv420p -c:v {hw_encode} -r 24 "{video_file}"'
            print(f"Running command: {command}")
            result = os.system(command)
            
            # Check if the video was created successfully
            if result != 0 or not os.path.exists(video_file) or os.path.getsize(video_file) == 0:
                print("Error with first method. Trying alternative GIF loop method...")
                
                # Second approach: Use -ignore_loop 0 to respect GIF loop metadata
                command = f'ffmpeg -y {hw_decode}-ignore_loop 0 -i "{image_file}" -t {audio_duration} -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" -pix_fmt yuv420p -c:v {hw_encode} -r 24 "{video_file}"'
                result = os.system(command)
                
                # If that fails too, try a third approach
                if result != 0 or not os.path.exists(video_file) or os.path.getsize(video_file) == 0:
                    print("Error with second method. Trying third GIF loop method...")
                    
                    # Extract GIF info to calculate loop count needed
                    probe_cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{image_file}"'
                    try:
                        gif_duration = float(subprocess.check_output(probe_cmd, shell=True).decode('utf-8').strip())
                        loop_count = int(audio_duration / gif_duration) + 1
                        print(f"GIF duration: {gif_duration}s, need to loop {loop_count} times")
                        
                        # Use explicit loop count
                        command = f'ffmpeg -y {hw_decode}-stream_loop {loop_count} -i "{image_file}" -t {audio_duration} -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" -pix_fmt yuv420p -c:v {hw_encode} -r 24 "{video_file}"'
                        result = os.system(command)
                    except:
                        print("Error calculating GIF duration.")
                        result = 1
                
                # If all GIF methods fail, fall back to static image
                if result != 0 or not os.path.exists(video_file) or os.path.getsize(video_file) == 0:
                    print("All GIF conversion methods failed. Falling back to static image...")
                    # Extract first frame
                    command = f'ffmpeg -y {hw_decode}-i "{image_file}" -vframes 1 "fallback_frame.jpg"'
                    os.system(command)
                    if os.path.exists("fallback_frame.jpg"):
                        return combine_video_audio_image("fallback_frame.jpg", audio_file, output_video, video_title, api_choice)
                    else:
                        print("Failed to extract frame from GIF. Cannot proceed.")
                        return False
            
            # Verify the looped video has the expected duration
            try:
                video_duration = float(subprocess.check_output(
                    f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{video_file}"',
                    shell=True
                ).decode('utf-8').strip())
                print(f"Created video duration: {video_duration}s (target: {audio_duration}s)")
                
                # If the video is too short, recreate it with a higher loop count
                if video_duration < audio_duration - 1:  # Allow 1 second tolerance
                    print("Looped video is too short. Creating with explicit longer duration...")
                    # Use a longer duration to ensure we cover the full audio
                    command = f'ffmpeg -y {hw_decode}-stream_loop -1 -i "{image_file}" -t {audio_duration*1.5} -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" -pix_fmt yuv420p -c:v {hw_encode} -r 24 "{video_file}"'
                    os.system(command)
            except:
                print("Could not verify video duration, continuing anyway.")
            
            # Add text overlay if needed
            if video_title:
                text = re.sub(r'\(.*?\)', '', re.sub(r'[\\/:*?"<>|]', '', video_title.replace("_", " ").replace("nightcore", "").replace("(Official Audio)", "").replace("slowed down", "").replace("(Official Lyric Video)", "").replace("(Lyrics)", "").replace("(Official Video)", "").replace("(Official Music Video)", "").replace("(Official Visualizer)", "").strip()))
                text_file = "temp_with_text.mp4"
                text_command = f'ffmpeg -y {hw_decode}-i "{video_file}" -vf "drawtext=text=\'{text}\':x=w-tw-10:y=h-th-10:fontsize=40:fontcolor=white:shadowcolor=black:shadowx=2:shadowy=2" -c:v {hw_encode} -codec:a copy "{text_file}"'
                print(f"Adding text overlay: {text}")
                result = os.system(text_command)
                
                # Check if text overlay was successful
                if result == 0 and os.path.exists(text_file) and os.path.getsize(text_file) > 0:
                    # Delete the original file first, then rename
                    if os.path.exists(video_file):
                        os.remove(video_file)
                    os.rename(text_file, video_file)
                else:
                    print("Failed to add text overlay. Using video without text.")

            # Combine video with audio
            print("Combining video with audio...")
            final_command = f'ffmpeg -y {hw_decode}-i "{video_file}" -i "{audio_file}" -map 0:v:0 -map 1:a:0 -c:v {hw_encode} -c:a aac -strict experimental -b:a 192k -shortest "{output_video}"'
            result = os.system(final_command)
            
            # Clean up
            if os.path.exists(video_file):
                os.remove(video_file)
                
            # Verify output video was created
            if result != 0 or not os.path.exists(output_video) or os.path.getsize(output_video) == 0:
                print("Failed to create final video with GIF background.")
                return False
                
            return True
        else:
            # Handle static image background
            print("Processing static image background...")
            resized_image_file = "resized_background.jpg"
            
            # For image operations, let's bypass hardware acceleration to avoid compatibility issues
            resize_command = f'ffmpeg -y -i "{image_file}" -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" -frames:v 1 "{resized_image_file}"'
            os.system(resize_command)
            
            if not os.path.exists(resized_image_file) or os.path.getsize(resized_image_file) == 0:
                print(f"Failed to resize image. Using original image.")
                resized_image_file = image_file
            
            if video_title:
                text = re.sub(r'\(.*?\)', '', re.sub(r'[\\/:*?"<>|]', '', video_title.replace("_", " ").replace("nightcore", "").replace("(Official Audio)", "").replace("slowed down", "").replace("(Official Lyric Video)", "").replace("(Lyrics)", "").replace("(Official Video)", "").replace("(Official Music Video)", "").replace("(Official Visualizer)", "").strip()))
                
                # Create image with text directly - no hardware acceleration for single image
                text_image_file = "text_overlay.jpg"
                text_command = f'ffmpeg -y -i "{resized_image_file}" -vf "drawtext=text=\'{text}\':x=w-tw-10:y=h-th-10:fontsize=40:fontcolor=white:shadowcolor=black:shadowx=2:shadowy=2" -frames:v 1 "{text_image_file}"'
                os.system(text_command)
                
                # Check if the text image was created successfully
                if os.path.exists(text_image_file) and os.path.getsize(text_image_file) > 0:
                    command = f'ffmpeg -y {hw_decode}-loop 1 -i "{text_image_file}" -i "{audio_file}" -c:v {hw_encode} -c:a aac -strict experimental -b:a 192k -shortest "{output_video}"'
                    os.system(command)
                    os.remove(text_image_file)
                else:
                    # Fallback if text overlay fails
                    print("Warning: Failed to create text overlay, using image without text.")
                    command = f'ffmpeg -y {hw_decode}-loop 1 -i "{resized_image_file}" -i "{audio_file}" -c:v {hw_encode} -c:a aac -strict experimental -b:a 192k -shortest "{output_video}"'
                    os.system(command)
            else:
                command = f'ffmpeg -y {hw_decode}-loop 1 -i "{resized_image_file}" -i "{audio_file}" -c:v {hw_encode} -c:a aac -strict experimental -b:a 192k -shortest "{output_video}"'
                os.system(command)
            
            if resized_image_file != image_file and os.path.exists(resized_image_file):
                os.remove(resized_image_file)
            
            # Verify output video was created
            if not os.path.exists(output_video) or os.path.getsize(output_video) == 0:
                print("Failed to create final video with static image background.")
                return False
                
            return True
    except Exception as e:
        print(f"Error combining video and audio: {e}")
        if api_choice:
            search_query = None if api_choice != "3" and api_choice != "4" else input("Enter search query: ")
            download_cat_image(image_file, api_choice, search_query)
            return combine_video_audio_image(image_file, audio_file, output_video, video_title, api_choice)
        return False

def main():
    # Display hardware acceleration status
    if HW_ACCEL_AVAILABLE:
        print("NVIDIA GPU hardware acceleration is ENABLED")
    else:
        print("NVIDIA GPU hardware acceleration is NOT AVAILABLE - using CPU")
    
    ascii_art = r"""
       _____                __               _____ __                       __   __  ____    __
      / ___/____  ___  ____/ /_  ______     / ___// /___ _      _____  ____/ /  /  |/  / |  / /
      \__ \/ __ \/ _ \/ __  / / / / __ \    \__ \/ / __ \ | /| / / _ \/ __  /  / /|_/ /| | / / 
     ___/ / /_/ /  __/ /_/ / /_/ / /_/ /   ___/ / / /_/ / |/ |/ /  __/ /_/ /  / /  / / | |/ /
    /____/ .___/\___/\__,_/\__,_/ .___/   /____/_/\____/|__/|__/\___/\__,_/  /_/  /_/  |___/
        /_/                    /_/                                                                                              
    """
    print(ascii_art)
    print("https://github.com/sankeer28/Spedup-Slowed-MV")
    print("Do you want to process:")
    print("1. One URL")
    print("2. All URLs from 'list.txt'")
    print("3. Extract all songs from channel, saves to list.txt (videos under 6 min, skips youtube shorts)")
    choice = input("Enter 1, 2, 3: ")
        
    if choice == '1':
        process_single_url()
    elif choice == '2':
        process_multiple_urls()
    elif choice == '3':
        process_playlist_url()
    else:
        print("Invalid choice. Please enter either 1, 2, or 3.")

def process_playlist_url():
    playlist_url = input("Enter the playlist URL: ")
    command = f'yt-dlp --flat-playlist  --match-filter "original_url!*=/shorts/ & url!*=/shorts/ & duration<360" --print-to-file url list.txt {playlist_url}'
    yt_dlp.main(shlex.split(command))

def process_single_url():
    video_url = input("Enter the video URL: ")
    api_choice = input("Background Options:\n0: Anime wallpaper\n1: Cat wallpaper\n2: Random wallpaper\n3: Pexels image\n4: GIF\nEnter background option: ")

    if api_choice not in ['0', '1', '2', '3', '4']:
        print("Invalid choice. Please enter a valid background option.")
        return
    
    search_query = None
    if api_choice == '3' or api_choice == '4':
        search_query = input(f"Enter search query for {'Pexels image' if api_choice == '3' else 'GIF'}: ")
    
    speed_choice = input("\nAudio Options:\n0: Sped up\n1: Slowed down\nEnter audio option: ")
    if speed_choice not in ['0', '1']:
        print("Invalid choice. Please enter '0' for sped up audio or '1' for slowed down audio.")
        return
    speed_up = speed_choice == '0'
    
    process_single_video(video_url, api_choice, speed_up, search_query)

def process_multiple_urls():
    try:
        with open("list.txt", "r") as file:
            urls = file.readlines()
    except FileNotFoundError:
        print("Error: File 'list.txt' not found.")
        return

    api_choice = input("Background Options:\n0: Anime wallpaper\n1: Cat wallpaper\n2: Random wallpaper\n3: Pexels image\n4: GIF\nEnter background option: ")

    if api_choice not in ['0', '1', '2', '3', '4']:
        print("Invalid choice. Please enter a valid background option.")
        return
    
    search_query = None
    if api_choice == '3' or api_choice == '4':
        search_query = input(f"Enter search query for {'Pexels image' if api_choice == '3' else 'GIF'}: ")
        
    speed_choice = input("\nAudio Options:\n0: Sped up\n1: Slowed down\nEnter audio option: ")
    if speed_choice not in ['0', '1']:
        print("Invalid choice. Please enter '0' for sped up audio or '1' for slowed down audio.")
        return
    speed_up = speed_choice == '0'
    
    for url in urls:
        video_url = url.strip()
        if video_url:
            process_single_video(video_url, api_choice, speed_up, search_query)

def download_audio(url, output_file):
    """Download audio directly from a video URL."""
    # Remove .mp3 extension if present to prevent double extension
    if output_file.endswith('.mp3'):
        output_base = output_file[:-4]
    else:
        output_base = output_file
        
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': output_base,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # Return the correct filename with extension
        expected_filename = f"{output_base}.mp3"
        if os.path.exists(expected_filename):
            print(f"Audio downloaded successfully: {expected_filename}")
            return expected_filename
        else:
            print(f"Warning: Expected file {expected_filename} not found")
            # Try to find any mp3 file that starts with the output_base
            for file in os.listdir():
                if file.startswith(output_base) and file.endswith('.mp3'):
                    print(f"Found alternative audio file: {file}")
                    return file
            print("Error: Could not find downloaded audio file")
            return None
    except Exception as e:
        print(f"Error downloading audio: {e}")
        return None

def modify_audio_speed(input_audio, output_audio, pitch=1.4, slow_down=False):
    """Modify audio speed and pitch."""
    if slow_down:
        pitch = 0.9
    
    # Add hardware acceleration for decoding
    hw_args = "-hwaccel cuda -hwaccel_output_format cuda -threads 8 " if HW_ACCEL_AVAILABLE else ""
    
    command = f'ffmpeg {hw_args}-i "{input_audio}" -af "asetrate=44100*{pitch},aresample=44100" -acodec libmp3lame "{output_audio}"'
    os.system(command)

def process_single_video(video_url, api_choice, speed_up, search_query):
    video_info = yt_dlp.YoutubeDL().extract_info(video_url, download=False)
    
    if speed_up:
        video_title = "nightcore_" + re.sub(r'[\\/:*?"<>|]', '', video_info['title'].replace(" ", "_"))
    else:
        video_title = "slowed_down_" + re.sub(r'[\\/:*?"<>|]', '', video_info['title'].replace(" ", "_"))
    
    # Download audio directly
    downloaded_audio_base = "original_audio"
    audio_filename = "modified_audio.mp3"
    
    # Set appropriate file extension based on background type
    image_filename = "background.gif" if api_choice == "4" else "background.jpg"
    output_video = f"{video_title}.mp4"

    print(f"\nProcessing: {video_info['title']}")
    print(f"Downloading audio...")
    downloaded_audio = download_audio(video_url, downloaded_audio_base)
    
    if not downloaded_audio or not os.path.exists(downloaded_audio):
        print(f"Error: Failed to download audio for {video_info['title']}")
        return
    
    print(f"Modifying audio speed/pitch...")
    modify_audio_speed(downloaded_audio, audio_filename, slow_down=not speed_up)
    
    if not os.path.exists(audio_filename):
        print(f"Error: Failed to create modified audio file {audio_filename}")
        return
    
    print(f"Downloading {'GIF' if api_choice == '4' else 'image'} background...")
    download_cat_image(image_filename, api_choice, search_query)
    
    print(f"Creating final video...")
    success = combine_video_audio_image(image_filename, audio_filename, output_video, video_title, api_choice)
    
    # Clean up temporary files
    if downloaded_audio and os.path.exists(downloaded_audio):
        os.remove(downloaded_audio)
    
    if os.path.exists(audio_filename):
        os.remove(audio_filename)
    
    if os.path.exists(image_filename):
        os.remove(image_filename)
    
    # Only move the file if it was created successfully
    if success and os.path.exists(output_video):
        print(f"Video created successfully: {output_video}")
        if not os.path.exists("outputs"):
            os.makedirs("outputs")
        output_path = os.path.join("outputs", output_video)
        try:
            # Remove any existing file with the same name in the output directory
            if os.path.exists(output_path):
                os.remove(output_path)
            os.rename(output_video, output_path)
            print(f"Video moved to outputs folder.")
        except Exception as e:
            print(f"Error moving video to outputs folder: {e}")
    else:
        print(f"Failed to create video for {video_info['title']}")

if __name__ == "__main__":
    main()
