import os
import yt_dlp
import requests
import re

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
        else:
            print("Invalid API choice.")
            return

        image_data = requests.get(image_url).content
        with open(output_image, 'wb') as f:
            f.write(image_data)
    except Exception as e:
        print(f"Error fetching image: {e}")

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

def combine_video_audio_image(image_file, audio_file, output_video, video_title, api_choice):
    try:
        resized_image_file = "resized_" + image_file
        resize_command = f'ffmpeg -i "{image_file}" -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" "{resized_image_file}" -y'
        os.system(resize_command)
        text = re.sub(r'\(.*?\)', '', re.sub(r'[\\/:*?"<>|]', '', video_title.replace("_", " ").replace("nightcore", "").replace("(Official Audio)", "").replace("slowed down", "").replace("(Official Lyric Video)", "").replace("(Lyrics)", "").replace("(Official Video)", "").replace("(Official Music Video)", "").replace("(Official Visualizer)", "").strip()))
        text_command = f'ffmpeg -loop 1 -i "{resized_image_file}" -vf "drawtext=text=\'{text}\':x=w-tw-10:y=h-th-10:fontsize=40:fontcolor=black:shadowcolor=white:shadowx=2:shadowy=2" -r 30 "{image_file}_with_text.jpg"'
        os.system(text_command)
        command = f'ffmpeg -loop 1 -i "{image_file}_with_text.jpg" -i "{audio_file}" -c:v libx264 -c:a aac -strict experimental -b:a 192k -shortest "{output_video}"'
        os.system(command)
        os.remove(resized_image_file)
        os.remove(f"{image_file}_with_text.jpg")
    except Exception as e:
        print(f"Error combining video and audio: {e}")
        download_cat_image(image_file, api_choice)
        combine_video_audio_image(image_file, audio_file, output_video, video_title, api_choice)

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
    import shlex
    playlist_url = input("Enter the playlist URL: ")
    command = f'yt-dlp --flat-playlist  --match-filter "original_url!*=/shorts/ & url!*=/shorts/ & duration<360" --print-to-file url list.txt {playlist_url}'
    yt_dlp.main(shlex.split(command))


def process_single_url():
    video_url = input("Enter the video URL: ")
    api_choice = input("Background Options:\n0: Anime wallpaper\n1: Cat wallpaper\n2: Random wallpaper\n3: Pexels image\nEnter background option: ")

    if api_choice not in ['0', '1', '2', '3']:
        print("Invalid choice. Please enter '0' for anime wallpaper, '1' for cat wallpaper, '2' for random wallpaper, or '3' for Pexels image.")
        return
    
    search_query = None
    if api_choice == '3':
        search_query = input("Enter search query for Pexels image: ")
    
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

    api_choice = input("Background Options:\n0: Anime wallpaper\n1: Cat wallpaper\n2: Random wallpaper\n3: Pexels image\nEnter background option: ")

    if api_choice not in ['0', '1', '2', '3']:
        print("Invalid choice. Please enter '0' for anime wallpaper, '1' for cat wallpaper, '2' for random wallpaper, or '3' for Pexels image.")
        return
    
    search_query = None
    if api_choice == '3':
        search_query = input("Enter search query for Pexels image: ")
        
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
    
    video_filename = "video.mp4"
    audio_filename = "audio.mp3"
    image_filename = "cat_image.jpg"
    output_video = f"{video_title}.mp4"

    download_video(video_url, video_filename)
    
    extract_audio(video_filename, audio_filename, slow_down=not speed_up)
    
    if api_choice == "3":
        download_pexels_image(image_filename, search_query)
    else:
        download_cat_image(image_filename, api_choice)
    
    combine_video_audio_image(image_filename, audio_filename, output_video, video_title, api_choice)

    os.remove(video_filename)
    os.remove(audio_filename)
    os.remove(image_filename)
    
    if not os.path.exists("outputs"):
        os.makedirs("outputs")
    os.rename(output_video, os.path.join("outputs", output_video))

if __name__ == "__main__":
    main()
