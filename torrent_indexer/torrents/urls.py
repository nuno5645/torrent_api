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
]