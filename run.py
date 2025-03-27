import os
import sys
import subprocess
import platform
import urllib.request
import zipfile
import shutil
from pydub import AudioSegment

def ensure_ffmpeg_installed():
    """Check if ffmpeg is available, and if not, download it (Windows only)"""
    try:
        # Try to run ffmpeg
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        if platform.system() != "Windows":
            print("FFmpeg is not installed. Please install it manually.")
            return False
            
        print("FFmpeg not found. Downloading...")
        try:
            # Create a temporary directory
            temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp")
            os.makedirs(temp_dir, exist_ok=True)
            
            # Download FFmpeg
            ffmpeg_url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
            zip_path = os.path.join(temp_dir, "ffmpeg.zip")
            urllib.request.urlretrieve(ffmpeg_url, zip_path)
            
            # Extract the zip
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Find the ffmpeg.exe file
            for root, dirs, files in os.walk(temp_dir):
                if "ffmpeg.exe" in files:
                    ffmpeg_path = os.path.join(root, "ffmpeg.exe")
                    # Copy to the current directory
                    shutil.copy(ffmpeg_path, os.path.dirname(os.path.abspath(__file__)))
                    break
            
            # Clean up
            shutil.rmtree(temp_dir)
            print("FFmpeg downloaded successfully.")
            return True
        except Exception as e:
            print(f"Error downloading FFmpeg: {e}")
            return False

def download_youtube_audio(url, output_folder="downloads"):
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    try:
        print(f"Attempting to access: {url}")
        
        # Use yt-dlp to download the audio with the video title as filename
        # %(title)s is a yt-dlp format specifier for the video title
        output_template = os.path.join(output_folder, "%(title)s.%(ext)s")
        
        # Determine the path to yt-dlp and ffmpeg
        yt_dlp_path = "yt-dlp"
        ffmpeg_path = "ffmpeg"
        
        # If we're running as a frozen executable, use the bundled binaries
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
            if platform.system() == "Windows":
                yt_dlp_path = os.path.join(base_path, "yt-dlp.exe")
                ffmpeg_path = os.path.join(base_path, "ffmpeg.exe")
            elif platform.system() == "Darwin":  # macOS
                yt_dlp_path = os.path.join(base_path, "yt-dlp")
                ffmpeg_path = os.path.join(base_path, "ffmpeg")
        
        command = [
            yt_dlp_path,
            "-f", "bestaudio",
            "-o", output_template,
            "--extract-audio",
            "--audio-format", "mp3",
            "--audio-quality", "0",  # 0 is best
            "--restrict-filenames",  # Replace spaces with underscores and remove special chars
            "--ffmpeg-location", os.path.dirname(ffmpeg_path),
            url
        ]
        
        print("Running download command...")
        result = subprocess.run(command, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error downloading: {result.stderr}")
            return None
        
        # Get the filename from the output
        # yt-dlp typically outputs a line like "[ExtractAudio] Destination: path/to/file.mp3"
        output_lines = result.stdout.split('\n')
        mp3_file = None
        
        for line in output_lines:
            if "[ExtractAudio] Destination:" in line:
                mp3_file = line.split("[ExtractAudio] Destination: ")[1].strip()
                break
                
        if not mp3_file or not os.path.exists(mp3_file):
            # Fallback: try to find any new MP3 file in the output folder
            mp3_files = [os.path.join(output_folder, f) for f in os.listdir(output_folder) 
                        if f.endswith('.mp3')]
            if mp3_files:
                mp3_file = mp3_files[-1]  # Take the most recently created file
            else:
                print("Download completed but MP3 file not found.")
                return None
            
        print(f"Downloaded and converted to MP3: {mp3_file}")
        return mp3_file

    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

if __name__ == "__main__":
    print("YouTube to MP3 Downloader")
    print("Python version:", sys.version)
    
    # Check for yt-dlp and ffmpeg
    if getattr(sys, 'frozen', False):
        # We're running as a bundled executable
        print("Running as bundled executable")
        # Make sure FFmpeg is available
        if not ensure_ffmpeg_installed():
            input("Press Enter to exit...")
            sys.exit(1)
    else:
        # We're running in a normal Python environment
        try:
            subprocess.run(["yt-dlp", "--version"], capture_output=True, text=True)
        except FileNotFoundError:
            print("yt-dlp is not installed. Installing now...")
            subprocess.run([sys.executable, "-m", "pip", "install", "yt-dlp"], check=True)
            print("yt-dlp installed successfully.")
        
        if not ensure_ffmpeg_installed():
            input("Press Enter to exit...")
            sys.exit(1)
    
    print("Make sure you have ffmpeg installed (brew install ffmpeg)")
    
    youtube_url = input("Enter YouTube video URL: ")
    result = download_youtube_audio(youtube_url)
    
    if result:
        print(f"Success! File saved to: {result}")
    else:
        print("Download failed. Please check the errors above.")
    
    # Keep the window open until the user presses Enter
    input("Press Enter to exit...")
