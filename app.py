import os
import requests
import time
import threading
from flask import Flask

CLIENT_ID = os.getenv('TWITCH_CLIENT_ID')
CLIENT_SECRET = os.getenv('TWITCH_CLIENT_SECRET')
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
DISCORD_CHANNEL_ID = os.getenv('DISCORD_CHANNEL_ID')

STREAMERS = ['kronk0133']
CHECK_INTERVAL = 60
TWITCH_API_URL = "https://api.twitch.tv/helix/streams"
DISCORD_API_URL = f"https://discord.com/api/channels/{DISCORD_CHANNEL_ID}/messages"

app = Flask(__name__)

@app.route("/")
def home():
    """Basic route to confirm service is running."""
    return "Twitch Monitor Service is Running!"

def get_oauth_token():
    """Fetch OAuth token from Twitch."""
    url = "https://id.twitch.tv/oauth2/token"
    payload = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'client_credentials'
    }
    response = requests.post(url, data=payload)
    response.raise_for_status()
    return response.json()['access_token']

def check_stream_status(access_token, streamer):
    """Check if a Twitch stream is live."""
    headers = {
        'Client-ID': CLIENT_ID,
        'Authorization': f'Bearer {access_token}'
    }
    params = {'user_login': streamer}
    response = requests.get(TWITCH_API_URL, headers=headers, params=params)
    response.raise_for_status()
    data = response.json()
    if data['data']:
        return {
            'title': data['data'][0]['title'],
            'category': data['data'][0]['game_name'],
            'url': f"https://www.twitch.tv/{streamer}"
        }
    return None

def send_discord_message(message):
    """Send a message to Discord."""
    headers = {
        'Authorization': f'Bot {DISCORD_BOT_TOKEN}',
        'Content-Type': 'application/json'
    }
    payload = {'content': message}
    response = requests.post(DISCORD_API_URL, headers=headers, json=payload)
    response.raise_for_status()

def monitor_streams():
    """Monitor Twitch streams and notify on Discord."""
    access_token = get_oauth_token()
    notified_streams = set()

    while True:
        for streamer in STREAMERS:
            stream_info = check_stream_status(access_token, streamer)
            if stream_info and streamer not in notified_streams:
                message = (
                    f"**{streamer} is live!** 🎮\n\n"
                    f"**Title:** {stream_info['title']}\n\n"
                    f"**Category:** {stream_info['category']}\n\n"
                    f"[Watch now!]({stream_info['url']})"
                )
                send_discord_message(message)
                notified_streams.add(streamer)
            elif not stream_info:
                notified_streams.discard(streamer)
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    monitor_thread = threading.Thread(target=monitor_streams)
    monitor_thread.daemon = True
    monitor_thread.start()

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))