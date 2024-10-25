from django.contrib import admin
from .models import Movie, WatchHistory, StreamingList, StreamingListMovie, Torrent, RealDebrid, TVShow, Season, Episode, TVShowWatchHistory, TVShowStreamingList, TVShowStreamingListShow, Source

# Register your models here
admin.site.register(Movie)
admin.site.register(WatchHistory)
admin.site.register(StreamingList)
admin.site.register(StreamingListMovie)
admin.site.register(Torrent)
admin.site.register(RealDebrid)
admin.site.register(TVShow)
admin.site.register(Season)
admin.site.register(Episode)
admin.site.register(TVShowWatchHistory)
admin.site.register(TVShowStreamingList)
admin.site.register(TVShowStreamingListShow)
admin.site.register(Source)
