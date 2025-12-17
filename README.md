## SuggestConcert – Spotify-based Concert Recommender

Given your Spotify playlists, SuggestConcert finds upcoming concerts near you for the artists you actually listen to.

### Features

- Log in with Spotify (OAuth) and read your playlists
- Aggregate your **top artists** based on how often they appear in your playlists
- Query a concerts API (Ticketmaster Discovery API example) for shows near a chosen city
- Simple web UI with Flask

### Setup

1. **Create a Spotify app**
   - Go to the Spotify Developer Dashboard and create an app.
   - Set the redirect URI to something like: `http://localhost:5000/callback`.

2. **Environment variables**

   Configure the following (e.g. in a `.env` file or via your shell/PowerShell):

   - `SPOTIPY_CLIENT_ID` – your Spotify client ID  
   - `SPOTIPY_CLIENT_SECRET` – your Spotify client secret  
   - `SPOTIPY_REDIRECT_URI` – e.g. `http://localhost:5000/callback`  
   - `FLASK_SECRET_KEY` – any random secret string for Flask sessions  
   - `TICKETMASTER_API_KEY` – API key for the Ticketmaster Discovery API (or adapt the code to another provider)

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the app**

   ```bash
   set FLASK_APP=main.py   # use $env:FLASK_APP = "main.py" on PowerShell
   flask run
   ```

   Then open `http://localhost:5000` in your browser.

### How it works (academic angle)

- Uses Spotify Web API via `spotipy` to:
  - authenticate the user,
  - retrieve playlists and tracks,
  - build a frequency distribution over artists.
- Selects top-N artists and queries a concerts/events API for each artist in the chosen city.
- You can extend this by:
  - modeling different “importance weights” for artists (e.g., recentness, playlist type),
  - evaluating coverage of recommended concerts vs. your listening history,
  - adding persistence with `sqlmodel` to store historical recommendations or user libraries.


