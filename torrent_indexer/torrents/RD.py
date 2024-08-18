import requests


class RealDebridAPI:
    BASE_URL = "https://api.real-debrid.com/rest/1.0"

    def __init__(self, access_token):
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    def _make_request(self, method, endpoint, params=None, data=None):
        url = f"{self.BASE_URL}{endpoint}"
        response = requests.request(method, url, headers=self.headers, params=params, data=data)
        return response.json() if response.content else None

    # User methods
    def get_user_info(self):
        return self._make_request("GET", "/user")

    # Unrestrict methods
    def check_link(self, link, password=None):
        data = {"link": link, "password": password}
        return self._make_request("POST", "/unrestrict/check", data=data)

    def unrestrict_link(self, link, password=None, remote=0):
        data = {"link": link, "password": password, "remote": remote}
        return self._make_request("POST", "/unrestrict/link", data=data)

    def unrestrict_folder(self, link):
        data = {"link": link}
        return self._make_request("POST", "/unrestrict/folder", data=data)

    # Traffic methods
    def get_traffic(self):
        return self._make_request("GET", "/traffic")

    def get_traffic_details(self, start=None, end=None):
        params = {"start": start, "end": end}
        return self._make_request("GET", "/traffic/details", params=params)

    # Streaming methods
    def get_streaming_transcode(self, id):
        return self._make_request("GET", f"/streaming/transcode/{id}")

    def get_streaming_media_info(self, id):
        return self._make_request("GET", f"/streaming/mediaInfos/{id}")

    # Downloads methods
    def get_downloads(self, offset=None, page=None, limit=None):
        params = {"offset": offset, "page": page, "limit": limit}
        return self._make_request("GET", "/downloads", params=params)

    def delete_download(self, id):
        return self._make_request("DELETE", f"/downloads/delete/{id}")

    # Torrents methods
    def get_torrents(self, offset=None, page=None, limit=None, filter=None):
        params = {"offset": offset, "page": page, "limit": limit, "filter": filter}
        return self._make_request("GET", "/torrents", params=params)

    def get_torrent_info(self, id):
        return self._make_request("GET", f"/torrents/info/{id}")

    def get_torrent_instant_availability(self, hash):
        return self._make_request("GET", f"/torrents/instantAvailability/{hash}")

    def get_active_torrents_count(self):
        return self._make_request("GET", "/torrents/activeCount")

    def get_available_hosts(self):
        return self._make_request("GET", "/torrents/availableHosts")

    def add_torrent(self, torrent_file, host=None):
        files = {"file": torrent_file}
        data = {"host": host} if host else {}
        return self._make_request("PUT", "/torrents/addTorrent", data=data, files=files)

    def add_magnet(self, magnet, host=None):
        data = {"magnet": magnet}
        return self._make_request("POST", "/torrents/addMagnet", data=data)

    def select_files(self, id, files):
        data = {"files": files}
        return self._make_request("POST", f"/torrents/selectFiles/{id}", data=data)

    def delete_torrent(self, id):
        return self._make_request("DELETE", f"/torrents/delete/{id}")

    # Hosts methods
    def get_hosts(self):
        return self._make_request("GET", "/hosts")

    def get_hosts_status(self):
        return self._make_request("GET", "/hosts/status")

    def get_hosts_regex(self):
        return self._make_request("GET", "/hosts/regex")

    def get_hosts_regex_folder(self):
        return self._make_request("GET", "/hosts/regexFolder")

    def get_hosts_domains(self):
        return self._make_request("GET", "/hosts/domains")

    # Settings methods
    def get_settings(self):
        return self._make_request("GET", "/settings")

    def update_settings(self, setting_name, setting_value):
        data = {"setting_name": setting_name, "setting_value": setting_value}
        return self._make_request("POST", "/settings/update", data=data)

    def convert_points(self):
        return self._make_request("POST", "/settings/convertPoints")

    def change_password(self):
        return self._make_request("POST", "/settings/changePassword")

    def upload_avatar(self, avatar_file):
        files = {"avatar": avatar_file}
        return self._make_request("PUT", "/settings/avatarFile", files=files)

    def delete_avatar(self):
        return self._make_request("DELETE", "/settings/avatarDelete")