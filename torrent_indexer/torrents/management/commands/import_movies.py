from django.core.management.base import BaseCommand
from torrents.models import Movie
from django.db import transaction
import csv
from datetime import datetime
from tqdm import tqdm
import os

class Command(BaseCommand):
    help = 'Import movies from a CSV file into the database'

    def handle(self, *args, **options):
        self.stdout.write(os.getcwd())
        
        csv_file = 'TMDB_movie_dataset_v11.csv'
        batch_size = 5000
        movies_to_create = []
        total_processed = 0
        successful_imports = 0
        
        with open(csv_file, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            for row in tqdm(csv_reader, desc="Processing movies"):
                total_processed += 1
                
                if not row['imdb_id'] or row['release_date'] <= '1970-01-01':
                    continue
                
                try:
                    release_year = int(row['release_date'][:4]) if row['release_date'] else None
                    
                    movie = Movie(
                        tmdb_id=int(row['id']),
                        imdb_id=row['imdb_id'],
                        title=row['title'],
                        overview=row['overview'] or None,
                        vote_average=float(row['vote_average']) if row['vote_average'] else None,
                        vote_count=int(row['vote_count']) if row['vote_count'] else None,
                        release_year=release_year,
                        poster_path=row['poster_path'] or None,
                        backdrop_path=row['backdrop_path'] or None,
                        popularity=float(row['popularity']) if row['popularity'] else None,
                        adult=row['adult'].lower() == 'true',
                        mediatype='movie'
                    )
                    movies_to_create.append(movie)
                    successful_imports += 1
                    
                    if len(movies_to_create) >= batch_size:
                        self._bulk_create_movies(movies_to_create)
                        movies_to_create = []
                
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Failed to process movie: {row.get("title", "Unknown")}. Error: {str(e)}'))
        
        if movies_to_create:
            self._bulk_create_movies(movies_to_create)
        
        self.stdout.write(self.style.SUCCESS(f'Movie import completed. Total movies processed: {total_processed}'))
        self.stdout.write(self.style.SUCCESS(f'Successful imports: {successful_imports}'))

    @transaction.atomic
    def _bulk_create_movies(self, movies):
        Movie.objects.bulk_create(movies, ignore_conflicts=True)