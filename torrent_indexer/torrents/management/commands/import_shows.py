from django.core.management.base import BaseCommand
from torrents.models import TVShow
from django.db import transaction
import csv
from datetime import datetime
from tqdm import tqdm
import os

class Command(BaseCommand):
    help = 'Import TV shows from a CSV file into the database'

    def handle(self, *args, **options):
        self.stdout.write(os.getcwd())
        
        csv_file = 'TMDB_tv_dataset_v3.csv'  # Update this to your TV shows CSV file
        batch_size = 5000
        shows_to_create = []
        total_processed = 0
        successful_imports = 0
        
        with open(csv_file, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            for row in tqdm(csv_reader, desc="Processing TV shows"):
                total_processed += 1
                
                
                try:
                    first_air_date = datetime.strptime(row['first_air_date'], '%Y-%m-%d').date() if row['first_air_date'] else None
                    
                    show = TVShow(
                        tmdb_id=int(row['id']),
                        title=row['name'],
                        overview=row['overview'] or None,
                        vote_average=float(row['vote_average']) if row['vote_average'] else None,
                        vote_count=int(row['vote_count']) if row['vote_count'] else None,
                        first_air_date=first_air_date,
                        poster_path=row['poster_path'] or None,
                        backdrop_path=row['backdrop_path'] or None,
                        popularity=float(row['popularity']) if row['popularity'] else None
                    )
                    shows_to_create.append(show)
                    successful_imports += 1
                    
                    if len(shows_to_create) >= batch_size:
                        self._bulk_create_shows(shows_to_create)
                        shows_to_create = []
                
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Failed to process TV show: {row.get("name", "Unknown")}. Error: {str(e)}'))
        
        if shows_to_create:
            self._bulk_create_shows(shows_to_create)
        
        self.stdout.write(self.style.SUCCESS(f'TV show import completed. Total shows processed: {total_processed}'))
        self.stdout.write(self.style.SUCCESS(f'Successful imports: {successful_imports}'))

    @transaction.atomic
    def _bulk_create_shows(self, shows):
        TVShow.objects.bulk_create(shows, ignore_conflicts=True)