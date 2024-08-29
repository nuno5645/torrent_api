# Python standard library imports
import json
import time
import zipfile
import io
import tempfile
import re
import os
from datetime import datetime, timedelta
from urllib.parse import unquote

# Django imports
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import cache_page

from django.views import View
from django.http import JsonResponse
from django.db.models import Q
from .models import Movie
# Third-party imports
import requests
import webvtt

# Local imports
from .RD import RealDebridAPI
from .torrent_api import TorrentAPI
from .opensubtitles import OpenSubtitlesClient
from .models import StreamingList, Movie, StreamingListMovie

from django.views import View
from django.shortcuts import render
from .models import StreamingList, Movie, StreamingListMovie
import requests
from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from allauth.account.views import LoginView, SignupView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator


    # (Previous imports remain the same)

# ANSI color codes
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
RESET = '\033[0m'

def log(message, color=RESET):
    print(f"{color}[{datetime.now().strftime('%d/%b/%Y %H:%M:%S')}] {message}{RESET}")

DISABLE_RD_TORRENT_SUBS = True


class SearchView(View):
    def get(self, request):
        query = request.GET.get('q', '').strip()
        if len(query) >= 3:
            movies = Movie.objects.filter(
                Q(title__icontains=query) |
                Q(overview__icontains=query)
            )[:10]  # Limit to 10 results for performance

            results = [
                {
                    'id': movie.tmdb_id,
                    'title': movie.title,
                    'release_year': movie.release_year,
                    'poster_path': movie.poster_path,
                    'vote_average': movie.vote_average
                }
                for movie in movies
            ]
            return JsonResponse(results, safe=False)
        return JsonResponse([], safe=False)
class HomePageView(LoginRequiredMixin, View):
    
    def get(self, request):
        log("HomePageView: GET request received", GREEN)
        
        new_on_stremio = self.get_or_create_list("Top Watched Movies of the Week", "https://mdblist.com/lists/linaspurinis/top-watched-movies-of-the-week/json")
        recommended_new = self.get_or_create_list("Recommended New", "https://mdblist.com/lists/zeroq/recommended-new-on-stremio/json")
        weekend_box_office = self.get_or_create_list("Weekend Box Office", "https://mdblist.com/lists/zeroq/weekend-box-office/json")

        context = {
            'movie_lists': [
                {"title": "Top Watched Movies of the Week", "movies": new_on_stremio},
                {"title": "Recommended New", "movies": recommended_new},
                {"title": "Weekend Box Office", "movies": weekend_box_office}
            ]
        }
        
        log("HomePageView: Rendering homepage with context", GREEN)
        return render(request, 'homepage.html', context)

    def get_or_create_list(self, list_name, url):
        log(f"get_or_create_list: Processing {list_name}", BLUE)
        streaming_list, created = StreamingList.objects.get_or_create(
            name=list_name,
            url=url
        )
        
        if created:
            log(f"get_or_create_list: Created new StreamingList '{list_name}'", GREEN)
        else:
            log(f"get_or_create_list: Retrieved existing StreamingList '{list_name}'", BLUE)

        if created or streaming_list.last_updated is None or self.should_update(streaming_list):
            log(f"get_or_create_list: Fetching fresh data for '{list_name}'", YELLOW)
            self.fetch_and_process_data(streaming_list)
            streaming_list.last_updated = timezone.now()
            streaming_list.save()
            log(f"get_or_create_list: Updated '{list_name}' with fresh data", GREEN)
        else:
            log(f"get_or_create_list: Using existing data for '{list_name}'", BLUE)

        return streaming_list.movies.all().order_by('streaminglistmovie__position')

    def should_update(self, streaming_list):
        should_update = timezone.now() - streaming_list.last_updated > timedelta(hours=24)
        log(f"should_update: List '{streaming_list.name}' should update: {should_update}", CYAN)
        return should_update

    @transaction.atomic
    def fetch_and_process_data(self, streaming_list):
        log(f"fetch_and_process_data: Starting for '{streaming_list.name}'", BLUE)
        response = requests.get(streaming_list.url)
        mdblist_data = response.json()

        current_movies = set(streaming_list.movies.values_list('imdb_id', flat=True))
        new_movies = set()

        for position, item in enumerate(mdblist_data, start=1):
            if item.get('mediatype') == 'movie':
                imdb_id = item.get('imdb_id')
                if imdb_id:
                    new_movies.add(imdb_id)
                    log(f"fetch_and_process_data: Processing movie {imdb_id}", CYAN)
                    tmdb_info = self.fetch_tmdb_info(imdb_id)
                    movie_data = {
                        'mdblist_id': item['id'],
                        'imdb_id': imdb_id,
                        'tvdbid': item.get('tvdbid'),
                        'title': item['title'],
                        'rank': item['rank'],
                        'adult': bool(item['adult']),
                        'mediatype': item['mediatype'],
                        'release_year': item['release_year'],
                    }
                    
                    if tmdb_info:
                        movie_data.update({
                            'tmdb_id': tmdb_info['id'],
                            'overview': tmdb_info.get('overview'),
                            'poster_path': tmdb_info.get('poster_path'),
                            'backdrop_path': tmdb_info.get('backdrop_path'),
                            'vote_average': tmdb_info.get('vote_average'),
                            'vote_count': tmdb_info.get('vote_count'),
                            'popularity': tmdb_info.get('popularity')
                        })
                    
                    movie, created = Movie.objects.update_or_create(
                        imdb_id=imdb_id,
                        defaults=movie_data
                    )
                    log(f"fetch_and_process_data: {'Created' if created else 'Updated'} movie {imdb_id}", GREEN)

                    StreamingListMovie.objects.update_or_create(
                        streaming_list=streaming_list,
                        movie=movie,
                        defaults={'position': position}
                    )

        # Remove movies that are no longer in the list
        movies_to_remove = current_movies - new_movies
        removed_count = StreamingListMovie.objects.filter(
            streaming_list=streaming_list, 
            movie__imdb_id__in=movies_to_remove
            ).delete()[0]
        log(f"fetch_and_process_data: Removed {removed_count} movies from '{streaming_list.name}'", YELLOW)

    def fetch_tmdb_info(self, imdb_id):
        log(f"fetch_tmdb_info: Fetching TMDB info for IMDB ID: {imdb_id}", BLUE)
        api_key = "2480c2206d4661b89bf222cbc9c7f5ea"
        url = f"https://api.themoviedb.org/3/find/{imdb_id}?api_key={api_key}&language=en-US&external_source=imdb_id"
        response = requests.get(url)
        data = response.json()
        
        if data.get('movie_results'):
            log(f"fetch_tmdb_info: Found TMDB info for {imdb_id}", GREEN)
            return data['movie_results'][0]
        log(f"fetch_tmdb_info: No TMDB info found for {imdb_id}", YELLOW)
        return None

class TrendingView(LoginRequiredMixin, View):
    def get(self, request):
        log("TrendingView: GET request received", GREEN)
        api_key = "2480c2206d4661b89bf222cbc9c7f5ea"
        url = f"https://api.themoviedb.org/3/movie/popular?api_key={api_key}&language=en-US&page=1"

        log("TrendingView: Fetching popular movies from TMDB", BLUE)
        response = requests.get(url)
        data = response.json()
        top_movies = data.get('results', [])[:20]

        movies_json = json.dumps(top_movies)
        movies_json = json.loads(movies_json)

        context = {
            'movies_json': movies_json
        }
        
        log("TrendingView: Rendering dashboard with context", GREEN)
        return render(request, 'dashboard_v2.html', context)

class MovieDetailView(LoginRequiredMixin, View):
    def get(self, request, movie_id):
        log(f"MovieDetailView: GET request received for movie ID: {movie_id}", GREEN)
        api_key = "2480c2206d4661b89bf222cbc9c7f5ea"
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US&append_to_response=credits"

        log(f"MovieDetailView: Fetching movie details from TMDB for ID: {movie_id}", BLUE)
        response = requests.get(url)
        movie_data = response.json()

        context = {
            'movie': movie_data,
            'cast': movie_data.get('credits', {}).get('cast', [])[:5]  # Get first 5 cast members
        }

        log("MovieDetailView: Rendering movie detail page", GREEN)
        return render(request, 'movie_detail_v2.html', context)
    
    def post(self, request, movie_id):
        movie_title = request.POST.get('movie_title')
        log(f"MovieDetailView: POST request received for movie: {movie_title}", GREEN)

        if DISABLE_RD_TORRENT_SUBS:
            log("MovieDetailView: Real-Debrid, torrent, and subtitles functionality disabled", YELLOW)
            moviesapi_url = f"https://moviesapi.club/movie/{movie_id}"
            vidsrc_url = f"https://vidsrc.cc/v2/embed/movie/{movie_id}"
            return JsonResponse({
                'redirect': reverse('video_stream', kwargs={'video_url': moviesapi_url}) + 
                    f'?title={movie_title}&movie_id={movie_id}&vidsrc_url={vidsrc_url}'
            })
        else:

            try:
                log(f"MovieDetailView: Fetching subtitles for {movie_title}", BLUE)
                subtitles = self.fetch_subtitles(movie_title)
            except Exception as e:
                log(f"MovieDetailView: Error fetching subtitles: {e}", RED)
                subtitles = []

            torrent_api = TorrentAPI()
            rd_api = RealDebridAPI("B4YMPW225WYGYYOOSRNEHFQX33WWVQNY7IWCO54XTVSQYNYJEY3Q")

            try:
                log(f"MovieDetailView: Searching for torrent for {movie_title}", BLUE)
                magnet_link = self.search_for_torrent(torrent_api, movie_title)
                if not magnet_link:
                    log(f"MovieDetailView: No suitable torrent found for: {movie_title}", RED)
                    return JsonResponse({'error': 'No suitable torrent found'}, status=400)

                log(f"MovieDetailView: Adding torrent to Real-Debrid for {movie_title}", BLUE)
                torrent_id = self.add_torrent_to_rd(rd_api, magnet_link)
                
                if not torrent_id:
                    log(f"MovieDetailView: Error adding torrent to Real-Debrid for {movie_title}", RED)
                    return JsonResponse({'error': 'Error adding torrent to Real-Debrid'}, status=400)
                
                log(f"MovieDetailView: Processing torrent for {movie_title}", BLUE)
                file_info = self.process_torrent(rd_api, torrent_id)

                while file_info['status'] != 'downloaded':
                    log(f"MovieDetailView: Waiting for torrent to download for {movie_title}. Current status: {file_info['status']}", YELLOW)
                    time.sleep(3)  # Wait for 10 seconds before checking again
                    file_info = rd_api.get_torrent_info(torrent_id)

                if file_info['status'] == 'downloaded':
                    log(f"MovieDetailView: Torrent downloaded successfully for {movie_title}", GREEN)
                    streaming_url, download_url = self.get_streaming_urls(rd_api, file_info)
                    log(f"MovieDetailView: Streaming URL: {streaming_url}", CYAN)
                    log(f"MovieDetailView: Download URL: {download_url}", CYAN)
                    return self.create_response(movie_title, movie_id, download_url, streaming_url, subtitles)
                else:
                    log(f"MovieDetailView: Torrent processing failed for: {movie_title}", RED)
                    return JsonResponse({'error': 'Torrent processing failed'}, status=400)

            except Exception as e:
                log(f"MovieDetailView: Error processing request: {str(e)}", RED)
                return JsonResponse({'error': 'An unexpected error occurred'}, status=500)

    def search_for_torrent(self, torrent_api, movie_title):
        search_sites = ["1337x", "torlock", "zooqle", "piratebay", "tgx", "nyaasi", "bitsearch", "kickass", "libgen", "yts", "limetorrent", "torrentfunk", "glodls", "torrentproject", "ybt"]
        for site in search_sites:
            try:
                log(f"search_for_torrent: Searching for torrent on {site}", BLUE)
                search_results = torrent_api.search(site, f"{movie_title} 1080p webrip", limit=5)
                if not search_results.get('error'):
                    for result in search_results.get('data', []):
                        if magnet_link := result.get('magnet'):
                            log(f"search_for_torrent: Found magnet link on {site}", GREEN)
                            return magnet_link
            except Exception as e:
                log(f"search_for_torrent: Error searching on {site}: {str(e)}", RED)
        return None

    def add_torrent_to_rd(self, rd_api, magnet_link):
        log(f"add_torrent_to_rd: Adding torrent to Real-Debrid. API: {rd_api}, Magnet: {magnet_link[:50]}...", BLUE)
        log("add_torrent_to_rd: Adding torrent to Real-Debrid", BLUE)
        torrent_response = rd_api.add_magnet(magnet_link)
        
        if torrent_response.get('error'):
            log(f"add_torrent_to_rd: Error adding torrent: {torrent_response['error']}", RED)
            return None
        
        print(f"Torrent added with ID: {torrent_response}")
        log(f"add_torrent_to_rd: Torrent added with ID: {torrent_response['id']}", GREEN)
        return torrent_response['id']

    def process_torrent(self, rd_api, torrent_id):
        log(f"process_torrent: Processing torrent with ID: {torrent_id}", BLUE)
        while True:
            file_info = rd_api.get_torrent_info(torrent_id)
            if file_info['status'] != "magnet_conversion":
                break
            log("process_torrent: Waiting for magnet conversion...", YELLOW)
            time.sleep(15)

        files = file_info['files']
        biggest_file = max(files, key=lambda x: x['bytes'])
        biggest_file_index = files.index(biggest_file)

        log("process_torrent: Selecting biggest file for download", BLUE)
        rd_api.select_files(torrent_id, biggest_file_index + 1)
        return rd_api.get_torrent_info(torrent_id)

    def get_streaming_urls(self, rd_api, file_info):
        log("get_streaming_urls: Getting streaming URLs", BLUE)
        streaming_link = file_info['links'][0]
        unrestricted_link = rd_api.unrestrict_link(streaming_link)
        download_url = unrestricted_link['download']
        
        match = re.search(r'/d/([A-Z0-9]+)/', download_url)
        streaming_url = f"https://real-debrid.com/streaming-{match.group(1)}" if match else download_url
        
        log(f"get_streaming_urls: Streaming URL: {streaming_url}", CYAN)
        log(f"get_streaming_urls: Download URL: {download_url}", CYAN)
        return streaming_url, download_url

    def create_response(self, movie_title, movie_id, download_url, streaming_url, subtitles):
        log(f"create_response: Creating response for {movie_title}", BLUE)
        response = JsonResponse({
            'redirect': reverse('video_stream', kwargs={'video_url': download_url}) + 
                f'?title={movie_title}&subtitles={",".join([sub["url"] for sub in subtitles])}&streaming_url={streaming_url}&movie_id={movie_id}'
        })
        log(f"create_response: Response created successfully for {movie_title}", GREEN)
        return response
                
    def fetch_subtitles(self, movie_title):
        log(f"fetch_subtitles: Fetching subtitles for: {movie_title}", BLUE)
        client = OpenSubtitlesClient()
        processed_subtitles = []

        try:
            movie_results = client.get_query_results(f"{movie_title} 1080p webrip")
            
            if not movie_results:
                log(f"fetch_subtitles: No results found for movie: {movie_title}", YELLOW)
                return []

            first_movie = movie_results[0]
            movie_id = first_movie.get('id')
            
            if not movie_id:
                log(f"fetch_subtitles: No movie ID found for: {movie_title}", YELLOW)
                return []

            # Create a folder for the movie
            movie_folder = os.path.join(settings.MEDIA_ROOT, 'subtitles', movie_title.replace(' ', '_'))
            os.makedirs(movie_folder, exist_ok=True)

            subtitles = client.get_subtitles_by_id(movie_id)
            counter = 0
            for sub in subtitles:
                try:
                    if counter == 5:
                        break
                    lang = sub.get('lang')
                    download_url = sub.get('download')
                    if lang == 'English' and download_url:
                        counter += 1
                        log(f"fetch_subtitles: Processing subtitle {counter} for {movie_title}", BLUE)
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

                        # Save the WebVTT file with a unique name in the movie folder
                        timestamp = int(time.time())
                        file_name = f"{lang}_{timestamp}_{counter}.vtt"
                        file_path = os.path.join(movie_folder, file_name)
                        
                        vtt.save(file_path)

                        # Remove the temporary SRT file
                        os.unlink(temp_srt_path)

                        # Generate the URL for the subtitle file
                        subtitle_url = f"{settings.MEDIA_URL}subtitles/{movie_title.replace(' ', '_')}/{file_name}"

                        processed_subtitles.append({
                            'lang': lang,
                            'url': subtitle_url
                        })
                        
                        log(f"fetch_subtitles: Processed subtitle: {processed_subtitles[-1]}", GREEN)

                except Exception as e:
                    log(f"fetch_subtitles: Error processing subtitle: {str(e)}", RED)
                    continue

        except Exception as e:
            log(f"fetch_subtitles: Error fetching subtitles: {str(e)}", RED)

        return processed_subtitles
class VideoStreamView(LoginRequiredMixin, View):
    def get(self, request, video_url):
        log(f"VideoStreamView: GET request received for URL: {video_url}", GREEN)
        try:
            response = requests.get(video_url, stream=True)
            response.raise_for_status()  # Raise an exception for bad status codes
        except requests.RequestException as e:
            log(f"VideoStreamView: Error fetching video: {str(e)}", RED)
            return HttpResponse(f"Error fetching video: {str(e)}", status=500)

        # Get subtitles from URL parameters
        subtitle_urls = request.GET.get('subtitles', '').split(',')
        subtitles = [
            {'lang': 'English', 'url': unquote(url)}
            for url in subtitle_urls if url
        ]

        log(f"VideoStreamView: Subtitles: {subtitles}", CYAN)

        # Get streaming_url from URL parameters
        streaming_url = request.GET.get('streaming_url', '')

        # Get movie_id from URL parameters
        movie_id = request.GET.get('movie_id', '')

        vidsrc_url = request.GET.get('vidsrc_url', '')

        # Create the MovieAPI URL
        movieapi_url = f"https://moviesapi.club/movie/{movie_id}" if movie_id else ''
        
        
        api_key = "2480c2206d4661b89bf222cbc9c7f5ea"
        movie_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US"
        movie_response = requests.get(movie_url)
        movie_data = movie_response.json()

        # Add movie data to the context
        context = {
            'stream_url': video_url,
            'streaming_url': streaming_url,
            'movieapi_url': movieapi_url,
            'vidsrc_url': vidsrc_url,
            'subtitles': subtitles,
            'movie': movie_data
        }
        log("VideoStreamView: Rendering stream template", GREEN)
        return render(request, 'stream.html', context)



    def stream_video(self, response):
        log("stream_video: Streaming video content", BLUE)
        for chunk in response.iter_content(chunk_size=8192):
            yield chunk