from django.db import models
from django.utils.text import slugify
from django.db import models
from django.utils import timezone

class Movie(models.Model):
    mdblist_id = models.IntegerField(unique=True)
    tmdb_id = models.IntegerField(unique=True, null=True, blank=True)
    imdb_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    tvdbid = models.IntegerField(null=True, blank=True)
    title = models.CharField(max_length=255)
    rank = models.IntegerField(null=True, blank=True)
    adult = models.BooleanField(default=False)
    mediatype = models.CharField(max_length=10)
    release_year = models.IntegerField()
    overview = models.TextField(null=True, blank=True)
    poster_path = models.CharField(max_length=255, null=True, blank=True)
    backdrop_path = models.CharField(max_length=255, null=True, blank=True)
    vote_average = models.FloatField(null=True, blank=True)
    vote_count = models.IntegerField(null=True, blank=True)
    popularity = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.title

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