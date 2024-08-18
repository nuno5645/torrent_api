from typing import Dict, List, Optional, Any
import requests


class TorrentAPI:
    BASE_URL: str = "http://localhost:8009/api/v1"

    def __init__(self) -> None:
        self.session: requests.Session = requests.Session()

    def get_supported_sites(self) -> List[str]:
        """Get list of supported torrent sites"""
        response: requests.Response = self.session.get(f"{self.BASE_URL}/sites")
        return response.json()

    def search(self, site: str, query: str, limit: Optional[int] = None, page: int = 1) -> Dict[str, Any]:
        """Search for torrents on a specific site"""
        params: Dict[str, Any] = {
            "site": site,
            "query": query,
            "limit": limit,
            "page": page
        }
        response: requests.Response = self.session.get(f"{self.BASE_URL}/search", params=params)
        return response.json()

    def get_trending(self, site: str, limit: Optional[int] = None, category: Optional[str] = None, page: int = 1) -> Dict[str, Any]:
        """Get trending torrents from a site"""
        params: Dict[str, Any] = {
            "site": site,
            "limit": limit,
            "category": category,
            "page": page
        }
        response: requests.Response = self.session.get(f"{self.BASE_URL}/trending", params=params)
        return response.json()

    def get_recent(self, site: str, limit: Optional[int] = None, category: Optional[str] = None, page: int = 1) -> Dict[str, Any]:
        """Get recent torrents from a site"""
        params: Dict[str, Any] = {
            "site": site,
            "limit": limit,
            "category": category,
            "page": page
        }
        response: requests.Response = self.session.get(f"{self.BASE_URL}/recent", params=params)
        return response.json()

    def search_by_category(self, site: str, query: str, category: str, limit: Optional[int] = None, page: int = 1) -> Dict[str, Any]:
        """Search torrents by category on a site"""
        params: Dict[str, Any] = {
            "site": site,
            "query": query,
            "category": category,
            "limit": limit,
            "page": page
        }
        response: requests.Response = self.session.get(f"{self.BASE_URL}/category", params=params)
        return response.json()

    def search_all_sites(self, query: str, limit: Optional[int] = None) -> Dict[str, Any]:
        """Search for torrents across all supported sites"""
        params: Dict[str, Any] = {
            "query": query,
            "limit": limit
        }
        response: requests.Response = self.session.get(f"{self.BASE_URL}/all/search", params=params)
        return response.json()

    def get_trending_all_sites(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """Get trending torrents from all supported sites"""
        params: Dict[str, Any] = {
            "limit": limit
        }
        response: requests.Response = self.session.get(f"{self.BASE_URL}/all/trending", params=params)
        return response.json()

    def get_recent_all_sites(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """Get recent torrents from all supported sites"""
        params: Dict[str, Any] = {
            "limit": limit
        }
        response: requests.Response = self.session.get(f"{self.BASE_URL}/all/recent", params=params)
        return response.json()