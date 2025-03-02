import os
import yt_dlp
import requests
import re
import subprocess
import random
import shlex

def detect_gpu_acceleration():
    """Detect available GPU acceleration methods for FFmpeg, prioritizing NVIDIA."""
    encoders = {}
    
    # First, detect what hardware accelerations are supported
    supported_hwaccels = []
    try:
        hwaccel_cmd = 'ffmpeg -hide_banner -hwaccels'
        hwaccel_result = subprocess.run(hwaccel_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if hwaccel_result.returncode == 0:
            # Parse the output to get supported hardware accelerations
            lines = hwaccel_result.stdout.strip().split('\n')
            if len(lines) > 1:  # First line is typically "Hardware acceleration methods:"
                for line in lines[1:]:
                    hwaccel = line.strip()
                    if hwaccel and not hwaccel.startswith('Hardware'):
                        supported_hwaccels.append(hwaccel)
            
            print(f"Supported hardware accelerations: {', '.join(supported_hwaccels)}")
    except Exception as e:
        print(f"Error detecting hardware accelerations: {e}")
    
    try:
        # Check for NVIDIA GPU (NVENC) if CUDA is supported
        if 'cuda' in supported_hwaccels:
            nvidia_cmd = 'ffmpeg -hide_banner -encoders | findstr nvenc'
            if os.name != 'nt':  # If not Windows
                nvidia_cmd = 'ffmpeg -hide_banner -encoders | grep nvenc'
            nvidia_result = subprocess.run(nvidia_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if nvidia_result.returncode == 0 and b'h264_nvenc' in nvidia_result.stdout:
                # Use higher performance settings for NVIDIA
                encoders['nvidia'] = {
                    'hwaccel': 'cuda',
                    'encoder': 'h264_nvenc',
                    'preset': 'p1',  # Fast preset for NVENC
                    'priority': 0  # Highest priority (reduced from 1 to 0)
                }
                print("NVIDIA NVENC encoding available and prioritized")
    
        # Check for Intel Quick Sync Video (QSV) if QSV is supported
        if 'qsv' in supported_hwaccels:
            qsv_cmd = 'ffmpeg -hide_banner -encoders | findstr qsv'
            if os.name != 'nt':
                qsv_cmd = 'ffmpeg -hide_banner -encoders | grep qsv'
            qsv_result = subprocess.run(qsv_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if qsv_result.returncode == 0 and b'h264_qsv' in qsv_result.stdout:
                encoders['intel'] = {
                    'hwaccel': 'qsv',
                    'encoder': 'h264_qsv',
                    'preset': 'faster',
                    'priority': 2
                }
                print("Intel QuickSync encoding available")
    
        # Check for AMD AMF if D3D11VA or DXVA2 is supported (Windows-specific)
        if 'd3d11va' in supported_hwaccels or 'dxva2' in supported_hwaccels:
            amf_cmd = 'ffmpeg -hide_banner -encoders | findstr amf'
            if os.name != 'nt':
                amf_cmd = 'ffmpeg -hide_banner -encoders | grep amf'
            amf_result = subprocess.run(amf_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if amf_result.returncode == 0 and b'h264_amf' in amf_result.stdout:
                encoders['amd'] = {
                    'hwaccel': 'd3d11va' if 'd3d11va' in supported_hwaccels else 'dxva2',
                    'encoder': 'h264_amf',
                    'preset': 'faster',
                    'priority': 3
                }
                print("AMD AMF encoding available")
    except Exception as e:
        print(f"Error detecting GPU acceleration: {e}")
    
    # Always include CPU as fallback
    encoders['cpu'] = {
        'hwaccel': '',
        'encoder': 'libx264',
        'preset': 'medium',
        'priority': 4
    }
    print("CPU encoding always available as fallback")
    
    # Sort by priority
    sorted_encoders = sorted(encoders.items(), key=lambda x: x[1]['priority'])
    return [v for k, v in sorted_encoders]

def run_ffmpeg_with_gpu_fallback(command_template, input_args, output_file):
    """Try to run ffmpeg command with GPU acceleration, prioritizing NVIDIA, then falling back to others."""
    encoders = detect_gpu_acceleration()
    
    # Fast-path for NVIDIA - try this first if available
    nvidia_encoder = next((encoder for encoder in encoders if encoder.get('encoder') == 'h264_nvenc'), None)
    if nvidia_encoder:
        # Move the NVIDIA encoder to the front of the list
        encoders.remove(nvidia_encoder)
        encoders.insert(0, nvidia_encoder)
        
    # Now try encoders in order
    for encoder in encoders:
        hwaccel_param = f"-hwaccel {encoder['hwaccel']} " if encoder['hwaccel'] else ""
        video_codec = f"-c:v {encoder['encoder']} "
        preset = f"-preset {encoder['preset']} " if encoder['preset'] else ""
        
        # Build the command with the current encoder - making sure ffmpeg comes first
        command = command_template.format(
            hwaccel=hwaccel_param, 
            video_codec=video_codec,
            preset=preset,
            **input_args
        )
        
        print(f"Trying encoder: {encoder['encoder']}")
        print(f"Running command: {command}")
        
        # Use subprocess to capture detailed error output
        try:
            process = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            if process.returncode == 0 and os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                print(f"Successfully processed with {encoder['encoder']}")
                return True
            else:
                print(f"Command failed with return code {process.returncode}")
                if process.stderr:
                    print(f"Error details: {process.stderr[:500]}...")  # Print first 500 chars of error
        except Exception as e:
            print(f"Exception running command: {e}")
        
        print(f"Failed with {encoder['encoder']}, trying next option...")
    
    print("All encoding options failed")
    return False

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
    # Improved quality settings with higher bitrate and better sampling
    command = f'ffmpeg -i "{video_file}" -vn -af "asetrate=48000*{pitch},aresample=48000" -acodec libmp3lame -b:a 320k -ar 48000 "{output_audio}"'
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
    TENOR_API_KEY = 'AIzaSyB0w1-_22Dk7_yyH62m2Tu8mRPJdKvcA7Y'
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

def escape_text_for_ffmpeg(text):
    """Properly escape text for ffmpeg's drawtext filter."""
    # First, escape single quotes (most critical as they delimit the filter string)
    text = text.replace("'", "'\\\\\\''")
    # Escape other potentially problematic characters
    text = text.replace(':', '\\:').replace(',', '\\,').replace('[', '\\[').replace(']', '\\]')
    return text

def download_audio(url, output_file):
    """Download audio directly from YouTube without downloading video first, prioritizing high quality"""
    ydl_opts = {
        # Format selection prioritizes high quality audio
        'format': 'bestaudio[acodec=opus]/bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',  # Increased from 192 to 320 kbps
        }],
        # Add audio quality settings
        'postprocessor_args': [
            '-ar', '48000',
            '-ac', '2',
        ],
        'outtmpl': output_file.replace('.mp3', ''),  # yt-dlp will add extension
    }
    
    try:
        print("Downloading highest quality audio available...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            # Show info about selected format
            if 'formats' in info:
                selected_format = next((f for f in info['formats'] if f.get('format_id') == info.get('format_id')), None)
                if selected_format:
                    print(f"Selected audio format: {selected_format.get('format_note', 'Unknown')} "
                          f"[{selected_format.get('ext', 'Unknown')}] - "
                          f"{selected_format.get('abr', 'Unknown')}kbps")
            
            # Download the audio
            ydl.download([url])
        
        # Ensure we have the correct filename (yt-dlp adds extension automatically)
        actual_file = output_file.replace('.mp3', '') + '.mp3'
        if os.path.exists(actual_file) and actual_file != output_file:
            os.rename(actual_file, output_file)
            
        return True
    except Exception as e:
        print(f"Error downloading high quality audio: {e}")
        
        # Try a fallback with simpler options
        try:
            print("Trying fallback audio download method...")
            simpler_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                }],
                'outtmpl': output_file.replace('.mp3', '')
            }
            with yt_dlp.YoutubeDL(simpler_opts) as ydl:
                ydl.download([url])
                
            actual_file = output_file.replace('.mp3', '') + '.mp3'
            if os.path.exists(actual_file) and actual_file != output_file:
                os.rename(actual_file, output_file)
                
            return True
        except Exception as e2:
            print(f"Fallback download method also failed: {e2}")
            return False

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
            # Add NVIDIA-specific settings if using NVIDIA
            command_template = 'ffmpeg {hwaccel}-y -stream_loop -1 -i "{input_file}" -t {duration} -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" -pix_fmt yuv420p {video_codec}{preset}"{output_file}"'
            
            success = run_ffmpeg_with_gpu_fallback(command_template, {
                'input_file': image_file,
                'duration': audio_duration,
                'output_file': video_file
            }, video_file)
            
            # Check if the video was created successfully
            if not success:
                print("Error with first method. Trying alternative GIF loop method...")
                
                # Second approach: Use -ignore_loop 0 to respect GIF loop metadata
                command_template = 'ffmpeg {hwaccel}-y -ignore_loop 0 -i "{input_file}" -t {duration} -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" -pix_fmt yuv420p {video_codec}{preset}"{output_file}"'
                
                success = run_ffmpeg_with_gpu_fallback(command_template, {
                    'input_file': image_file,
                    'duration': audio_duration,
                    'output_file': video_file
                }, video_file)
                
                # If that fails too, try a third approach
                if not success:
                    print("Error with second method. Trying third GIF loop method...")
                    
                    # Extract GIF info to calculate loop count needed
                    probe_cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{image_file}"'
                    try:
                        gif_duration = float(subprocess.check_output(probe_cmd, shell=True).decode('utf-8').strip())
                        loop_count = int(audio_duration / gif_duration) + 1
                        print(f"GIF duration: {gif_duration}s, need to loop {loop_count} times")
                        
                        # Use explicit loop count
                        command_template = 'ffmpeg {hwaccel}-y -stream_loop {loop_count} -i "{input_file}" -t {duration} -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" -pix_fmt yuv420p {video_codec}{preset}"{output_file}"'
                        
                        success = run_ffmpeg_with_gpu_fallback(command_template, {
                            'input_file': image_file,
                            'duration': audio_duration,
                            'loop_count': loop_count,
                            'output_file': video_file
                        }, video_file)
                    except:
                        print("Error calculating GIF duration.")
                        success = False
                
                # If all GIF methods fail, fall back to static image
                if not success:
                    print("All GIF conversion methods failed. Falling back to static image...")
                    # Extract first frame
                    command = f'ffmpeg -y -i "{image_file}" -vframes 1 "fallback_frame.jpg"'
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
                    command_template = 'ffmpeg {hwaccel}-y -stream_loop -1 -i "{input_file}" -t {duration} -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" -pix_fmt yuv420p {video_codec}{preset}"{output_file}"'
                    
                    run_ffmpeg_with_gpu_fallback(command_template, {
                        'input_file': image_file,
                        'duration': audio_duration*1.5,
                        'output_file': video_file
                    }, video_file)
            except:
                print("Could not verify video duration, continuing anyway.")
            
            # Combine video with audio (no text overlay)
            print("Combining video with audio...")
            command_template = 'ffmpeg {hwaccel}-y -i "{input_video}" -i "{input_audio}" -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -strict experimental -b:a 192k -shortest "{output_file}"'
            
            success = run_ffmpeg_with_gpu_fallback(command_template, {
                'input_video': video_file,
                'input_audio': audio_file,
                'output_file': output_video
            }, output_video)
            
            # Clean up
            if os.path.exists(video_file):
                os.remove(video_file)
                
            # Verify output video was created
            if not success:
                print("Failed to create final video with GIF background.")
                return False
                
            return True
        else:
            # Handle static image background
            print("Processing static image background...")
            resized_image_file = "resized_background.jpg"
            
            command_template = 'ffmpeg {hwaccel}-y -i "{input_file}" -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" {video_codec}{preset}"{output_file}"'
            
            resize_success = run_ffmpeg_with_gpu_fallback(command_template, {
                'input_file': image_file,
                'output_file': resized_image_file
            }, resized_image_file)
            
            if not resize_success:
                print(f"Failed to resize image. Using original image.")
                resized_image_file = image_file
            
            # Create video directly from static image and audio (no text overlay)
            command_template = 'ffmpeg {hwaccel}-y -loop 1 -i "{input_image}" -i "{input_audio}" {video_codec}{preset}-c:a aac -strict experimental -b:a 192k -shortest "{output_file}"'
            
            success = run_ffmpeg_with_gpu_fallback(command_template, {
                'input_image': resized_image_file,
                'input_audio': audio_file,
                'output_file': output_video
            }, output_video)
            
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

def process_single_video(video_url, api_choice, speed_up, search_query):
    video_info = yt_dlp.YoutubeDL().extract_info(video_url, download=False)
    
    if speed_up:
        video_title = "nightcore_" + re.sub(r'[\\/:*?"<>|]', '', video_info['title'].replace(" ", "_"))
    else:
        video_title = "slowed_down_" + re.sub(r'[\\/:*?"<>|]', '', video_info['title'].replace(" ", "_"))
    
    audio_filename = "audio.mp3"
    
    # Set appropriate file extension based on background type
    image_filename = "background.gif" if api_choice == "4" else "background.jpg"
    output_video = f"{video_title}.mp4"

    print(f"\nProcessing: {video_info['title']}")
    
    # Download audio directly instead of downloading video first
    print(f"Downloading audio...")
    if download_audio(video_url, audio_filename):
        print(f"Audio downloaded successfully")
    else:
        print(f"Failed to download audio directly, falling back to video download method")
        video_filename = "video.mp4"
        download_video(video_url, video_filename)
        print(f"Extracting and modifying audio...")
        extract_audio(video_filename, audio_filename, slow_down=not speed_up)
        # Clean up video file
        if os.path.exists(video_filename):
            os.remove(video_filename)
    
    # Apply audio speed modification
    print(f"Modifying audio speed...")
    temp_audio = "temp_audio.mp3"
    if os.path.exists(temp_audio):
        os.remove(temp_audio)
    extract_audio(audio_filename, temp_audio, slow_down=not speed_up)
    os.remove(audio_filename)
    os.rename(temp_audio, audio_filename)
    
    print(f"Downloading {'GIF' if api_choice == '4' else 'image'} background...")
    download_cat_image(image_filename, api_choice, search_query)
    
    print(f"Creating final video...")
    success = combine_video_audio_image(image_filename, audio_filename, output_video, video_title, api_choice)
    
    # Clean up audio file
    if os.path.exists(audio_filename):
        os.remove(audio_filename)
    
    # Clean up image file
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
