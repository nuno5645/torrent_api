import json
import time
import zipfile
import io
import tempfile
import re
import os
from django.conf import settings
import webvtt

import requests
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import cache_page
from urllib.parse import unquote

from .RD import RealDebridAPI
from .torrent_api import TorrentAPI
from .opensubtitles import OpenSubtitlesClient


class HomePageView(View):
    @method_decorator(cache_page(60 * 15))  # Cache for 15 minutes
    def get(self, request):
        print("Homepage requested")
        
        # new_on_stremio = self.get_cached_data("new_on_stremio", "https://mdblist.com/lists/zeroq/new-on-stremio/json")
        new_on_stremio = self.get_cached_data("new_on_stremio", "https://mdblist.com/lists/linaspurinis/top-watched-movies-of-the-week/json")

        recommended_new = self.get_cached_data("recommended_new", "https://mdblist.com/lists/zeroq/recommended-new-on-stremio/json")
        weekend_box_office = self.get_cached_data("weekend_box_office", "https://mdblist.com/lists/zeroq/weekend-box-office/json")

        # Filter out non-movies from the data
        new_on_stremio = [item for item in new_on_stremio if item.get('mediatype') == 'movie']
        recommended_new = [item for item in recommended_new if item.get('mediatype') == 'movie']
        weekend_box_office = [item for item in weekend_box_office if item.get('mediatype') == 'movie']

        context = {
            'new_on_stremio': new_on_stremio,
            'recommended_new': recommended_new,
            'weekend_box_office': weekend_box_office
        }
        
        return render(request, 'homepage.html', context)

    def get_cached_data(self, cache_key, url):
        cached_data = cache.get(cache_key)
        if cached_data is None:
            print(f"Fetching fresh data for {cache_key}")
            data = self.fetch_and_process_data(url)
            cache.set(cache_key, data, 60 * 60)  # Cache for 1 hour
            return data
        print(f"Using cached data for {cache_key}")
        return cached_data

    def fetch_and_process_data(self, url):
        print("Fetching and processing data")
        response = requests.get(url)
        data = response.json()
        processed_data = []

        for item in data[:10]:  # Limit to 10 items
            imdb_id = item.get('imdb_id')
            if imdb_id:
                tmdb_info = self.fetch_tmdb_info(imdb_id)
                if tmdb_info:
                    processed_data.append({
                        'title': tmdb_info.get('title'),
                        'poster_path': tmdb_info.get('poster_path'),
                        'overview': tmdb_info.get('overview'),
                        'vote_average': tmdb_info.get('vote_average'),
                        'release_date': tmdb_info.get('release_date'),
                        'rank': item.get('rank'),
                        'mediatype': item.get('mediatype'),
                        'tmdb_id': tmdb_info.get('id')
                    })

        return processed_data

    def fetch_tmdb_info(self, imdb_id):
        print("Fetching TMDB info")
        api_key = "2480c2206d4661b89bf222cbc9c7f5ea"
        url = f"https://api.themoviedb.org/3/find/{imdb_id}?api_key={api_key}&language=en-US&external_source=imdb_id"
        response = requests.get(url)
        data = response.json()
        
        if data.get('movie_results'):
            return data['movie_results'][0]
        elif data.get('tv_results'):
            return data['tv_results'][0]
        return None

    @method_decorator(cache_page(60 * 15))  # Cache for 15 minutes
    def get_movie_data(self, request):
        print("Getting movie data")
        new_on_stremio = self.get_cached_data("new_on_stremio", "https://mdblist.com/lists/zeroq/new-on-stremio/json")
        recommended_new = self.get_cached_data("recommended_new", "https://mdblist.com/lists/zeroq/recommended-new-on-stremio/json")
        weekend_box_office = self.get_cached_data("weekend_box_office", "https://mdblist.com/lists/zeroq/weekend-box-office/json")

        # Filter out non-movies from the data
        new_on_stremio = [item for item in new_on_stremio if item.get('mediatype') == 'movie']
        recommended_new = [item for item in recommended_new if item.get('mediatype') == 'movie']
        weekend_box_office = [item for item in weekend_box_office if item.get('mediatype') == 'movie']

        print(new_on_stremio)
        print(recommended_new)
        print(weekend_box_office)
        return JsonResponse({
            'new_on_stremio': new_on_stremio,
            'recommended_new': recommended_new,
            'weekend_box_office': weekend_box_office
        })

class TrendingView(View):
    def get(self, request):
        api_key = "2480c2206d4661b89bf222cbc9c7f5ea"
        url = f"https://api.themoviedb.org/3/movie/popular?api_key={api_key}&language=en-US&page=1"

        response = requests.get(url)
        data = response.json()
        top_movies = data.get('results', [])[:20]

        movies_json = json.dumps(top_movies)
        movies_json = json.loads(movies_json)

        context = {
            'movies_json': movies_json
        }
        
        print(context)
        return render(request, 'dashboard_v2.html', context)

class LoginView(View):
    def get(self, request):
        form = AuthenticationForm()
        return render(request, 'login.html', {'form': form})

    def post(self, request):
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('homepage')  # Changed to redirect to homepage
        return render(request, 'login.html', {'form': form})

class MovieDetailView(View):
    def get(self, request, movie_id):
        api_key = "2480c2206d4661b89bf222cbc9c7f5ea"
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US&append_to_response=credits"

        response = requests.get(url)
        movie_data = response.json()

        context = {
            'movie': movie_data,
            'cast': movie_data.get('credits', {}).get('cast', [])[:5]  # Get first 5 cast members
        }

        return render(request, 'movie_detail_v2.html', context)
    
    def post(self, request, movie_id):
        movie_title = request.POST.get('movie_title')
        print(f"Received movie title: {movie_title}")
        
        subtitles = self.fetch_subtitles(movie_title)
        print(f"Subtitles: {subtitles}")
        # Step 1: Search for the video using TorrentAPI
        torrent_api = TorrentAPI()
        print("Searching for torrents...")
        search_results = torrent_api.search("piratebay", f"{movie_title}", limit=5)
        print(f"Search results: {search_results}")

        # Step 2: Process torrents with Real-Debrid
        rd_api = RealDebridAPI("B4YMPW225WYGYYOOSRNEHFQX33WWVQNY7IWCO54XTVSQYNYJEY3Q")

        for result in search_results.get('data', []):
            magnet_link = result.get('magnet')
            if not magnet_link:
                print("No magnet link found for this result.")
                continue

            print(f"Processing result: {result}")
            print(f"Found magnet link: {magnet_link}")

            try:
                # Adding torrent
                print("Adding torrent...")
                torrent_response = rd_api.add_magnet(magnet_link)
                print(f"Response from adding torrent: {torrent_response}")
                torrent_id = torrent_response['id']

                # Getting torrent info
                print("Getting torrent info...")
                file_info = rd_api.get_torrent_info(torrent_id)
                file_status = file_info['status']
                print(f"Initial file status: {file_status}")

                # Waiting for Magnet conversion
                print("Waiting for Magnet conversion...")
                while file_status == "magnet_conversion":
                    time.sleep(15)
                    file_info = rd_api.get_torrent_info(torrent_id)
                    file_status = file_info['status']
                    print(f"Current file status: {file_status}")

                # Selecting Files
                print("Conversion done. Selecting Files...")
                files = file_info['files']
                print(f"Total files available: {len(files)}")
                biggest_file = max(files, key=lambda x: x['bytes'])
                biggest_file_index = files.index(biggest_file)
                biggest_file_name = biggest_file['path']

                print(f"Torrenting now: {biggest_file_name}")
                print(f"Torrent ID: {torrent_id}")
                print(f"Biggest file index: {biggest_file_index + 1}")

                select_result = rd_api.select_files(torrent_id, biggest_file_index + 1)
                print(f"Select result: {select_result}")

                # Waiting for torrent to finish
                print("Waiting for torrent to finish...")
                file_info = rd_api.get_torrent_info(torrent_id)
                print(f"File info after waiting: {file_info}")
                # Get streaming link
                if file_info['status'] == 'downloaded':
                    streaming_link = file_info['links'][0]
                    unrestricted_link = rd_api.unrestrict_link(streaming_link)
                    print(f"Unrestricted link: {unrestricted_link}")

                    # Redirect to VideoStreamView with the streaming URL
                    return JsonResponse({
                        'redirect': reverse('video_stream', kwargs={'video_url': unrestricted_link['download']}) + 
                                    f'?title={movie_title}&subtitles={",".join([sub["url"] for sub in subtitles])}'
                    })

            except Exception as e:
                print(f"Error processing magnet link: {str(e)}")

        # If no successful result found
        return JsonResponse({'error': 'No suitable torrent found or error occurred'}, status=400)
    
    def fetch_subtitles(self, movie_title):
        client = OpenSubtitlesClient()
        movie_results = client.get_query_results(movie_title)
        
        if not movie_results:
            return []

        first_movie = movie_results[0]
        movie_id = first_movie.get('id')
        
        if not movie_id:
            return []

        subtitles = client.get_subtitles_by_id(movie_id)
        processed_subtitles = []

        for sub in subtitles:
            if sub.get('lang') in ['English', 'Portuguese'] and len(processed_subtitles) < 2:
                download_url = sub.get('download')
                if download_url:
                    try:
                        # Download the zip file
                        response = requests.get(download_url)
                        response.raise_for_status()

                        # Extract the subtitle file from the zip
                        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                            subtitle_file = z.namelist()[0]  # Assume the first file is the subtitle
                            subtitle_content = z.read(subtitle_file)

                        # Save SRT content to a temporary file
                        with tempfile.NamedTemporaryFile(mode='w+', suffix='.srt', delete=False, encoding='utf-8') as temp_srt:
                            temp_srt.write(subtitle_content.decode('utf-8'))
                            temp_srt_path = temp_srt.name

                        # Convert SRT to WebVTT
                        vtt = webvtt.from_srt(temp_srt_path)

                        # Save the WebVTT file
                        subtitle_dir = os.path.join(settings.MEDIA_ROOT, 'subtitles')
                        os.makedirs(subtitle_dir, exist_ok=True)
                        file_name = f"{movie_title.replace(' ', '_')}_{sub['lang']}.vtt"
                        file_path = os.path.join(subtitle_dir, file_name)
                        
                        vtt.save(file_path)

                        # Remove the temporary SRT file
                        os.unlink(temp_srt_path)

                        # Generate the URL for the subtitle file
                        subtitle_url = f"{settings.MEDIA_URL}subtitles/{file_name}"

                        processed_subtitles.append({
                            'lang': sub['lang'],
                            'url': subtitle_url
                        })
                        
                        print(f"\033[92mProcessed subtitle: {processed_subtitles[-1]}\033[0m")

                    except Exception as e:
                        print(f"Error processing subtitle: {str(e)}")
                        continue

        return processed_subtitles


class VideoStreamView(View):
    def get(self, request, video_url):
        try:
            response = requests.get(video_url, stream=True)
            response.raise_for_status()  # Raise an exception for bad status codes
        except requests.RequestException as e:
            return HttpResponse(f"Error fetching video: {str(e)}", status=500)

        # Get subtitles from URL parameters
        subtitle_urls = request.GET.get('subtitles', '').split(',')
        subtitles = [
            {'lang': 'English', 'url': unquote(url)} if i == 0 else {'lang': 'Portuguese', 'url': unquote(url)}
            for i, url in enumerate(subtitle_urls) if url
        ]

        # Pass the video URL and subtitles to the template
        context = {
            'stream_url': video_url,
            'subtitles': subtitles
        }
        return render(request, 'stream.html', context)

    def stream_video(self, response):
        for chunk in response.iter_content(chunk_size=8192):
            yield chunk