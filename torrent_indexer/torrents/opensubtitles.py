import requests
from bs4 import BeautifulSoup
from typing import List, Union
from datetime import datetime

class OpenSubtitlesClient:
    def __init__(self):
        self.OPENSUBTITLE_URL = "https://www.opensubtitles.org/en/search/sublanguageid-all"

    def get_api_info(self):

        server_location = self.fetch_server_location()

        return {
            "success": True,
            "playground": "http://82.180.131.185:5000",
            "endpoint": "https://github.com/Snowball-01/OpenSubtitles-API",
            "developer": "https://t.me/Snowball_Official",
            "date": datetime.now().strftime("%m/%d/%Y, %I:%M:%S %p"),
            "server": server_location,
            "version": "1.0.0",
        }

    def get_query_results(self, query: Union[str, None] = None):
        if query:
            return self.fetch_query(query)
        else:
            raise ValueError("Query not provided")

    def get_subtitles_by_id(self, id: Union[str, None] = None):
        if id:
            return self.fetch_subtitles(self.OPENSUBTITLE_URL + "/" + id)
        else:
            raise ValueError("ID not provided")

    def fetch_server_location(self):
        try:
            response = requests.get("http://ipinfo.io/json")
            data = response.json()
            return f"{data['city']}, {data['region']}, {data['country']}"
        except Exception as e:
            return "Location unknown"

    def fetch_subtitles(self, url: str) -> List[dict]:
        response = requests.get(url)
        text = response.text
        soup = BeautifulSoup(text, "lxml")
        data = []

        for el in soup.find_all("tr", onclick=True):
            td_elements = el.find_all("td")

            br_element = td_elements[0].find("br")
            br_text = br_element.next_sibling.text.strip() if br_element else "None"
            span_text = td_elements[0].find("span").text.strip() if td_elements[0].find("span") else ""

            lang = td_elements[1].find("a")["title"] if len(td_elements) > 1 else "Unknown"
            imdb = td_elements[7].find("a").text if len(td_elements) >= 7 else "None"

            raw_title = el.find("a").text.strip()
            clean_title = raw_title.replace("\n", "").replace("\\", "").replace('"', "")

            subtitle = {
                "id": el.find("a")["href"].split("/")[3],
                "title": clean_title,
                "description": br_text + span_text,
                "lang": lang,
                "sub_type": td_elements[4].find("span").text,
                "imdb": f"{imdb}/10",
                "url": f'https://www.opensubtitles.org{el.find("a")["href"]}',
                "download": f"https://www.opensubtitles.org/en/subtitleserve/sub/{el.find('a')['href'].split('/')[3]}",
            }
            data.append(subtitle)

        if not data:
            object = {
                "id": url.split("/")[-1],
                "title": soup.find("span", attrs={"itemprop": "name"}).text.strip(),
                "description": soup.find("h2").text.strip(),
                "lang": soup.find("span", attrs={"itemprop": "name"}).text.strip().split(" ")[-1],
                "sub_type": soup.find("h2").text.strip().split(" ")[-1],
                "imdb": soup.find("span", attrs={"itemprop": "ratingValue"}).text.strip() + "/" + "10",
                "url": url,
                "download": soup.find("a", attrs={"title": "Download"})["href"],
            }
            data.append(object)
        
        return data

    def fetch_query(self, query: str) -> List[dict]:
        url = f"https://www.opensubtitles.org/en/search2/sublanguageid-all/moviename-{query.replace(' ', '+')}"
        response = requests.get(url)
        text = response.text
        soup = BeautifulSoup(text, "lxml")
        data = []

        for el in soup.find_all("tr", onclick=True):
            raw_title = el.find("a").text.strip()
            clean_title = raw_title.replace("\n", "").replace("\\", "").replace('"', "")

            description_span = el.find("span", attrs={"class": "p"})
            description = "".join(description_span.stripped_strings) if description_span else ""

            query_result = {
                "id": el.get("onclick").split("/")[-1].replace("')", ""),
                "title": clean_title,
                "description": description,
                "image": f"https://{el.find('img')['src'][2:]}",
                "imdb": f'{el.find("td", attrs={"align": "center"}).text}/10',
                "url": f'https://www.opensubtitles.org{el.find("a")["href"]}',
            }
            data.append(query_result)
            
            # print(data)

        return data