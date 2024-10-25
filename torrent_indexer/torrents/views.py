# Python standard library imports
import json
import requests
from datetime import datetime, timedelta
from urllib.parse import unquote
from django.template.defaulttags import register

register.filter('class_name', lambda value: value.__class__.__name__)

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
from .models import TVShowStreamingList, TVShowStreamingListShow, WatchHistory, TVShow, Season, Episode, TVShowWatchHistory, Source

# Local imports
from .models import Movie, StreamingList, StreamingListMovie


from bs4 import BeautifulSoup

import tmdbsimple as tmdb

# At the beginning of your file, after the imports
tmdb.API_KEY = "2480c2206d4661b89bf222cbc9c7f5ea"

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


class TVShowHomePageView(LoginRequiredMixin, View):
    
    def get(self, request):
        log("TVShowHomePageView: GET request received", GREEN)
        
        latest_tv_shows = self.get_or_create_tv_list("Latest TV Shows", "https://mdblist.com/lists/garycrawfordgc/latest-tv-shows/json")
        netflix_shows = self.get_or_create_tv_list("Netflix Shows", "https://mdblist.com/lists/garycrawfordgc/netflix-shows/json")
        hbo_shows = self.get_or_create_tv_list("HBO Shows", "https://mdblist.com/lists/garycrawfordgc/hbo-shows/json")
        imdb_100k_votes = self.get_or_create_tv_list("IMDB 7.0+ Trakt 70%+", "https://mdblist.com/lists/superash/tv-shows-imdb-7-trakt-70/json")

        context = {
            'tv_show_lists': [
                {"title": "Latest TV Shows", "tv_shows": latest_tv_shows},
                {"title": "IMDB Most Votes", "tv_shows": imdb_100k_votes},
                {"title": "Netflix Shows", "tv_shows": netflix_shows},
                {"title": "HBO Shows", "tv_shows": hbo_shows},
            ]
        }
                
        log("TVShowHomePageView: Rendering TV show homepage with context", GREEN)
        return render(request, 'tv_show_homepage.html', context)

    def get_or_create_tv_list(self, list_name, url):
        log(f"get_or_create_tv_list: Processing {list_name}", BLUE)
        streaming_list, created = TVShowStreamingList.objects.get_or_create(
            name=list_name,
            url=url
        )
        
        if created:
            log(f"get_or_create_tv_list: Created new TVShowStreamingList '{list_name}'", GREEN)
        else:
            log(f"get_or_create_tv_list: Retrieved existing TVShowStreamingList '{list_name}'", BLUE)

        if created or streaming_list.last_updated is None or self.should_update(streaming_list):
            log(f"get_or_create_tv_list: Fetching fresh data for '{list_name}'", YELLOW)
            self.fetch_and_process_tv_data(streaming_list)
            streaming_list.last_updated = timezone.now()
            streaming_list.save()
            log(f"get_or_create_tv_list: Updated '{list_name}' with fresh data", GREEN)
        else:
            log(f"get_or_create_tv_list: Using existing data for '{list_name}'", BLUE)
            #self.fetch_and_process_tv_data(streaming_list)

        return streaming_list.tv_shows.all().order_by('-tvshowstreaminglistshow__tv_show__popularity')

    def should_update(self, streaming_list):
        should_update = timezone.now() - streaming_list.last_updated > timedelta(hours=24)
        log(f"should_update: List '{streaming_list.name}' should update: {should_update}", CYAN)
        return should_update

    @transaction.atomic
    def fetch_and_process_tv_data(self, streaming_list):
        log(f"fetch_and_process_tv_data: Starting for '{streaming_list.name}'", BLUE)
                
        
        response = requests.get(streaming_list.url)
                
        mdblist_data = response.json()
        
        mdblist_data = mdblist_data[:30]
        
        current_tv_shows = set(streaming_list.tv_shows.values_list('imdb_id', flat=True))
        new_tv_shows = set()

        for position, item in enumerate(mdblist_data, start=1):
            if item.get('mediatype') == 'show':
                log(f"fetch_and_process_tv_data: Processing TV show {item.get('title')}", CYAN)
                tmdb_info = self.fetch_tmdb_tv_info(item.get('id'))
                if tmdb_info:
                    # Check if 'animation' is in the genres
                    genres = [genre['name'].lower() for genre in tmdb_info.get('genres', [])]
                    if 'animation' in genres:
                        log(f"fetch_and_process_tv_data: Skipping animated show {item.get('title')}", YELLOW)
                        continue

                    tv_show_data = {
                        'imdb_id': item.get('imdb_id'),
                        'title': item['title'],
                        'first_air_date': item.get('release_date'),
                    }
                    
                    tv_show_data.update({
                        'tmdb_id':item.get('id'),
                        'overview': tmdb_info.get('overview'),
                        'poster_path': tmdb_info.get('poster_path'),
                        'backdrop_path': tmdb_info.get('backdrop_path'),
                        'vote_average': tmdb_info.get('vote_average'),
                        'vote_count': tmdb_info.get('vote_count'),
                        'popularity': tmdb_info.get('popularity')
                    })
                    
                    try:
                        tv_show, created = TVShow.objects.update_or_create(
                            tmdb_id=item.get('id'),
                            defaults=tv_show_data
                        )
                        TVShowStreamingListShow.objects.update_or_create(
                            streaming_list=streaming_list,
                            tv_show=tv_show,
                            defaults={'position': position}
                        )
                        log(f"fetch_and_process_tv_data: {'Created' if created else 'Updated'} TV show {item.get('imdb_id')}", GREEN)
                    except Exception as e:
                        log(f"fetch_and_process_tv_data: Error creating TV show {item.get('title')}: {e}", RED)

                        tv_show = TVShow.objects.get(tmdb_id=item.get('id'))

                        TVShowStreamingListShow.objects.update_or_create(
                            streaming_list=streaming_list,
                            tv_show=tv_show,
                            defaults={'position': position}
                        )
                        
                        

        # # Remove TV shows that are no longer in the list
        # tv_shows_to_remove = current_tv_shows - new_tv_shows
        # removed_count = TVShowStreamingListShow.objects.filter(
        #     streaming_list=streaming_list, 
        #     tv_show__imdb_id__in=tv_shows_to_remove
        # ).delete()[0]
        # log(f"fetch_and_process_tv_data: Removed {removed_count} TV shows from '{streaming_list.name}'", YELLOW)

    def fetch_tmdb_tv_info(self, tmdb_id):
        log(f"fetch_tmdb_tv_info: Fetching TMDB info for tmdb ID: {tmdb_id}", BLUE)
        api_key = "2480c2206d4661b89bf222cbc9c7f5ea"
        url = f"https://api.themoviedb.org/3/tv/{tmdb_id}?api_key={api_key}&language=en-US"

        response = requests.get(url)
        data = response.json()
                
        if data:
            return data
        
        log(f"fetch_tmdb_tv_info: No TMDB info found for {tmdb_id}", YELLOW)
        return None
class MovieDetailView(LoginRequiredMixin, View):
    def get(self, request, movie_id):
        log(f"MovieDetailView: GET request received for movie ID: {movie_id}", GREEN)
        
        movie = tmdb.Movies(movie_id)
        movie_data = movie.info(append_to_response='credits')
        
        # Fetch movie recommendations
        recommendations = movie.recommendations()

        context = {
            'movie': movie_data,
            'cast': movie_data.get('credits', {}).get('cast', [])[:5],  # Get first 5 cast members
            'recommended_movies': recommendations.get('results', [])[:5]  # Get first 5 recommended movies
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

        # Get all active sources for movies
        sources = Source.objects.filter(is_active=True).order_by('priority')

        # Generate URLs for each source
        available_sources = {}
        for source in sources:
            url = source.get_movie_url(movie_id)
            if url:
                available_sources[source.name.lower()] = {
                    'name': source.name,
                    'url': url
                }

        api_key = "2480c2206d4661b89bf222cbc9c7f5ea"
        movie_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US"
        movie_response = requests.get(movie_url)
        movie_data = movie_response.json()

        # Record the watch history
        movie, created = Movie.objects.get_or_create(tmdb_id=movie_id)
        if created:
            log(f"VideoStreamView: Movie with ID {movie_id} does not exist.", YELLOW)
        else:
            WatchHistory.objects.create(
                user=request.user,
                movie=movie,
                watched_at=timezone.now()
            )
            log(f"VideoStreamView: Recorded watch history for user {request.user.username} and movie {movie.title}", GREEN)

        # Add movie data and available sources to the context
        context = {
            'available_sources': available_sources,
            'movie': movie_data
        }
        log("VideoStreamView: Rendering stream template", GREEN)
        return render(request, 'stream.html', context)


class WatchHistoryView(LoginRequiredMixin, View):
    def get(self, request):
        movie_history = WatchHistory.objects.filter(user=request.user).order_by('-watched_at')
        tv_history = TVShowWatchHistory.objects.filter(user=request.user).order_by('-watched_at')
        
        # Combine and sort the two querysets
        combined_history = sorted(
            list(movie_history) + list(tv_history),
            key=lambda x: x.watched_at,
            reverse=True
        )
        
        context = {
            'watch_history': combined_history
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
        
        tv = tmdb.TV(show_id)
        show_data = tv.info(append_to_response='credits,external_ids')
        
        # Fetch or create TVShow object
        tv_show, created = TVShow.objects.update_or_create(
            tmdb_id=show_data['id'],
            defaults={
                'title': show_data['name'],
                'imdb_id': show_data['external_ids'].get('imdb_id', None),
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
            season_details = tmdb.TV_Seasons(show_id, season_data['season_number']).info()
            
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
                episode_watched = TVShowWatchHistory.objects.filter(user=request.user, episode=episode).exists()

                if episode_watched:
                    episode_data['watched'] = True

                episodes.append(episode_data)
            
            season_data['episodes'] = episodes
            seasons_with_episodes.append(season_data)
            
        context = {
            'show': show_data,
            'cast': show_data.get('credits', {}).get('cast', [])[:5],
            'seasons': seasons_with_episodes,
        }

        log("TVShowDetailView: Rendering TV show detail page", GREEN)
        return render(request, 'tv_show_detail.html', context)

    def post(self, request, show_id):
        season = request.POST.get('season')
        episode = request.POST.get('episode')
        imdb_id = request.POST.get('imdb_id')
        if season and episode:
            if imdb_id:
                return redirect('tv_stream', show_id=show_id, season=season, episode=episode, imdb_id=imdb_id)
            else:
                return redirect('tv_stream', show_id=show_id, season=season, episode=episode)
        else:
            return JsonResponse({'error': 'Invalid season or episode'}, status=400)




class TVShowStreamView(LoginRequiredMixin, View):
    def get(self, request, show_id, season, episode, imdb_id=None):
        season_number = season
        episode_number = episode

        # Get all active sources for TV shows
        sources = Source.objects.filter(is_active=True, has_tv_shows=True).order_by('priority')
        
        print(f"{GREEN}Sources: {sources}{RESET}")

        # Generate URLs for each source
        available_sources = {}
        for source in sources:
            url = source.get_tv_show_url(show_id, season_number, episode_number, imdb_id)
            if url:
                print(f"{BLUE}Checking availability of {source.name} at {url}{RESET}")
                if self.check_source_availability(url):
                    available_sources[f'{source.name.lower()}_url'] = url
                    print(f"{GREEN}{source.name} is available at {url}{RESET}")
                else:
                    available_sources[f'{source.name.lower()}_url'] = url

        url_list = [url for url in available_sources.values()]
        print(f"{GREEN}Available source URLs: {url_list}{RESET}")

        api_key = "2480c2206d4661b89bf222cbc9c7f5ea"
        episode_url = f"https://api.themoviedb.org/3/tv/{show_id}/season/{season_number}/episode/{episode_number}?api_key={api_key}&language=en-US"
        episode_response = requests.get(episode_url)
        episode_data = episode_response.json()

        # Record watch history
        self.record_watch_history(show_id, season_number, episode_number)

        next_episode = self.get_next_episode(show_id, season_number, episode_number, imdb_id)

        context = {
            'url_list': url_list,
            'episode': episode_data,
            'next_episode': next_episode,
            'imdb_id': imdb_id,
        }
        log("TVShowStreamView: Rendering TV show stream template", GREEN)
        return render(request, 'tv_stream.html', context)
    
    def check_source_availability(self, url):
        error_phrases = ["Video not found", "404", "File not found"]
        error_words = [" Erro ", " Error "]
        
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                if soup.find('video') or soup.find('iframe'):
                    return True

                if any(phrase in response.text for phrase in error_phrases) or \
                any(word in f" {response.text.lower()} " for word in error_words) or \
                response.text.lower().startswith(("erro ", "error ")) or \
                response.text.lower().endswith((" erro", " error")):
                    print(f"{RED}Source {url} is not available{RESET}")
                    return False

            return True
        except requests.RequestException:
            return False

    def record_watch_history(self, show_id, season_number, episode_number):
        try:
            tv_show = TVShow.objects.get(tmdb_id=show_id)
            season = Season.objects.get(tv_show=tv_show, season_number=season_number)
            episode = Episode.objects.get(season=season, episode_number=episode_number)
            TVShowWatchHistory.objects.create(
                user=self.request.user,
                episode=episode,
                watched_at=timezone.now()
            )
            
            log(f"TVShowStreamView: Recorded watch history for user {self.request.user.username} and episode {episode}", GREEN)
        except (TVShow.DoesNotExist, Season.DoesNotExist, Episode.DoesNotExist):
            log(f"TVShowStreamView: TV show, season, or episode does not exist.", YELLOW)
            


            
    def get_next_episode(self, show_id, season_number, episode_number, imdb_id):
        try:
            tv_show = TVShow.objects.get(tmdb_id=show_id)
            current_season = Season.objects.get(tv_show=tv_show, season_number=season_number)
            current_episode = Episode.objects.get(season=current_season, episode_number=episode_number)
            
            # Try to get the next episode in the same season
            next_episode = Episode.objects.filter(season=current_season, episode_number__gt=episode_number).order_by('episode_number').first()
            
            if next_episode:
                return {
                    'show_id': show_id,
                    'season': season_number,
                    'episode': next_episode.episode_number,
                    'imdb_id': imdb_id
                }
            
            # If there's no next episode in the current season, try the next season
            next_season = Season.objects.filter(tv_show=tv_show, season_number__gt=season_number).order_by('season_number').first()
            
            if next_season:
                first_episode_next_season = Episode.objects.filter(season=next_season).order_by('episode_number').first()
                if first_episode_next_season:
                    return {
                        'show_id': show_id,
                        'season': next_season.season_number,
                        'episode': first_episode_next_season.episode_number,
                        'imdb_id': imdb_id
                    }
            
            # If there's no next episode or season, return None
            return None
        except (TVShow.DoesNotExist, Season.DoesNotExist, Episode.DoesNotExist):
            return None

