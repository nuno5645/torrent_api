# Updated urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.HomePageView.as_view(), name='homepage'),
    path('get_movie_data/', views.HomePageView.as_view(), name='get_movie_data'),
    path('search/', views.SearchView.as_view(), name='search'),
    path('<int:movie_id>/', views.MovieDetailView.as_view(), name='movie_detail'),
    path('stream/', views.VideoStreamView.as_view(), name='video_stream'),
    path('watch_history/', views.WatchHistoryView.as_view(), name='watch_history'),
    path('tv/search/', views.TVShowSearchView.as_view(), name='tv_search'),
    path('tv/<int:show_id>/', views.TVShowDetailView.as_view(), name='tv_show_detail'),
    path('tv/stream/<int:show_id>/<int:season>/<int:episode>/<str:imdb_id>/', views.TVShowStreamView.as_view(), name='tv_stream'),
    path('tv-shows/', views.TVShowHomePageView.as_view(), name='tv_show_homepage'),
]