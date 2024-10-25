from django.core.management.base import BaseCommand
from django.shortcuts import get_object_or_404
from ...models import TVShow, Source

class Command(BaseCommand):
    help = 'Check sources for a given TV show episode'

    def add_arguments(self, parser):
        parser.add_argument('tmdb_id', type=int, help='TMDB ID of the TV show')
        parser.add_argument('season', type=int, help='Season number')
        parser.add_argument('episode', type=int, help='Episode number')

    def handle(self, *args, **options):
        tmdb_id = options['tmdb_id']
        season = options['season']
        episode = options['episode']

        episode_urls = self.get_episode_urls(tmdb_id, season, episode)
        for source_id, url in episode_urls.items():
            self.stdout.write(f"{source_id}: {url}")

    def get_episode_urls(self, tmdb_id, season, episode):
        # Fetch the TV show
        tv_show = get_object_or_404(TVShow, tmdb_id=tmdb_id)

        # Get all active sources
        sources = Source.objects.filter(is_active=True, has_tv_shows=True).order_by('priority')

        # Generate URLs for each source
        urls = {}
        for source in sources:
            url = source.get_tv_show_url(tv_show, season, episode)
            if url:
                urls[source.id] = url

        return urls

# Remove the example usage code