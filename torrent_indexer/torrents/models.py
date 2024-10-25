from django.db import models
from django.utils.text import slugify
from django.db import models
from django.utils import timezone
from django.conf import settings  # Import settings to reference the User model

class Movie(models.Model):
    tmdb_id = models.IntegerField(null=True, blank=True)
    imdb_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    tvdbid = models.IntegerField(null=True, blank=True)
    title = models.CharField(max_length=255)
    rank = models.IntegerField(null=True, blank=True)
    adult = models.BooleanField(default=False)
    mediatype = models.CharField(max_length=10, default="movie")
    release_year = models.IntegerField(default=0)
    overview = models.TextField(null=True, blank=True)
    poster_path = models.CharField(max_length=255, null=True, blank=True)
    backdrop_path = models.CharField(max_length=255, null=True, blank=True)
    vote_average = models.FloatField(null=True, blank=True)
    vote_count = models.IntegerField(null=True, blank=True)
    popularity = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.title
    
class WatchHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='watch_history')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='watch_history')
    watched_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} watched {self.movie.title} at {self.watched_at}"

class StreamingList(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    url = models.URLField(default="")
    movies = models.ManyToManyField(Movie, through='StreamingListMovie')
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

class StreamingListMovie(models.Model):
    streaming_list = models.ForeignKey(StreamingList, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    position = models.IntegerField()

    class Meta:
        ordering = ['position']
        unique_together = ('streaming_list', 'movie')

class Torrent(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='torrents')
    name = models.CharField(max_length=255)
    magnet_link = models.TextField()
    file_size = models.BigIntegerField()  # Size in bytes
    seeders = models.IntegerField()
    leechers = models.IntegerField()
    upload_date = models.DateTimeField()
    quality = models.CharField(max_length=10)
    resolution = models.CharField(max_length=10)
    codec = models.CharField(max_length=10)
    audio_codec = models.CharField(max_length=10)
    

    def __str__(self):
        return f"{self.name} - {self.movie.title}"
    
    
class RealDebrid(models.Model):
    torrent = models.OneToOneField(Torrent, on_delete=models.CASCADE, related_name='real_debrid')
    rd_id = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=50)
    download_link = models.URLField(max_length=500)
    added_date = models.DateTimeField(auto_now_add=True)
    last_checked = models.DateTimeField(auto_now=True)
    file_path = models.CharField(max_length=500)
    file_size = models.BigIntegerField()  # Size in bytes
    seeders = models.IntegerField()
    speed = models.CharField(max_length=50)
    progress = models.FloatField(default=0)

    def __str__(self):
        return f"RD: {self.torrent.name}"
class TVShow(models.Model):
    tmdb_id = models.IntegerField(unique=True)
    imdb_id = models.CharField(max_length=20, null=True, blank=True)
    tvdb_id = models.IntegerField(null=True, blank=True)
    title = models.CharField(max_length=255)
    overview = models.TextField(null=True, blank=True)
    poster_path = models.CharField(max_length=255, null=True, blank=True)
    backdrop_path = models.CharField(max_length=255, null=True, blank=True)
    first_air_date = models.DateField(null=True, blank=True)
    vote_average = models.FloatField(null=True, blank=True)
    vote_count = models.IntegerField(null=True, blank=True)
    popularity = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.title

class Season(models.Model):
    tv_show = models.ForeignKey(TVShow, on_delete=models.CASCADE, related_name='seasons')
    season_number = models.IntegerField()
    name = models.CharField(max_length=255)
    overview = models.TextField(null=True, blank=True)
    poster_path = models.CharField(max_length=255, null=True, blank=True)
    air_date = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ('tv_show', 'season_number')

    def __str__(self):
        return f"{self.tv_show.title} - Season {self.season_number}"

class Episode(models.Model):
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name='episodes')
    episode_number = models.IntegerField()
    name = models.CharField(max_length=255)
    overview = models.TextField(null=True, blank=True)
    still_path = models.CharField(max_length=255, null=True, blank=True)
    air_date = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ('season', 'episode_number')

    def __str__(self):
        return f"{self.season.tv_show.title} - S{self.season.season_number:02d}E{self.episode_number:02d} - {self.name}"

class TVShowWatchHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tv_watch_history')
    episode = models.ForeignKey(Episode, on_delete=models.CASCADE, related_name='watch_history')
    watched_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} watched {self.episode} at {self.watched_at}"

class TVShowStreamingList(models.Model):
    name = models.CharField(max_length=255)
    url = models.URLField()
    last_updated = models.DateTimeField(null=True, blank=True)
    tv_shows = models.ManyToManyField(TVShow, through='TVShowStreamingListShow')

class TVShowStreamingListShow(models.Model):
    streaming_list = models.ForeignKey(TVShowStreamingList, on_delete=models.CASCADE)
    tv_show = models.ForeignKey(TVShow, on_delete=models.CASCADE)
    position = models.IntegerField()

    class Meta:
        ordering = ['position']

class Source(models.Model):
    # id = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=255)
    base_url = models.URLField()
    has_tv_shows = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=0)

    # Fields for constructing URLs
    uses_tmdb = models.BooleanField(default=True)
    movie_path = models.CharField(max_length=255, blank=True)
    tv_show_path = models.CharField(max_length=255, blank=True)

    # Placeholders for dynamic parts of the URL
    season_placeholder = models.CharField(max_length=20, default="{season}")
    episode_placeholder = models.CharField(max_length=20, default="{episode}")

    def __str__(self):
        return f"{self.name} ({self.id})"

    def get_movie_url(self, movie):
        if not self.movie_path:
            return None
        id_to_use = movie
        return f"{self.base_url}{self.movie_path.format(id=id_to_use)}"

    def get_tv_show_url(self, show_id, season, episode, imdb_id=None):
        if not self.has_tv_shows or not self.tv_show_path:
            return None
        id_to_use = show_id if self.uses_tmdb else imdb_id
        return (f"{self.base_url}{self.tv_show_path}"
                .format(id=id_to_use, season=season, episode=episode))