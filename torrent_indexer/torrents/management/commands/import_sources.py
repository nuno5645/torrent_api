from django.core.management.base import BaseCommand
from torrents.models import Source

class Command(BaseCommand):
    help = 'Adds predefined sources to the database'

    def handle(self, *args, **options):
        sources = [
            {
                'name': 'VidSrc',
                'base_url': 'https://vidsrc.xyz/embed/',
                'has_tv_shows': True,
                'uses_tmdb': True,
                'movie_path': 'movie/{id}',
                'tv_show_path': 'tv/{id}/{season}/{episode}',
                'priority': 1,
            },
            {
                'name': 'VidSrc Pro',
                'base_url': 'https://vidsrc.pro/embed/',
                'has_tv_shows': True,
                'uses_tmdb': True,
                'movie_path': 'movie/{id}',
                'tv_show_path': 'tv/{id}/{season}/{episode}',
                'priority': 2,
            },
            {
                'name': 'WarezCDN',
                'base_url': 'https://embed.warezcdn.com/',
                'has_tv_shows': True,
                'uses_tmdb': False,
                'movie_path': 'filme/{id}',
                'tv_show_path': 'serie/{id}/{season}/{episode}',
                'priority': 3,
            },
            {
                'name': 'Moviee',
                'base_url': 'https://moviee.tv/embed/',
                'has_tv_shows': True,
                'uses_tmdb': True,
                'movie_path': 'movie/{id}',
                'tv_show_path': 'tv/{id}?season={season}&episode={episode}',
                'priority': 4,
            },
            {
                'name': 'EmbedFlix',
                'base_url': 'https://www.embedflix.win/embed/',
                'has_tv_shows': True,
                'uses_tmdb': True,
                'movie_path': 'movie/{id}',
                'tv_show_path': 'tv/{id}/{season}/{episode}',
                'priority': 5,
            },
            {
                'name': 'MovieAPI',
                'base_url': 'https://moviesapi.club/',
                'has_tv_shows': False,
                'uses_tmdb': True,
                'movie_path': 'movie/{id}',
                'tv_show_path': '',
                'priority': 6,
            },
            {
                'name': 'VidSrc CC',
                'base_url': 'https://vidsrc.cc/v2/embed/',
                'has_tv_shows': True,
                'uses_tmdb': True,
                'movie_path': 'movie/{id}',
                'tv_show_path': 'tv/{id}/{season}/{episode}',
                'priority': 7,
            },
            {
                'name': 'MultiEmbed',
                'base_url': 'https://multiembed.mov/',
                'has_tv_shows': False,
                'uses_tmdb': True,
                'movie_path': '?video_id={id}&tmdb=1',
                'tv_show_path': '',
                'priority': 8,
            },
            {
                'name': 'embed.su',
                'base_url': 'https://embed.su/embed/',
                'has_tv_shows': True,
                'uses_tmdb': True,
                'movie_path': 'movie/{id}',
                'tv_show_path': 'tv/{id}/{season}/{episode}',
                'priority': 9,
            },
            {
                'name': 'AutoEmbed',
                'base_url': 'https://player.autoembed.cc/embed/',
                'has_tv_shows': True,
                'uses_tmdb': True,
                'movie_path': 'movie/{id}',
                'tv_show_path': 'tv/{id}/{season}/{episode}',
                'priority': 10,
            },
            {
                'name': '2Embed',
                'base_url': 'https://www.2embed.stream/embed/',
                'has_tv_shows': True,
                'uses_tmdb': True,
                'movie_path': 'movie/{id}',
                'tv_show_path': 'tv/{id}/{season}/{episode}',
                'priority': 11,
            },
            {
                'name': 'Vidsrc.to',
                'base_url': 'https://vidsrc.to/embed/',
                'has_tv_shows': True,
                'uses_tmdb': True,
                'movie_path': 'movie/{id}',
                'tv_show_path': 'tv/{id}/{season}/{episode}',
                'priority': 12,
            },
        ]

        for source_data in sources:
            source, created = Source.objects.update_or_create(
                name=source_data['name'],
                defaults=source_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Successfully added source: {source.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Updated existing source: {source.name}'))

        self.stdout.write(self.style.SUCCESS('All sources have been added or updated successfully.'))