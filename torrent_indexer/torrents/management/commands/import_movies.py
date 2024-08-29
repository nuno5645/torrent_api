import pandas as pd
from django.core.management.base import BaseCommand
from torrents.models import Movie
from tqdm import tqdm
import os

class Command(BaseCommand):
    help = 'Import movies from a CSV file into the database'

    def handle(self, *args, **options):
        
        #print current directory
        self.stdout.write(os.getcwd())
        # Read the CSV file
        df = pd.read_csv('TMDB_movie_dataset_v11.csv')
        
        df = df[df['imdb_id'].notna()]
        
        #release_date bigger than 1970
        df = df[df['release_date'] > '1970-01-01']
        
        total_movies = len(df)
        
        # Counter for successful and failed imports
        successful_imports = 0
        failed_imports = 0

        # Iterate through the rows and create Movie objects
        for index, row in tqdm(df.iterrows(), total=total_movies, desc="Importing movies"):
            try:
                movie, created = Movie.objects.get_or_create(
                    mdblist_id=row['id'],
                    defaults={
                        'tmdb_id': row['id'],
                        'imdb_id': row['imdb_id'] if pd.notna(row['imdb_id']) else None,
                        'title': row['title'],
                        'overview': row['overview'] if pd.notna(row['overview']) else None,
                        'vote_average': row['vote_average'],
                        'vote_count': row['vote_count'],
                        'release_year': int(row['release_date'][:4]) if pd.notna(row['release_date']) else None,
                        'poster_path': row['poster_path'] if pd.notna(row['poster_path']) else None,
                        'backdrop_path': row['backdrop_path'] if pd.notna(row['backdrop_path']) else None,
                        'popularity': row['popularity'],
                        'adult': row['adult'],
                        'mediatype': 'movie'
                    }
                )
                successful_imports += 1
            except Exception as e:
                failed_imports += 1
                self.stdout.write(self.style.ERROR(f'[{index+1}/{total_movies}] Failed to import movie: {row["title"]}. Error: {str(e)}'))

        self.stdout.write(self.style.SUCCESS(f'Movie import completed. Total movies processed: {total_movies}'))
        self.stdout.write(self.style.SUCCESS(f'Successful imports: {successful_imports}'))
        self.stdout.write(self.style.WARNING(f'Failed imports: {failed_imports}'))