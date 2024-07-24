import os
import yt_dlp
import requests
import re
import subprocess

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
    command = f'ffmpeg -i "{video_file}" -vn -af "asetrate=44100*{pitch},aresample=44100" -acodec libmp3lame "{output_audio}"'
    os.system(command)

def get_audio_duration(audio_file):
    result = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', audio_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    return float(result.stdout)

def combine_video_audio_image(image_file, audio_file, output_video):
    try:
        audio_duration = get_audio_duration(audio_file)
        if image_file.endswith(".gif"):
            video_file = "looped_video.mp4"
            command = f'ffmpeg -stream_loop -1 -i "{image_file}" -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" -t {audio_duration} -pix_fmt yuv420p -c:v libx264 -r 30 "{video_file}"'
            os.system(command)
        else:
            video_file = image_file
        
        command = f'ffmpeg -i "{video_file}" -i "{audio_file}" -c:v copy -c:a aac -strict experimental -b:a 192k -shortest "{output_video}"'
        os.system(command)
        if image_file.endswith(".gif"):
            os.remove(video_file)
    except Exception as e:
        print(f"Error combining video and audio: {e}")

def download_random_gif(search_query, output_gif):
    TENOR_API_KEY = ''
    try:
        params = {
            'q': search_query,
            'key': TENOR_API_KEY,
            'limit': 1,
            'media_filter': 'minimal',
            'contentfilter': 'high'
        }
        response = requests.get('https://tenor.googleapis.com/v2/search', params=params)
        response.raise_for_status()
        data = response.json()
        if not data['results']:
            print("No GIFs found for the given query.")
            return None
        gif_url = data['results'][0]['media_formats']['gif']['url']
        gif_data = requests.get(gif_url).content
        with open(output_gif, 'wb') as f:
            f.write(gif_data)
        return output_gif
    except Exception as e:
        print(f"Error fetching GIF: {e}")
        return None

def process_single_url():
    video_url = input("Enter the video URL: ")
    search_query = input("Enter search query for GIF: ")

    speed_choice = input("\nAudio Options:\n0: Sped up\n1: Slowed down\nEnter audio option: ")
    if speed_choice not in ['0', '1']:
        print("Invalid choice. Please enter '0' for sped up audio or '1' for slowed down audio.")
        return
    speed_up = speed_choice == '0'

    gif_filename = "background.gif"
    if download_random_gif(search_query, gif_filename):
        video_info = yt_dlp.YoutubeDL().extract_info(video_url, download=False)
        video_title = re.sub(r'[\\/:*?"<>|]', '', video_info['title'].replace(" ", "_"))
        video_filename = "video.mp4"
        audio_filename = "audio.mp3"
        output_video = f"{video_title}.mp4"

        download_video(video_url, video_filename)
        extract_audio(video_filename, audio_filename, slow_down=not speed_up)
        combine_video_audio_image(gif_filename, audio_filename, output_video)

        os.remove(video_filename)
        os.remove(audio_filename)
        os.remove(gif_filename)

        if not os.path.exists("outputs"):
            os.makedirs("outputs")
        os.rename(output_video, os.path.join("outputs", output_video))

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
    process_single_url()


if __name__ == "__main__":
    main()
