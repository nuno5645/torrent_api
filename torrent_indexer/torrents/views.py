# Python standard library imports
import json
import requests
from datetime import datetime, timedelta
from urllib.parse import unquote

# Django imports
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.db.models import Q
from .models import WatchHistory, TVShow, Season, Episode, TVShowWatchHistory

# Local imports
from .models import Movie, StreamingList, StreamingListMovie

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



        print(new_on_stremio)
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
        
        print(data)
        
        if data.get('movie_results'):
            log(f"fetch_tmdb_info: Found TMDB info for {imdb_id}", GREEN)
            return data['movie_results'][0]
        log(f"fetch_tmdb_info: No TMDB info found for {imdb_id}", YELLOW)
        return None

class MovieDetailView(LoginRequiredMixin, View):
    def get(self, request, movie_id):
        log(f"MovieDetailView: GET request received for movie ID: {movie_id}", GREEN)
        api_key = "2480c2206d4661b89bf222cbc9c7f5ea"
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US&append_to_response=credits"
        
        # Fetch movie recommendations
        recommendations_url = f"https://api.themoviedb.org/3/movie/{movie_id}/recommendations?api_key={api_key}&language=en-US&page=1"
        log(f"MovieDetailView: Fetching movie recommendations for ID: {movie_id}", BLUE)
        recommendations_response = requests.get(recommendations_url)
        recommendations_data = recommendations_response.json()


        log(f"MovieDetailView: Fetching movie details from TMDB for ID: {movie_id}", BLUE)
        response = requests.get(url)
        movie_data = response.json()
        print(movie_data)
        context = {
            'movie': movie_data,
            'cast': movie_data.get('credits', {}).get('cast', [])[:5],  # Get first 5 cast members
            'recommended_movies': recommendations_data.get('results', [])[:5]  # Get first 5 recommended movies
        }

        log("MovieDetailView: Rendering movie detail page", GREEN)
        return render(request, 'movie_detail_v2.html', context)
    
    def post(self, request, movie_id):
        movie_title = request.POST.get('movie_title')
        imdb_id = request.POST.get('imdb_id')
        log(f"MovieDetailView: POST request received for movie: {movie_title}", GREEN)

        if DISABLE_RD_TORRENT_SUBS:
            log("MovieDetailView: Real-Debrid, torrent, and subtitles functionality disabled", YELLOW)
            
            # Redirect to VideoStreamView with only necessary parameters
            redirect_url = reverse('video_stream') + f'?movie_id={movie_id}&title={movie_title}&imdb_id={imdb_id}'
            
            return JsonResponse({
                'redirect': redirect_url
            })
        

class VideoStreamView(LoginRequiredMixin, View):
    def get(self, request):
        movie_id = request.GET.get('movie_id')
        title = request.GET.get('title')
        imdb_id = request.GET.get('imdb_id')

        # Construct URLs based on movie_id
         # Create the MovieAPI URL
        movieapi_url = f"https://moviesapi.club/movie/{movie_id}" if movie_id else ''
        vidsrc_url = f"https://vidsrc.cc/v2/embed/movie/{movie_id}"
        vidsrc_url_2 = f"https://vidsrc.xyz/embed/movie/{movie_id}"
        multiembed_url = f"https://multiembed.mov/?video_id={movie_id}&tmdb=1"
        warezcdn_url = f"https://embed.warezcdn.com/filme/{imdb_id}"
            
       

        api_key = "2480c2206d4661b89bf222cbc9c7f5ea"
        movie_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US"
        movie_response = requests.get(movie_url)
        movie_data = movie_response.json()
        


        # Record the watch history
        try:
            movie = Movie.objects.get(tmdb_id=movie_id)
            WatchHistory.objects.create(
                user=request.user,
                movie=movie,
                watched_at=timezone.now()
            )
            log(f"VideoStreamView: Recorded watch history for user {request.user.username} and movie {movie.title}", GREEN)
        except Movie.DoesNotExist:
            log(f"VideoStreamView: Movie with ID {movie_id} does not exist.", YELLOW)

        # Add movie data to the context
        context = {
            'movieapi_url': movieapi_url,
            'vidsrc_url': vidsrc_url,
            'vidsrc_url_2': vidsrc_url_2,
            'warezcdn_url': warezcdn_url,
            'multiembed_url': multiembed_url,  # Add the new source to the context
            'movie': movie_data
        }
        log("VideoStreamView: Rendering stream template", GREEN)
        return render(request, 'stream.html', context)



class WatchHistoryView(LoginRequiredMixin, View):
    def get(self, request):
        watch_history = WatchHistory.objects.filter(user=request.user).order_by('-watched_at')
        context = {
            'watch_history': watch_history
        }
        return render(request, 'watch_history.html', context)

class TVShowSearchView(View):
    def get(self, request):
        query = request.GET.get('q', '').strip()
        if len(query) >= 3:
            tv_shows = TVShow.objects.filter(
                Q(title__icontains=query) |
                Q(overview__icontains=query)
            )[:10]  # Limit to 10 results for performance

            results = [
                {
                    'id': show.tmdb_id,
                    'title': show.title,
                    'first_air_date': show.first_air_date,
                    'poster_path': show.poster_path,
                    'vote_average': show.vote_average
                }
                for show in tv_shows
            ]
            return JsonResponse(results, safe=False)
        return JsonResponse([], safe=False)

class TVShowDetailView(LoginRequiredMixin, View):
    def get(self, request, show_id):
        log(f"TVShowDetailView: GET request received for show ID: {show_id}", GREEN)
        api_key = "2480c2206d4661b89bf222cbc9c7f5ea"
        url = f"https://api.themoviedb.org/3/tv/{show_id}?api_key={api_key}&language=en-US&append_to_response=credits,seasons,external_ids"
        
        log(f"TVShowDetailView: Fetching TV show details from TMDB for ID: {show_id}", BLUE)
        response = requests.get(url)
        show_data = response.json()
        
        #print the show data and make it visible in the terminal in a readable format
        print(json.dumps(show_data, indent=4))
        
        # Fetch or create TVShow object
        tv_show, created = TVShow.objects.update_or_create(
            tmdb_id=show_data['id'],
            defaults={
                'title': show_data['name'],
                'imdb_id': show_data['external_ids']['imdb_id'],
                'overview': show_data['overview'],
                'poster_path': show_data['poster_path'],
                'backdrop_path': show_data['backdrop_path'],
                'first_air_date': show_data['first_air_date'],
                'vote_average': show_data['vote_average'],
                'vote_count': show_data['vote_count'],
                'popularity': show_data['popularity'],
            }
        )

        # Update or create seasons and episodes
        seasons_with_episodes = []
        for season_data in show_data['seasons']:
            season, _ = Season.objects.update_or_create(
                tv_show=tv_show,
                season_number=season_data['season_number'],
                defaults={
                    'name': season_data['name'],
                    'overview': season_data['overview'],
                    'poster_path': season_data['poster_path'],
                    'air_date': season_data['air_date'],
                }
            )
            
            # Fetch episode data for each season
            season_url = f"https://api.themoviedb.org/3/tv/{show_id}/season/{season_data['season_number']}?api_key={api_key}&language=en-US"
            season_response = requests.get(season_url)
            season_details = season_response.json()
            
            episodes = []
            for episode_data in season_details['episodes']:
                episode, _ = Episode.objects.update_or_create(
                    season=season,
                    episode_number=episode_data['episode_number'],
                    defaults={
                        'name': episode_data['name'],
                        'overview': episode_data['overview'],
                        'air_date': episode_data['air_date'],
                    }
                )
                episodes.append(episode_data)
            
            season_data['episodes'] = episodes
            seasons_with_episodes.append(season_data)

        context = {
            'show': show_data,
            'cast': show_data.get('credits', {}).get('cast', [])[:5],  # Get first 5 cast members
            'seasons': seasons_with_episodes,
        }

        log("TVShowDetailView: Rendering TV show detail page", GREEN)
        return render(request, 'tv_show_detail.html', context)

    def post(self, request, show_id):
        season = request.POST.get('season')
        episode = request.POST.get('episode')
        imdb_id = request.POST.get('imdb_id')
        if season and episode:
            return redirect('tv_stream', show_id=show_id, season=season, episode=episode, imdb_id=imdb_id)
        else:
            return JsonResponse({'error': 'Invalid season or episode'}, status=400)


class TVShowStreamView(LoginRequiredMixin, View):
    def get(self, request, show_id, season, episode, imdb_id):
        # Use the parameters directly from the URL
        season_number = season
        episode_number = episode

        # Construct URLs based on show_id, season, and episode
        vidsrc_url = f"https://vidsrc.cc/v2/embed/tv/{show_id}/{season_number}/{episode_number}"
        vidsrc_url_2 = f"https://vidsrc.xyz/embed/tv/{show_id}/{season_number}/{episode_number}"
        multiembed_url = f"https://multiembed.mov/?video_id={show_id}&tmdb=1&s={season_number}&e={episode_number}"
        warezcdn_url = f"https://embed.warezcdn.com/serie/{imdb_id}/{season_number}/{episode_number}"
        
        print(warezcdn_url)

        api_key = "2480c2206d4661b89bf222cbc9c7f5ea"
        episode_url = f"https://api.themoviedb.org/3/tv/{show_id}/season/{season_number}/episode/{episode_number}?api_key={api_key}&language=en-US"
        episode_response = requests.get(episode_url)
        episode_data = episode_response.json()

        # Record the watch history
        try:
            tv_show = TVShow.objects.get(tmdb_id=show_id)
            season = Season.objects.get(tv_show=tv_show, season_number=season_number)
            episode = Episode.objects.get(season=season, episode_number=episode_number)
            TVShowWatchHistory.objects.create(
                user=request.user,
                episode=episode,
                watched_at=timezone.now()
            )
            log(f"TVShowStreamView: Recorded watch history for user {request.user.username} and episode {episode}", GREEN)
        except (TVShow.DoesNotExist, Season.DoesNotExist, Episode.DoesNotExist):
            log(f"TVShowStreamView: TV show, season, or episode does not exist.", YELLOW)

        context = {
            'vidsrc_url': vidsrc_url,
            'vidsrc_url_2': vidsrc_url_2,
            'multiembed_url': multiembed_url,
            'warezcdn_url': warezcdn_url,
            'episode': episode_data,
        }
        log("TVShowStreamView: Rendering TV show stream template", GREEN)
        return render(request, 'tv_stream.html', context)