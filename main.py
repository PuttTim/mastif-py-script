import firebase_admin
from firebase_admin import credentials, firestore
import requests
import re

# Credentials for the various services
cred = credentials.Certificate('!!Certificate here!!')
CLIENT_ID = '!!Client ID Here!!'
CLIENT_SECRET = '!!Client Secret Here!!'
token = '!!Token here!!'
headers = {'Authorization': 'Bearer {token}'.format(token=token)}

# Firestore database initialization
default_app = firebase_admin.initialize_app(cred)
db = firestore.client()


song_list = []


class Song(object):
    def __init__(self, artist, cover, link, title):
        self.artist = artist
        self.cover = cover
        self.link = link
        self.title = title

    def to_dict(self):
        dest = {"artist": self.artist, "cover": self.cover, "link": self.link, "title": self.title}

        if self.artist:
            dest["artist"] = self.artist

        if self.cover:
            dest["cover"] = self.cover

        if self.link:
            dest["link"] = self.link

        if self.title:
            dest["title"] = self.title
        return dest

    def from_dict(source):
        song = Song(source[u'artist'], source[u'cover'], source[u'link'], source['title'])

        if u'artist' in source:
            song.artist = source[u'cover']

        if u'cover' in source:
            song.cover = source[u'cover']

        if u'link' in source:
            song.link = source[u'link']

        if u'title' in source:
            song.title = source[u'title']
        return song


def get_all_songs():
    docs = db.collection('songs-library').stream()

    for doc in docs:
        song = Song.from_dict(doc.to_dict())
        print(song.title, song.artist, song.cover, song.link)


def request_token():
    token_response = requests.post(
        'https://accounts.spotify.com/api/token', {
            'grant_type': 'client_credentials',
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
        })
    token_data = token_response.json()
    token = token_data['access_token']
    print(token)
    headers = {'Authorization': 'Bearer {token}'.format(token=token)}
    fetch_response(headers)


def fetch_response(headers):
    response = requests.get(
        f'https://api.spotify.com/v1/playlists/{id}/tracks?market=SG&fields=items(track(album(images)%2C%20artists(name)%2C%20name%2C%20preview_url))',
        headers=headers)
    if response.status_code == 401:
        request_token()
    else:
        fetch_playlist(response)


def fetch_playlist(response):
    json = response.json()

    for item in json['items']:
        artist = item['track']['artists'][0]['name']
        cover = item['track']['album']['images'][0]['url']
        link = item['track']['preview_url']
        title = item['track']['name']
        if (artist == None) or (cover == None) or (link == None) or (title == None):
            print(
                f"Skipped {artist}, {title} \n\n")
        else:
            song = Song(artist=artist, cover=cover, link=link, title=title)
            song_list.append(song)
            print(
                f"Artist: {artist}\nCover: {cover}\nLink: {link}\nTitle: {title} \n \n")


def add_to_firestore():
    docs = db.collection(u'songs-library').stream()
    db_song = []
    for doc in docs:
        db_song.append(Song.from_dict(doc.to_dict()))
    for i in range(len(song_list)):
        for j in range(len(db_song)):
            # print(f"Loop match with {db_song[j].title} and {song_list[i].title}")
            if db_song[j].title == song_list[i].title:
                print(
                    f'Skipping: \nArtist: {song_list[i].artist}\nCover: {song_list[i].cover}\nLink: {song_list[i].link}\nTitle: {song_list[i].title} \n \n')
                break
        else:
            print(
                f"Adding: \nArtist: {song_list[i].artist}\nCover: {song_list[i].cover}\nLink: {song_list[i].link}\nTitle: {song_list[i].title} \n \n")
            db.collection(u'songs-library').add(song_list[i].to_dict())

spotify_input = str(input("Please enter your playlist here: "))

if re.sub(r'https://open.spotify.com/playlist/', '', spotify_input) == None:
    id = spotify_input
else:
    id = re.sub(r'https://open.spotify.com/playlist/',
                '', spotify_input).partition('?si=')[0]

fetch_response(headers)

if input("Upload to Firestore? (Preview your songs) [Y/N] ") == "Y":
    add_to_firestore()
    print("\n \nDone")

else:
    print("Will not add to Firestore, byebye!")
