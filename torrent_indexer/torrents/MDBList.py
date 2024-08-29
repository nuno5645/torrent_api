import requests
import logging
from typing import Dict, List, Union, Optional

class MDBListAPI:
    """
    A class to interact with the MDBList API.
    """

    def __init__(self, api_key: str, base_url: str = "https://mdblist.com/api/"):
        """
        Initialize the MDBListAPI class.

        :param api_key: The API key for authentication.
        :param base_url: The base URL for the API (default: "https://mdblist.com/api/").
        """
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.params = {"apikey": self.api_key}

        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def _make_request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Dict:
        """
        Make a request to the API.

        :param method: The HTTP method (GET, POST, PUT, DELETE).
        :param endpoint: The API endpoint.
        :param params: Query parameters for the request.
        :param data: The data to send in the request body.
        :return: The JSON response from the API.
        """
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(method, url, params=params, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error making request to {url}: {str(e)}")
            return {"error": str(e)}

    def get_movie_info(self, imdb_id: str) -> Dict:
        """
        Get information about a specific movie.

        :param imdb_id: The IMDb ID of the movie.
        :return: A dictionary containing movie information.
        """
        return self._make_request("GET", "", params={"i": imdb_id})

    def search_movies(self, title: str, year: Optional[int] = None, score: Optional[int] = None) -> List[Dict]:
        """
        Search for movies by title.

        :param title: The title to search for.
        :param year: Optional year to limit the search.
        :param score: Optional score to limit the results.
        :return: A list of dictionaries containing movie information.
        """
        params = {"s": title, "m": "movie"}
        if year:
            params["y"] = year
        if score:
            params["sc"] = score
        return self._make_request("GET", "", params=params)

    def get_user_limits(self) -> Dict:
        """
        Get the user's limits.

        :return: A dictionary containing the user's limits.
        """
        return self._make_request("GET", "user/")

    def get_user_lists(self) -> List[Dict]:
        """
        Get all lists for the authenticated user.

        :return: A list of dictionaries containing list information.
        """
        return self._make_request("GET", "lists/user/")

    def get_list_info(self, list_id: int) -> Dict:
        """
        Get information about a specific list.

        :param list_id: The ID of the list.
        :return: A dictionary containing list information.
        """
        return self._make_request("GET", f"lists/{list_id}")

    def get_list_items(self, list_id: int) -> List[Dict]:
        """
        Get items in a specific list.

        :param list_id: The ID of the list.
        :return: A list of dictionaries containing list items.
        """
        return self._make_request("GET", f"lists/{list_id}/items")

    def add_items_to_list(self, list_id: int, movies: List[Dict], shows: List[Dict]) -> Dict:
        """
        Add items to a static list.

        :param list_id: The ID of the list.
        :param movies: A list of dictionaries containing movie information.
        :param shows: A list of dictionaries containing show information.
        :return: A dictionary containing the response from the API.
        """
        data = {"movies": movies, "shows": shows}
        return self._make_request("POST", f"lists/{list_id}/items/add", data=data)

    def remove_items_from_list(self, list_id: int, movies: List[Dict], shows: List[Dict]) -> Dict:
        """
        Remove items from a static list.

        :param list_id: The ID of the list.
        :param movies: A list of dictionaries containing movie information.
        :param shows: A list of dictionaries containing show information.
        :return: A dictionary containing the response from the API.
        """
        data = {"movies": movies, "shows": shows}
        return self._make_request("POST", f"lists/{list_id}/items/remove", data=data)

    def get_top_lists(self) -> List[Dict]:
        """
        Get top-100 lists by likes.

        :return: A list of dictionaries containing top lists information.
        """
        return self._make_request("GET", "lists/top")

    def search_lists(self, query: str) -> List[Dict]:
        """
        Search public lists by title.

        :param query: The list title to search for.
        :return: A list of dictionaries containing matching lists.
        """
        return self._make_request("GET", "lists/search", params={"s": query})

    def get_bulk_ratings(self, media_type: str, return_rating: str, ids: List[Union[int, str]], provider: str = "tmdb") -> Dict:
        """
        Get bulk ratings for multiple items.

        :param media_type: The media type ('movie' or 'show').
        :param return_rating: The type of rating to return.
        :param ids: A list of media IDs.
        :param provider: The ID provider ('tmdb' or 'imdb').
        :return: A dictionary containing the ratings.
        """
        data = {"ids": ids, "provider": provider}
        return self._make_request("POST", f"rating/{media_type}/{return_rating}", data=data)