from flask import Flask, session, redirect, url_for, request, render_template_string
import os
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import FlaskSessionCacheHandler
import spotipy
import requests
from collections import Counter


"""
Minimal Flask-based concert recommender.

Flow:
1. User hits "/" and clicks "Log in with Spotify".
2. Spotify OAuth completes at "/callback".
3. We fetch the user's playlists and tracks, derive top artists,
   and then at "/concerts" we look up upcoming concerts for those artists
   near a user-provided city using an external concerts API (e.g. Ticketmaster).

NOTE: You must set your secrets via environment variables before running:
  - SPOTIPY_CLIENT_ID
  - SPOTIPY_CLIENT_SECRET
  - SPOTIPY_REDIRECT_URI   (e.g. http://localhost:5000/callback)
  - TICKETMASTER_API_KEY   (or another provider you use)
"""

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")


def _get_spotify_client() -> spotipy.Spotify:
    cache_handler = FlaskSessionCacheHandler(session)
    auth_manager = SpotifyOAuth(
        scope="playlist-read-private playlist-read-collaborative user-top-read",
        cache_handler=cache_handler,
        redirect_uri="http://127.0.0.1:5000/callback",
        show_dialog=True,
    )

    if request.args.get("code"):
        auth_manager.get_access_token(request.args.get("code"))

    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return None

    return spotipy.Spotify(auth_manager=auth_manager)


def get_user_playlists(sp: spotipy.Spotify):
    playlists = sp.current_user_playlists()
    all_playlists = []

    while playlists:
        for playlist in playlists["items"]:
            playlist_info = {
                "name": playlist["name"],
                "id": playlist["id"],
            }
            all_playlists.append(playlist_info)

        if playlists["next"]:
            playlists = sp.next(playlists)
        else:
            playlists = None

    return all_playlists


def get_playlist_tracks(sp: spotipy.Spotify, playlist_id: str):
    results = sp.playlist_tracks(playlist_id)
    tracks = []

    while results:
        for item in results["items"]:
            track = item["track"]
            if track:
                tracks.append(
                    {
                        "name": track["name"],
                        "artist": track["artists"][0]["name"],
                        "album": track["album"]["name"],
                        "id": track["id"],
                    }
                )

        if results["next"]:
            results = sp.next(results)
        else:
            results = None

    return tracks


def get_top_artists(sp: spotipy.Spotify, max_artists: int = 10, time_range: str = "medium_term"):
    """
    Use Spotify's Top Artists API to get the artists you actually listen to most.

    time_range options (per Spotify API):
      - "short_term"  ~4 weeks
      - "medium_term" ~6 months
      - "long_term"   several years
    """
    results = sp.current_user_top_artists(limit=max_artists, time_range=time_range)
    artists = [item["name"] for item in results.get("items", [])]
    return artists


def geocode_city(city: str):
    """
    Use OpenStreetMap Nominatim to convert a city name into latitude/longitude.
    """
    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": city, "format": "json", "limit": 1},
            headers={"User-Agent": "SuggestConcert/1.0 (academic project)"},
            timeout=5,
        )
        resp.raise_for_status()
        data = resp.json()
        if not data:
            return None, None
        return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception:
        return None, None


def get_upcoming_concerts(artists, lat: float, lon: float, radius_miles: int = 200):
    """
    Look up upcoming events for a list of artists in a given city.
    Uses Ticketmaster Discovery API as an example:
    https://developer.ticketmaster.com/products-and-docs/apis/discovery-api/v2/

    You must set TICKETMASTER_API_KEY in your environment.
    """
    api_key = os.environ.get("TICKETMASTER_API_KEY")
    if not api_key:
        return []

    concerts = []
    base_url = "https://app.ticketmaster.com/discovery/v2/events.json"

    for artist in artists:
        params = {
            "apikey": api_key,
            "keyword": artist,
            "latlong": f"{lat},{lon}",
            "radius": radius_miles,
            "unit": "miles",
            "size": 10,
        }
        try:
            resp = requests.get(base_url, params=params, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            events = data.get("_embedded", {}).get("events", [])
            for ev in events:
                concerts.append(
                    {
                        "artist": artist,
                        "name": ev.get("name"),
                        "date": ev.get("dates", {})
                        .get("start", {})
                        .get("localDate"),
                        "venue": (
                            ev.get("_embedded", {})
                            .get("venues", [{}])[0]
                            .get("name")
                        ),
                        "url": ev.get("url"),
                    }
                )
        except Exception:
            # For an academic project, you can log the error or count failures.
            continue

    return concerts


INDEX_HTML = """
<!doctype html>
<title>SuggestConcert</title>
<h1>SuggestConcert</h1>
{% if not logged_in %}
  <p>Log in with Spotify to analyze your playlists and get concert suggestions.</p>
  <a href="{{ url_for('login') }}">Log in with Spotify</a>
{% else %}
  <p>Logged in with Spotify.</p>
  <form action="{{ url_for('concerts') }}" method="get">
    <label>City:
      <input type="text" name="city" placeholder="e.g. Berlin" required>
    </label>
    <button type="submit">Find concerts within ~200 miles</button>
  </form>
{% endif %}
"""


CONCERTS_HTML = """
<!doctype html>
<title>Suggested Concerts</title>
<h1>Suggested Concerts near {{ city | e }}</h1>
<p>Based on your top Spotify artists: {{ artists|join(', ') }}</p>

{% if concerts %}
  <ul>
  {% for c in concerts %}
    <li>
      <strong>{{ c.artist }}</strong> — {{ c.name }}<br>
      {{ c.date }} at {{ c.venue }}<br>
      <a href="{{ c.url }}" target="_blank">Tickets</a>
    </li>
  {% endfor %}
  </ul>
{% else %}
  <p>No concerts found. Try another city or check your API key configuration.</p>
{% endif %}

<p><a href="{{ url_for('index') }}">Back</a></p>
"""


@app.route("/")
def index():
    logged_in = "token_info" in session
    return render_template_string(INDEX_HTML, logged_in=logged_in)


@app.route("/login")
def login():
    cache_handler = FlaskSessionCacheHandler(session)
    auth_manager = SpotifyOAuth(
        scope="playlist-read-private playlist-read-collaborative user-top-read",
        cache_handler=cache_handler,
        redirect_uri="http://127.0.0.1:5000/callback",
        show_dialog=True,
    )
    auth_url = auth_manager.get_authorize_url()
    return redirect(auth_url)


@app.route("/callback")
def callback():
    _ = _get_spotify_client()  # this will store the token in the session
    return redirect(url_for("index"))


@app.route("/concerts")
def concerts():
    city = request.args.get("city")
    if not city:
        return redirect(url_for("index"))

    sp = _get_spotify_client()
    if sp is None:
        return redirect(url_for("login"))

    # Use your real top artists from Spotify (last ~6 months by default)
    artists = get_top_artists(sp, max_artists=10, time_range="medium_term")
    lat, lon = geocode_city(city)
    if lat is None or lon is None:
        concerts = []
    else:
        concerts = get_upcoming_concerts(artists, lat=lat, lon=lon, radius_miles=200)
    return render_template_string(
        CONCERTS_HTML, city=city, artists=artists, concerts=concerts
    )


if __name__ == "__main__":
    # Run with: flask --app main run --debug  (or python main.py)
    app.run(debug=True)