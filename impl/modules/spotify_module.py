import spotipy
import os
from spotipy import oauth2


class SpotifyModule:
    def __init__(self, config):
        self.invalid = False

        if (
            config is not None
            and "Spotify" in config
            and "client_id" in config["Spotify"]
            and "client_secret" in config["Spotify"]
            and "redirect_uri" in config["Spotify"]
        ):

            client_id = config["Spotify"]["client_id"]
            client_secret = config["Spotify"]["client_secret"]
            redirect_uri = config["Spotify"]["redirect_uri"]
            CACHE = ".spotipyoauthcache"
            SCOPE = "user-read-currently-playing, user-read-playback-state, user-modify-playback-state"
            sp_oauth = oauth2.SpotifyOAuth(
                client_id, client_secret, redirect_uri, scope=SCOPE, cache_path=CACHE
            )

            if (
                client_id is not ""
                and client_secret is not ""
                and redirect_uri is not ""
            ):
                try:
                    access_token = ""
                    token_info = sp_oauth.get_cached_token()
                    self.auth_manager = spotipy.SpotifyOAuth(scope=SCOPE)
                    if token_info:
                        print("Found cached token!")
                        access_token = token_info["access_token"]
                    else:
                        url = self.auth_manager.get_authorize_url()
                        code = sp_oauth.parse_response_code(url)
                        if code != url:
                            print(
                                "Found Spotify auth code in Request URL! Trying to get valid access token..."
                            )
                            token_info = sp_oauth.get_access_token(code)
                            access_token = token_info["access_token"]

                    if access_token:
                        print(
                            "Access token available! Trying to get user information..."
                        )
                        self.sp = spotipy.Spotify(access_token)

                    # os.environ["SPOTIPY_CLIENT_ID"] = client_id
                    # os.environ["SPOTIPY_CLIENT_SECRET"] = client_secret
                    # os.environ["SPOTIPY_REDIRECT_URI"] = redirect_uri

                    # scope = "user-read-currently-playing, user-read-playback-state, user-modify-playback-state"
                    # self.auth_manager = spotipy.SpotifyOAuth(scope=scope)
                    # print("Authenticated for spotipy", self.auth_manager)
                    # print(self.auth_manager.get_authorize_url())

                    # self.sp = spotipy.Spotify(
                    #     auth_manager=self.auth_manager, requests_timeout=10
                    # )

                    self.isPlaying = False
                except Exception as e:
                    print("[Spotify Module] error trying to authenticate", e)
                    self.invalid = True
            else:
                print("[Spotify Module] Empty Spotify client id or secret")
                self.invalid = True
        else:
            print("[Spotify Module] Missing config parameters")
            self.invalid = True

    def isInvalid(self):
        return self.invalid

    def getCurrentPlayback(self):
        if self.invalid:
            return None

        try:
            track = self.sp.current_user_playing_track()
            if track is not None:
                if track["item"] is None:
                    artist = None
                    title = None
                    art_url = None
                else:
                    artist = track["item"]["artists"][0]["name"]
                    if len(track["item"]["artists"]) >= 2:
                        artist = artist + ", " + track["item"]["artists"][1]["name"]
                    title = track["item"]["name"]
                    art_url = track["item"]["album"]["images"][0]["url"]
                self.isPlaying = track["is_playing"]
                return (
                    artist,
                    title,
                    art_url,
                    self.isPlaying,
                    track["progress_ms"],
                    track["item"]["duration_ms"],
                )
            else:
                print("[Spotify Module] Nothing in get user track")
                return None
        except Exception as e:
            print("[Spotify Module] Exception caught in current_user_playing_track")
            print(e)
            return None

    def resume_playback(self):
        if not self.invalid:
            try:
                self.sp.start_playback()
            except spotipy.exceptions.SpotifyException:
                print("no active, trying specific device")
                devices = self.sp.devices()
                if "devices" in devices and len(devices["devices"]) > 0:
                    try:
                        self.sp.start_playback(device_id=devices["devices"][0]["id"])
                    except Exception as e:
                        print(e)
            except Exception as e:
                print(e)

    def pause_playback(self):
        if not self.invalid:
            try:
                self.sp.pause_playback()
            except spotipy.exceptions.SpotifyException:
                print("problem pausing")
            except Exception as e:
                print(e)

    def next_track(self):
        if not self.invalid:
            try:
                self.sp.next_track()
            except spotipy.exceptions.SpotifyException:
                print("no active, trying specific device")
                devices = self.sp.devices()
                if "devices" in devices and len(devices["devices"]) > 0:
                    self.sp.next_track(device_id=devices["devices"][0]["id"])
            except Exception as e:
                print(e)

    def previous_track(self):
        if not self.invalid:
            try:
                self.sp.previous_track()
            except spotipy.exceptions.SpotifyException:
                print("no active, trying specific device")
                devices = self.sp.devices()
                if "devices" in devices and len(devices["devices"]) > 0:
                    self.sp.previous_track(device_id=devices["devices"][0]["id"])
            except Exception as e:
                print(e)

    def increase_volume(self):
        if not self.invalid and self.isPlaying:
            try:
                devices = self.sp.devices()
                curr_volume = devices["devices"][0]["volume_percent"]
                self.sp.volume(min(100, curr_volume + 5))
            except Exception as e:
                print(e)

    def decrease_volume(self):
        if not self.invalid and self.isPlaying:
            try:
                devices = self.sp.devices()
                curr_volume = devices["devices"][0]["volume_percent"]
                self.sp.volume(max(0, curr_volume - 5))
            except Exception as e:
                print(e)
