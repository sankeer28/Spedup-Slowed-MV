
# Spedup/Slowed down Music Video Maker

A Python script that automates the creation of nightcore-style/sped-up videos or slowed-down videos by combining a wallpaper with audio extracted from YouTube videos.
![carbon (2)](https://github.com/sankeer28/Spedup-Slowed-MV/assets/112449287/4e0fa887-4631-4fe1-8c5b-c3c6e0b60f91)


2. Follow the prompts to enter the YouTube video URL, wallpaper choice, and speed preference.

3. The script will then download the video, extract audio, fetch the wallpaper, and combine them to create the nightcore-style video.

4. The final video will be saved in the `outputs` directory.

## Dependencies
Do  ```pip install -r requirements.txt```
- [Python 3.10.0](https://www.python.org/downloads/release/python-3100/): requires this specific version of Python
  - On linux you can do ```sudo apt install python3.10``` then ``` python3 main.py```
- [ffmpeg](https://ffmpeg.org/): Add to system path.
  - Linux (apt): 
  ```sudo apt install ffmpeg```
  - macOS (brew): 
      ```brew install ffmpeg```
  - Windows (chocolatey), google how to do it: 
      ```choco install ffmpeg```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request with any improvements or bug fixes.

