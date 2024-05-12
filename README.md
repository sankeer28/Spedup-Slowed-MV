
# Spedup/Slowed down Music Video Maker

A Python script that automates the creation of nightcore-style/sped-up videos or slowed-down videos by combining a wallpaper with audio extracted from URLs from supported websites like **YouTube**, **YouTube music**, and **Soundcloud**. This will work with other sites, full list can be found [here](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)
![carbon (5)](https://github.com/sankeer28/Spedup-Slowed-MV/assets/112449287/cfa45c33-9b6a-4dcb-ac27-1a640a8d92d7)

## If you run into any bugs, try old.py (does not have bulk url download feature and does not have the feature to download all videos from channel), or try old1.py (does not have the feature to download all videos from channel)
## Features

- Downloads from URLs of [supported websites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)
- Extract audio from videos
- Fetch background images from multiple sources
- Combine audio and images to create videos
- Each video has the title of the song in the bottom right corner
- Option to download multiple URLs from a list and apply the same options to all of them
- Option to download all the video URLs from a Youtube channel to a text file with restriction on max length while also skipping Youtube Shorts
## How to run
1. run ``` python main.py``` or ``` python3 main.py```.
2. Follow the prompts to enter the YouTube video URL, wallpaper choice, and speed preference.

3. The script will then download the video, extract audio, fetch the wallpaper, and combine them to create the nightcore-style video.

4. The final video will be saved in the `outputs` directory.

## Dependencies
Do  ```pip install -r requirements.txt``` If you run into errors try ```python3 -m pip install yt-dlp```
- Tested and working Python versions: Python 3.10.0,3.11.8, 3.12.3
  - On linux you can do ```sudo apt install python3.10``` then ``` python3 main.py```
- [ffmpeg](https://ffmpeg.org/): Add to system path. 
  - Linux (apt): 
  ```sudo apt install ffmpeg```
  - macOS (via homebrew): 
      ```brew install ffmpeg```
  - Windows: tutorials can be found on google like [this](https://www.wikihow.com/Install-FFmpeg-on-Windows): 


### [Replit Demo](https://replit.com/@SankeerthikanNi/Spedup-Slowed-MV)
This will be much slower compared to running locally if using the free version of replit
<details>
<summary>
Examples
</summary>

### Anime Slowed
https://github.com/sankeer28/Spedup-Slowed-MV/assets/112449287/22cac793-a34f-4453-9e81-9455060ac358

### Random Wallpaper Spedup
https://github.com/sankeer28/Spedup-Slowed-MV/assets/112449287/8f3a09bc-39cd-4f4f-980f-d2ad478c4d4f
### Pexels Query: City
https://github.com/sankeer28/Spedup-Slowed-MV/assets/112449287/956394c8-a519-4491-9e92-89409752e7e6


### Anime Spedup
https://github.com/sankeer28/Spedup-Slowed-MV/assets/112449287/f124f1a7-52ed-45db-88f0-7f0edf7a159a

https://github.com/sankeer28/Spedup-Slowed-MV/assets/112449287/9fd4c20c-1b03-4819-a5b3-8fdc4a67df2a

### Cat Spedup
https://github.com/sankeer28/Spedup-Slowed-MV/assets/112449287/070be00a-1ff8-4d46-9662-2a6df9a0b4b7



</details>
