from django.db import models

class Movie(models.Model):
    adult = models.BooleanField(default=False)
    backdrop_path = models.CharField(max_length=255)
    genre_ids = models.JSONField()  # Assuming you want to store a list of genre IDs
    tmdb_id = models.IntegerField(unique=True)  # Renamed 'id' to 'tmdb_id' for clarity
    original_language = models.CharField(max_length=10)
    original_title = models.CharField(max_length=255)
    overview = models.TextField()
    popularity = models.FloatField()
    poster_path = models.CharField(max_length=255)
    release_date = models.DateField()
    title = models.CharField(max_length=255)
    video = models.BooleanField(default=False)
    vote_average = models.FloatField()
    vote_count = models.IntegerField()

    def __str__(self):
        return self.title