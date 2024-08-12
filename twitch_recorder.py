import time
import json
import subprocess
import os
import requests
from bs4 import BeautifulSoup

def load_config(config_file):
    with open(config_file, 'r') as f:
        return json.load(f)

def is_streamer_live(channel_name):
    # Get the HTML content of the streamer's Twitch page
    url = f'https://www.twitch.tv/{channel_name}'
    response = requests.get(url)
    contents = response.content.decode('utf-8')
    
    # Check if the streamer is live
    is_live = 'isLiveBroadcast' in contents
    
    # Parse the HTML using BeautifulSoup
    soup = BeautifulSoup(contents, 'html.parser')
    
    # Extract the stream title from the meta tag or another relevant tag
    stream_title = None
    if is_live:
        meta_tag = soup.find('meta', {'property': 'og:description'})
        if meta_tag:
            stream_title = meta_tag.get('content')
    
    return is_live, stream_title

def download_stream(channel_name, stream_title, output_dir):
    output_directory = os.path.join(output_dir, channel_name)
    os.makedirs(output_directory, exist_ok=True)

    filename = f"{stream_title}_{time.strftime('%Y%m%d_%H%M%S')}.mp4"
    output_path = os.path.join(output_directory, filename)
    
    command = [
        'streamlink', '--twitch-disable-ads', f'twitch.tv/{channel_name}', 'best',
        '-o', output_path
    ]
    print(command)
    
    try:
        process = subprocess.Popen(command)
        process.communicate()  # Wait for the download to finish
        
        # Call FFmpeg to compress or convert the video after download
        compressed_output_path = os.path.join(output_directory, f"compressed_{filename}")
        compress_video(output_path, compressed_output_path)
        
        return compressed_output_path
    except Exception as e:
        print(f"An error occurred: {e}")

def compress_video(input_file, output_file):
    command = [
        'ffmpeg', '-i', input_file, '-vcodec', 'libx265', '-crf', '28', output_file
    ]
    try:
        subprocess.run(command, check=True)
        print(f"Video compressed successfully to {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred during compression: {e}")
  
def monitor_streamers(config):
    currently_downloading = set()
    
    while True:
        for channel in config['channels']:
            # Skip if already downloading this channel
            if channel in currently_downloading:
                print(f"Already downloading {channel}. Skipping this check.")
                continue

            is_live, stream_title = is_streamer_live(channel)
            if is_live:
                print(f"{channel} is live! Starting download.")
                currently_downloading.add(channel)
                process = download_stream(channel, stream_title, config['output_directory'])
                
                # Remove from currently_downloading when the process finishes
                process.communicate()  # Wait for the download to finish
                currently_downloading.remove(channel)
            else:
                print(f"{channel} is not live. Checking again in {config['check_interval']} seconds.")
                
        time.sleep(config['check_interval'])

if __name__ == "__main__":
    config = load_config("streamers.json")
    monitor_streamers(config)