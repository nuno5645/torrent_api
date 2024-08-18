# Updated urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.HomePageView.as_view(), name='homepage'),
    path('get_movie_data/', views.HomePageView.as_view(), name='get_movie_data'),
    path('trending/', views.TrendingView.as_view(), name='trending'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('<int:movie_id>/', views.MovieDetailView.as_view(), name='movie_detail'),
    path('stream/<path:video_url>/', views.VideoStreamView.as_view(), name='video_stream'),
]