from flask import Flask
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)

client_id = '79b91ee5592049fd8d1f7fe678cedd75'
client_secret = 'bb4517d558854b15a05d6a87a7ab3698'
redirect_uri = 'http://localhost:5000/callback'
scope = 'playlist-read-private'
# new comment in code 00:30 on 03/30
#new comment added on line 12 at 17:27 on 03/30
if __name__ == '__main__':
    app.run(debug=True)