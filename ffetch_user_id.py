import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import re

# Your Spotify API credentials
CLIENT_ID = '79b91ee5592049fd8d1f7fe678cedd75'
CLIENT_SECRET = 'bb4517d558854b15a05d6a87a7ab3698'

# Initialize Spotipy client
auth_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
sp = spotipy.Spotify(auth_manager=auth_manager)

# List of playlist URLs or IDs
playlist_inputs = [
    "https://open.spotify.com/playlist/5FJXhjdILmRA2z5bvz4nzf",
]

# Function to extract playlist ID from full URL or plain ID
def extract_playlist_id(url_or_id):
    match = re.search(r"playlist/([a-zA-Z0-9]+)", url_or_id)
    if match:
        return match.group(1)
    return url_or_id.strip()

# Main loop
if __name__ == "__main__":
    for item in playlist_inputs:
        playlist_id = extract_playlist_id(item)
        try:
            playlist_data = sp.playlist(playlist_id)
            owner_id = playlist_data['owner']['id']
            playlist_name = playlist_data['name']
            print(f"Playlist: '{playlist_name}' | ID: {playlist_id} | Owner (User ID): {owner_id}")
        except spotipy.exceptions.SpotifyException as e:
            print(f"[ERROR] Failed to fetch playlist {playlist_id}: {e}")
