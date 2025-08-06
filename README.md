
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

- Requires Tenor API for gifs, can be obtained at https://developers.google.com/tenor/guides/quickstart
<img width="1230" height="649" alt="image" src="https://github.com/user-attachments/assets/ec81df52-e65e-410f-917e-affa98052ce5" />

<details>
<summary>
examples
</summary>
       
https://github.com/user-attachments/assets/d4d58936-934e-412e-a609-5981f80cf296



https://github.com/user-attachments/assets/23602066-479c-420b-80c2-58bb3cd47210



https://github.com/user-attachments/assets/77bccb29-d06f-416b-a713-28c384195cb2



https://github.com/user-attachments/assets/b5974b81-b192-4cae-87da-a2fc966f7d56



https://github.com/user-attachments/assets/dab6bf93-6ef7-43f2-8a73-16cc0ffb1cec



https://github.com/user-attachments/assets/84ddf208-5ce8-4fc0-9508-e35ff0c13f1f


</details>

## Features
- Downloads from URLs of [supported websites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md) using *yt-dlp*
- Extract audio from videos using *ffmpeg*
- Fetch background images from multiple sources [(1)](https://pic.re/image), [(2)](https://api.thecatapi.com/v1/images/search), [(3)](https://random.imagecdn.app/v1/image?width=1920&height=1080&format=json)
- Combine audio and images to create videos using *ffmpeg*
- Each video has the title of the song in the bottom right corner
- Option to download multiple URLs from a list and apply the same options to all of them
- Option to download all the video URLs from a Youtube channel to a text file with restriction on max length while also skipping Youtube Shorts
- Uses GIFs as the background using the tenor v2 api
- User can input query for gif search.
- Allow the artist of the image/gif to be credited (gui-ffmpegexe.py only)
## How to run - clone and run using python flask or just run the .exe
1. clone repository  ```git clone https://github.com/sankeer28/Spedup-Slowed-MV.git```
2. open folder ```cd Spedup-Slowed-MV ```
3. install dependencies ```pip install -r requirements.txt``` 
4. run ```python app.py``` or ```python3 app.py```.
5. Open your browser and go to: http://localhost:5000

## Dependencies
Do  ```pip install -r requirements.txt``` If you run into errors try ```python3 -m pip install yt-dlp```
- will install FFmpeg.exe and FFprobe.exe

## Examples
<details>
<summary>
examples
</summary>

### Anime Slowed
https://github.com/sankeer28/Spedup-Slowed-MV/assets/112449287/22cac793-a34f-4453-9e81-9455060ac358

### Random Wallpaper Spedup
https://github.com/sankeer28/Spedup-Slowed-MV/assets/112449287/8f3a09bc-39cd-4f4f-980f-d2ad478c4d4f
### Pexels Query: City
https://github.com/sankeer28/Spedup-Slowed-MV/assets/112449287/956394c8-a519-4491-9e92-89409752e7e6


### Anime Spedup


https://github.com/sankeer28/Spedup-Slowed-MV/assets/112449287/ccd01716-2b52-4d7c-9d2d-22f962615652

https://github.com/sankeer28/Spedup-Slowed-MV/assets/112449287/9fd4c20c-1b03-4819-a5b3-8fdc4a67df2a

https://github.com/sankeer28/Spedup-Slowed-MV/assets/112449287/f5738fd4-90f4-4908-9b0a-3a9a15b5062d


### Cat Spedup
https://github.com/sankeer28/Spedup-Slowed-MV/assets/112449287/070be00a-1ff8-4d46-9662-2a6df9a0b4b7



</details>
