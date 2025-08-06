from flask import Flask, render_template, request, jsonify, send_file, Response
import subprocess
import os
import threading
import yt_dlp
import re
import requests
import shutil
import zipfile
import tempfile
import time
from datetime import datetime

app = Flask(__name__)

# Get the directory where the script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Define paths to FFmpeg executables
FFMPEG_PATH = os.path.join(SCRIPT_DIR, "ffmpeg.exe")
FFPROBE_PATH = os.path.join(SCRIPT_DIR, "ffprobe.exe")

# Global variables for progress tracking
processing_status = {
    'status': 'idle',
    'progress': 0,
    'message': '',
    'output_file': None
}

def quote_path(path):
    return f'"{path}"'

def download_ffmpeg():
    """Download FFmpeg executables if they don't exist"""
    if os.path.exists(FFMPEG_PATH) and os.path.exists(FFPROBE_PATH):
        return True
    
    print("FFmpeg not found. Downloading...")
    
    # FFmpeg download URL for Windows
    ffmpeg_url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    
    try:
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = os.path.join(temp_dir, "ffmpeg.zip")
            
            # Download the zip file
            print("Downloading FFmpeg archive...")
            response = requests.get(ffmpeg_url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"\rDownload progress: {progress:.1f}%", end='', flush=True)
            
            print("\nExtracting FFmpeg...")
            
            # Extract the zip file
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Find the bin directory in the extracted files
                for file_info in zip_ref.filelist:
                    if file_info.filename.endswith('ffmpeg.exe') or file_info.filename.endswith('ffprobe.exe'):
                        # Extract just the executable files to the script directory
                        exe_name = os.path.basename(file_info.filename)
                        target_path = os.path.join(SCRIPT_DIR, exe_name)
                        
                        with zip_ref.open(file_info) as source, open(target_path, 'wb') as target:
                            shutil.copyfileobj(source, target)
                        
                        print(f"Extracted {exe_name}")
            
            # Verify both files were extracted
            if os.path.exists(FFMPEG_PATH) and os.path.exists(FFPROBE_PATH):
                print("FFmpeg downloaded and extracted successfully!")
                return True
            else:
                print("Error: Failed to extract FFmpeg executables")
                return False
                
    except Exception as e:
        print(f"Error downloading FFmpeg: {e}")
        return False

def check_nvidia_gpu():
    """Check if NVIDIA GPU is available for hardware acceleration."""
    try:
        # Check if the NVENC encoder is available
        result = subprocess.run(
            [FFMPEG_PATH, '-hide_banner', '-encoders'],
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

def process_video_task(youtube_url, media_type, bg_url, speed_choice, save_credits, custom_speed=None):
    """Background task for video processing"""
    global processing_status
    
    try:
        processing_status['status'] = 'processing'
        processing_status['progress'] = 10
        processing_status['message'] = 'Starting video processing...'
        
        # Initialize filenames
        video_filename = "video.mp4"
        audio_filename = "audio.mp3"
        
        if media_type == "gif":
            bg_filename = "background.gif"
        else:
            bg_filename = "background.jpg"
        
        # Download selected background
        processing_status['progress'] = 15
        processing_status['message'] = f'Downloading {"GIF" if media_type == "gif" else "Image"}...'
        
        # Download with better error handling and headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        try:
            response = requests.get(bg_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Check if we actually got image data
            content_type = response.headers.get('content-type', '')
            if not any(img_type in content_type.lower() for img_type in ['image', 'gif']):
                print(f"Warning: Content-Type is {content_type}, might not be an image")
            
            bg_data = response.content
            if len(bg_data) == 0:
                raise Exception("Downloaded file is empty")
                
            with open(bg_filename, 'wb') as f:
                f.write(bg_data)
                
            print(f"Downloaded background: {len(bg_data)} bytes, Content-Type: {content_type}")
            
            # Verify the downloaded file is a valid image using FFprobe
            try:
                probe_command = f'{quote_path(FFPROBE_PATH)} -v error -select_streams v:0 -show_entries stream=codec_name,width,height -of csv=p=0 {quote_path(bg_filename)}'
                probe_result = subprocess.run(probe_command, shell=True, capture_output=True, text=True)
                if probe_result.returncode == 0:
                    print(f"Image validation successful: {probe_result.stdout.strip()}")
                else:
                    print(f"Image validation failed: {probe_result.stderr}")
                    raise Exception(f"Downloaded file is not a valid image: {probe_result.stderr}")
            except Exception as probe_error:
                print(f"Image validation error: {probe_error}")
                raise Exception(f"Downloaded image file is corrupted or invalid")
            
        except Exception as e:
            raise Exception(f"Failed to download background image: {str(e)}")
        
        # Get video info and create output filename
        processing_status['progress'] = 25
        processing_status['message'] = 'Getting video info...'
        video_info = yt_dlp.YoutubeDL().extract_info(youtube_url, download=False)
        
        # Create appropriate filename based on speed choice
        if speed_choice == "slow":
            prefix = "slowed_down_"
        else:  # speed up
            prefix = "nightcore_"
            
        # More thorough sanitization of the filename
        video_title = video_info['title']
        sanitized_title = re.sub(r'[^a-zA-Z0-9]', '_', video_title)
        sanitized_title = re.sub(r'_{2,}', '_', sanitized_title)
        if len(sanitized_title) > 50:
            sanitized_title = sanitized_title[:50]
        sanitized_filename = f"{prefix}{sanitized_title}"
        output_video = f"{sanitized_filename}.mp4"
        
        # Download YouTube audio only
        processing_status['progress'] = 35
        processing_status['message'] = 'Downloading audio...'
        base_audio_name = os.path.splitext(audio_filename)[0]
        ydl_opts = {
            'outtmpl': base_audio_name,
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])
        
        # Find the actual downloaded audio file
        downloaded_audio = None
        if os.path.exists(audio_filename):
            downloaded_audio = audio_filename
        elif os.path.exists(f"{audio_filename}.mp3"):
            downloaded_audio = f"{audio_filename}.mp3"
        elif os.path.exists(f"{base_audio_name}.mp3"):
            downloaded_audio = f"{base_audio_name}.mp3"
        else:
            raise Exception("Could not find downloaded audio file")
        
        # Process audio (change pitch/speed)
        processing_status['progress'] = 50
        processing_status['message'] = 'Processing audio...'
        
        # Use custom speed if provided, otherwise use defaults
        if custom_speed is not None:
            pitch = custom_speed
        else:
            pitch = 0.9 if speed_choice == "slow" else 1.4
        
        processed_audio = "processed_audio.mp3"
        command = f'{quote_path(FFMPEG_PATH)} -i {quote_path(downloaded_audio)} -af "asetrate=44100*{pitch},aresample=44100" -acodec libmp3lame {quote_path(processed_audio)} -y'
        subprocess.run(command, shell=True)
        
        # Clean up original downloaded file and rename processed file
        if os.path.exists(downloaded_audio):
            os.remove(downloaded_audio)
        os.rename(processed_audio, audio_filename)
        
        # Get audio duration
        processing_status['progress'] = 65
        processing_status['message'] = 'Preparing final video...'
        result = subprocess.run(
            [FFPROBE_PATH, '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', audio_filename],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        audio_duration = float(result.stdout)
        
        # Check hardware acceleration
        has_hw_accel = check_nvidia_gpu()
        
        # Process based on media type
        processing_status['progress'] = 75
        processing_status['message'] = 'Creating video...'
        
        if media_type == "gif":
            # Create video from GIF - use original resolution
            temp_video = "looped_video.mp4"
            
            video_encoder = "-c:v h264_nvenc -preset p4 -tune hq -b:v 5M" if has_hw_accel else "-c:v libx264"
            command = f'{quote_path(FFMPEG_PATH)} -stream_loop -1 -i {quote_path(bg_filename)} -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" -t {audio_duration} -pix_fmt yuv420p {video_encoder} -r 30 {quote_path(temp_video)} -y'
            
            try:
                subprocess.run(command, shell=True, check=True)
            except subprocess.CalledProcessError:
                # Fallback: try without scaling to preserve original resolution
                command = f'{quote_path(FFMPEG_PATH)} -stream_loop -1 -i {quote_path(bg_filename)} -t {audio_duration} -pix_fmt yuv420p -c:v libx264 -r 30 {quote_path(temp_video)} -y'
                subprocess.run(command, shell=True)
        else:
            # Create video from static image
            temp_video = "image_video.mp4"
            
            # Resize image first with better error handling
            resized_image = "resized_background.jpg"
            
            # Try with pixel format conversion first
            resize_command = f'{quote_path(FFMPEG_PATH)} -i {quote_path(bg_filename)} -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" -pix_fmt rgb24 {quote_path(resized_image)} -y'
            try:
                subprocess.run(resize_command, shell=True, check=True)
            except subprocess.CalledProcessError:
                print("First resize attempt failed, trying with different format...")
                # Fallback: try without pixel format specification
                resize_command = f'{quote_path(FFMPEG_PATH)} -i {quote_path(bg_filename)} -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" {quote_path(resized_image)} -y'
                try:
                    subprocess.run(resize_command, shell=True, check=True)
                except subprocess.CalledProcessError:
                    print("Second resize attempt failed, trying simpler scaling...")
                    # Fallback: try with simpler scaling
                    resize_command = f'{quote_path(FFMPEG_PATH)} -i {quote_path(bg_filename)} -vf "scale=1280:720" {quote_path(resized_image)} -y'
                    subprocess.run(resize_command, shell=True, check=True)
            
            video_encoder = "-c:v h264_nvenc -preset p4 -tune hq -b:v 5M" if has_hw_accel else "-c:v libx264"
            video_command = f'{quote_path(FFMPEG_PATH)} -loop 1 -i {quote_path(resized_image)} {video_encoder} -t {audio_duration} -pix_fmt yuv420p -r 30 {quote_path(temp_video)} -y'
            
            try:
                subprocess.run(video_command, shell=True, check=True)
            except subprocess.CalledProcessError:
                video_command = f'{quote_path(FFMPEG_PATH)} -loop 1 -i {quote_path(resized_image)} -c:v libx264 -t {audio_duration} -pix_fmt yuv420p -r 30 {quote_path(temp_video)} -y'
                subprocess.run(video_command, shell=True, check=True)
            
            if os.path.exists(resized_image):
                os.remove(resized_image)
        
        # Combine video and audio
        processing_status['progress'] = 85
        processing_status['message'] = 'Combining video and audio...'
        
        current_dir_output = output_video
        
        if has_hw_accel:
            command = f'{quote_path(FFMPEG_PATH)} -hwaccel cuda -i {quote_path(temp_video)} -i {quote_path(audio_filename)} -c:v h264_nvenc -preset p4 -tune hq -b:v 5M -c:a aac -strict experimental -b:a 192k -shortest {quote_path(current_dir_output)} -y'
            try:
                subprocess.run(command, shell=True, check=True)
            except subprocess.CalledProcessError:
                command = f'{quote_path(FFMPEG_PATH)} -i {quote_path(temp_video)} -i {quote_path(audio_filename)} -c:v copy -c:a aac -strict experimental -b:a 192k -shortest {quote_path(current_dir_output)} -y'
                subprocess.run(command, shell=True)
        else:
            command = f'{quote_path(FFMPEG_PATH)} -i {quote_path(temp_video)} -i {quote_path(audio_filename)} -c:v libx264 -preset fast -crf 22 -c:a aac -strict experimental -b:a 192k -shortest {quote_path(current_dir_output)} -y'
            try:
                subprocess.run(command, shell=True, check=True)
            except subprocess.CalledProcessError:
                command = f'{quote_path(FFMPEG_PATH)} -i {quote_path(temp_video)} -i {quote_path(audio_filename)} -c:v copy -c:a aac -strict experimental -b:a 192k -shortest {quote_path(current_dir_output)} -y'
                subprocess.run(command, shell=True)
        
        # Clean up temporary files
        processing_status['progress'] = 95
        processing_status['message'] = 'Cleaning up...'
        try:
            os.remove(audio_filename)
            os.remove(bg_filename)
            os.remove(temp_video)
        except Exception as e:
            print(f"Warning: Could not remove temporary file: {e}")
        
        # Move to outputs folder
        output_folder = os.path.join(SCRIPT_DIR, "outputs")
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        # Find the created file
        if not os.path.exists(current_dir_output):
            possible_files = [f for f in os.listdir('.') if f.endswith('.mp4')]
            if possible_files:
                current_dir_output = possible_files[0]
            else:
                raise Exception("No MP4 output file found")
        
        # Move to outputs folder
        output_path = os.path.join(output_folder, os.path.basename(current_dir_output))
        if os.path.exists(output_path):
            timestamp = int(time.time())
            filename_parts = os.path.splitext(os.path.basename(current_dir_output))
            new_filename = f"{filename_parts[0]}_{timestamp}{filename_parts[1]}"
            output_path = os.path.join(output_folder, new_filename)
        
        shutil.copy2(current_dir_output, output_path)
        os.remove(current_dir_output)
        
        processing_status['status'] = 'complete'
        processing_status['progress'] = 100
        processing_status['message'] = 'Video created successfully!'
        processing_status['output_file'] = output_path
        
    except Exception as e:
        processing_status['status'] = 'error'
        processing_status['message'] = f'Error creating video: {str(e)}'
        print(f"Error in video processing: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/process', methods=['POST'])
def process_video():
    global processing_status
    
    if processing_status['status'] == 'processing':
        return jsonify({'error': 'Already processing a video'}), 400
    
    data = request.json
    youtube_url = data.get('youtube_url')
    media_type = data.get('media_type')  # 'gif' or 'image'
    bg_url = data.get('bg_url')
    speed_choice = data.get('speed_choice')  # 'fast', 'slow', or 'custom'
    custom_speed = data.get('custom_speed')  # float value for custom speed
    save_credits = data.get('save_credits', False)
    
    if not all([youtube_url, media_type, bg_url, speed_choice]):
        return jsonify({'error': 'Missing required parameters'}), 400
    
    # Reset processing status
    processing_status = {
        'status': 'processing',
        'progress': 0,
        'message': 'Starting...',
        'output_file': None
    }
    
    # Start processing in background thread
    thread = threading.Thread(target=process_video_task, args=(youtube_url, media_type, bg_url, speed_choice, save_credits, custom_speed))
    thread.daemon = True
    thread.start()
    
    return jsonify({'message': 'Processing started'})

@app.route('/api/status')
def get_status():
    return jsonify(processing_status)

@app.route('/api/gif-search')
def search_gifs():
    query = request.args.get('query', '')
    api_key = request.args.get('api_key', '')
    offset = int(request.args.get('offset', 0))
    
    if not query or not api_key:
        return jsonify({'error': 'Missing query or API key'}), 400
    
    try:
        params = {
            'q': query,
            'key': api_key,
            'limit': 12,
            'pos': offset,  # Tenor uses 'pos' for offset
            'media_filter': 'minimal',
            'contentfilter': 'high'
        }
        
        response = requests.get('https://tenor.googleapis.com/v2/search', params=params)
        data = response.json()
        
        gifs = []
        for result in data.get('results', []):
            gifs.append({
                'url': result['media_formats']['gif']['url'],
                'preview': result['media_formats']['tinygif']['url']
            })
        
        return jsonify({'gifs': gifs, 'hasMore': len(gifs) == 12})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/images')
def get_images():
    source = request.args.get('source', 'anime')  # anime, cat, random
    count = int(request.args.get('count', 12))
    page = int(request.args.get('page', 1))
    
    try:
        images = []
        
        if source == 'anime':
            # For anime, we'll use different endpoints to get variety
            endpoints = [
                "https://api.waifu.pics/sfw/waifu",
                "https://api.waifu.pics/sfw/neko", 
                "https://api.waifu.pics/sfw/shinobu",
                "https://api.waifu.pics/sfw/megumin"
            ]
            
            for _ in range(count):
                # Rotate through different endpoints for variety
                endpoint = endpoints[len(images) % len(endpoints)]
                try:
                    response = requests.get(endpoint, timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        if 'url' in data:
                            images.append(data['url'])
                except:
                    continue
                        
        elif source == 'cat':
            # Cat API supports pagination
            params = {'limit': count, 'page': page - 1}
            response = requests.get("https://api.thecatapi.com/v1/images/search", params=params)
            if response.status_code == 200:
                data = response.json()
                for item in data:
                    if 'url' in item:
                        images.append(item['url'])
                        
        elif source == 'random':
            for _ in range(count):
                try:
                    # Add some variety to random images
                    width = 500 + (page * 50)  # Slight variation based on page
                    height = 500 + (page * 50)
                    response = requests.get(f"https://random.imagecdn.app/v1/image?width={width}&height={height}&format=json", timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        if 'url' in data:
                            images.append(data['url'])
                except:
                    continue
        
        return jsonify({'images': images, 'page': page, 'hasMore': len(images) == count})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    output_folder = os.path.join(SCRIPT_DIR, "outputs")
    file_path = os.path.join(output_folder, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return "File not found", 404

@app.route('/video/<filename>')
def serve_video(filename):
    """Serve video files for streaming in the browser with range support"""
    output_folder = os.path.join(SCRIPT_DIR, "outputs")
    file_path = os.path.join(output_folder, filename)
    
    if not os.path.exists(file_path):
        return "File not found", 404
    
    def generate():
        with open(file_path, 'rb') as f:
            data = f.read(1024)
            while data:
                yield data
                data = f.read(1024)
    
    file_size = os.path.getsize(file_path)
    
    # Handle range requests for video streaming
    range_header = request.headers.get('Range', None)
    if range_header:
        byte_start = 0
        byte_end = file_size - 1
        
        # Parse range header
        range_match = re.match(r'bytes=(\d+)-(\d*)', range_header)
        if range_match:
            byte_start = int(range_match.group(1))
            if range_match.group(2):
                byte_end = int(range_match.group(2))
        
        # Read the requested range
        def generate_range():
            with open(file_path, 'rb') as f:
                f.seek(byte_start)
                remaining = byte_end - byte_start + 1
                while remaining > 0:
                    chunk_size = min(1024, remaining)
                    data = f.read(chunk_size)
                    if not data:
                        break
                    remaining -= len(data)
                    yield data
        
        response = Response(
            generate_range(),
            206,
            headers={
                'Content-Range': f'bytes {byte_start}-{byte_end}/{file_size}',
                'Accept-Ranges': 'bytes',
                'Content-Length': str(byte_end - byte_start + 1),
                'Content-Type': 'video/mp4',
            }
        )
        return response
    
    # No range request, serve full file
    return Response(
        generate(),
        headers={
            'Content-Type': 'video/mp4',
            'Accept-Ranges': 'bytes',
            'Content-Length': str(file_size)
        }
    )

if __name__ == '__main__':
    # Download FFmpeg if not present
    if not download_ffmpeg():
        print("Failed to download FFmpeg. Please download it manually.")
        exit(1)
    
    print("Starting Spedup-Slowed-MV Web Interface...")
    print("Open your browser and go to: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)