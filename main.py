from flask import Flask, session, redirect, url_for, request
import os
from spotipy import Spotify, SpotifyClientCredentials   
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import FlaskSessionCacheHandler



app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)

client_id = '79b91ee5592049fd8d1f7fe678cedd75'
client_secret = 'bb4517d558854b15a05d6a87a7ab3698'
'''redirect_uri = 'http://localhost:5000/callback'
scope = 'playlist-read-private, streaming'''
# new comment in code 00:30 on 03/30
#new comment added on line 12 at 17:27 on 03/30
#added new comment to check if git desktop and github online is syncing properly 1:30 AM 04/02
cache_handler = FlaskSessionCacheHandler(session)
sp_auth = SpotifyOAuth(
    client_id=client_id,
    client_secret=client_secret
)

#create an instance of the spotify client that interscts with the spotify web api
sp = Spotify(auth_manager=sp_auth)

def search_songs(query: str) -> list[Song]:
    results = sp.search(query ,limit=50)

    songs = []
    for track in results["track"]["item"]:
        song = Song(
            title=track["title"]
            artist=track["artist"]
            album=track["album"]
            spotify_id=track["id"] #unique identifier for each song

        )
        song = song.append(song)
    return songs


if __name__ == '__main__':
    app.run(debug=True)