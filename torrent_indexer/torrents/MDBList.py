import requests
import json

class MDBListAPI:
    BASE_URL = "https://mdblist.com/api/"
    
    def __init__(self, api_key):
        self.api_key = api_key
    
    def _make_request(self, endpoint, params=None):
        url = self.BASE_URL + endpoint
        params = params or {}
        params['apikey'] = self.api_key
        response = requests.get(url, params=params)
        print(response)
        
        return response.json()
    
    def get_movie_info(self, imdb_id):
        return self._make_request("", params={"i": imdb_id})
    
    def search_movies(self, title, year=None, score=None, limit=50):
        params = {
            "s": title,
            "l": limit
        }
        if year:
            params["y"] = year
        if score:
            params["sc"] = score
        return self._make_request("", params=params)
    
    def get_user_limits(self):
        return self._make_request("user/")
    
    def get_user_lists(self):
        return self._make_request("lists/user/")
    
    def get_list_info(self, list_id):
        return self._make_request(f"lists/{list_id}")
    
    def get_list_items(self, list_id):
        return self._make_request(f"lists/{list_id}/items")
    
    def add_items_to_list(self, list_id, movies=None, shows=None):
        url = f"{self.BASE_URL}lists/{list_id}/items/add"
        data = {"movies": movies or [], "shows": shows or []}
        response = requests.post(url, params={"apikey": self.api_key}, json=data)
        return response.json()
    
    def remove_items_from_list(self, list_id, movies=None, shows=None):
        url = f"{self.BASE_URL}lists/{list_id}/items/remove"
        data = {"movies": movies or [], "shows": shows or []}
        response = requests.post(url, params={"apikey": self.api_key}, json=data)
        return response.json()
    
    def get_top_lists(self):
        return self._make_request("lists/top")
    
    def search_lists(self, query):
        return self._make_request("lists/search", params={"s": query})
    
    def get_bulk_ratings(self, media_type, return_rating, ids, provider="tmdb"):
        url = f"{self.BASE_URL}rating/{media_type}/{return_rating}"
        data = {"ids": ids, "provider": provider}
        response = requests.post(url, params={"apikey": self.api_key}, json=data)
        return response.json()

# Usage example:
# api = MDBListAPI("your_api_key_here")
# movie_info = api.get_movie_info("tt0073195")
# print(movie_info)