
# Spedup/Slowed down Music Video Maker
```ruby
       _____                __               _____ __                       __   __  ____    __
      / ___/____  ___  ____/ /_  ______     / ___// /___ _      _____  ____/ /  /  |/  / |  / /
      \__ \/ __ \/ _ \/ __  / / / / __ \    \__ \/ / __ \ | /| / / _ \/ __  /  / /|_/ /| | / / 
     ___/ / /_/ /  __/ /_/ / /_/ / /_/ /   ___/ / / /_/ / |/ |/ /  __/ /_/ /  / /  / / | |/ /
    /____/ .___/\___/\__,_/\__,_/ .___/   /____/_/\____/|__/|__/\___/\__,_/  /_/  /_/  |___/
        /_/                    /_/ 
```
### A Python script that automates the creation of nightcore-style/sped-up videos or slowed-down videos by combining a wallpaper with audio extracted from URLs from supported websites like **YouTube**, **YouTube music**, and **Soundcloud**. 
### This script will work with other sites, full list can be found [here](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md).
![gif](https://github.com/sankeer28/Spedup-Slowed-MV/assets/112449287/52e46e16-7421-42f0-bd5e-ac603290e9af)
## Features
- Downloads from URLs of [supported websites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md) using *yt-dlp*
- Extract audio from videos using *ffmpeg*
- Fetch background images from multiple sources [(1)](https://pic.re/image), [(2)](https://api.thecatapi.com/v1/images/search), [(3)](https://random.imagecdn.app/v1/image?width=1920&height=1080&format=json)
- Combine audio and images to create videos using *ffmpeg*
- Each video has the title of the song in the bottom right corner
- Option to download multiple URLs from a list and apply the same options to all of them
- Option to download all the video URLs from a Youtube channel to a text file with restriction on max length while also skipping Youtube Shorts
## How to run
1. clone repository  ```git clone https://github.com/sankeer28/Spedup-Slowed-MV.git```
2. open folder ```cd Spedup-Slowed-MV ```
3. install dependencies ```pip install -r requirements.txt``` and ffmpeg
4. run ```python main.py``` or ```python3 main.py```.
5. Follow the prompts to enter the YouTube video URL, wallpaper choice, and speed preference.
6. The script will then download the video, extract audio, fetch the wallpaper, and combine them to create the nightcore-style video.
7. The final video will be saved in the `outputs` directory.
## Dependencies
Do  ```pip install -r requirements.txt``` If you run into errors try ```python3 -m pip install yt-dlp```
- Tested and working Python versions: Python 3.10.0,3.11.8, 3.12.3
  - On linux you can do ```sudo apt install python3.10``` then ```python3 main.py```
- [ffmpeg](https://ffmpeg.org/): Add to system path. 
  - Linux (apt): 
  ```sudo apt install ffmpeg```
  - macOS (via homebrew): 
      ```brew install ffmpeg```
  - Windows: tutorials can be found on Google like [this](https://www.wikihow.com/Install-FFmpeg-on-Windows): 

## Older Versions: 
- old.py: does not have bulk url download feature and does not have the feature to download all videos from channel
- old1.py: does not have the feature to download all videos from channel
### [Replit Demo](https://replit.com/@SankeerthikanNi/Spedup-Slowed-MV)
This will be much slower compared to running locally if using the free version of Replit
## Examples

<details>
<summary>
expand
</summary>

### Anime Slowed
https://github.com/sankeer28/Spedup-Slowed-MV/assets/112449287/22cac793-a34f-4453-9e81-9455060ac358

### Random Wallpaper Spedup
https://github.com/sankeer28/Spedup-Slowed-MV/assets/112449287/8f3a09bc-39cd-4f4f-980f-d2ad478c4d4f
### Pexels Query: City
https://github.com/sankeer28/Spedup-Slowed-MV/assets/112449287/956394c8-a519-4491-9e92-89409752e7e6


### Anime Spedup

https://github.com/sankeer28/Spedup-Slowed-MV/assets/112449287/6c7c3915-1930-4ae4-b4e1-c806084e507c

https://github.com/sankeer28/Spedup-Slowed-MV/assets/112449287/9fd4c20c-1b03-4819-a5b3-8fdc4a67df2a

### Cat Spedup
https://github.com/sankeer28/Spedup-Slowed-MV/assets/112449287/070be00a-1ff8-4d46-9662-2a6df9a0b4b7



</details>
