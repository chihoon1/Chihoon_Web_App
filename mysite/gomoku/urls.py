from django.urls import path
from .views import MainView, PlayView, DifficultyView

app_name = 'gomoku'
urlpatterns = [
    path('', MainView.as_view(), name="main-page"),
    path('SelectDifficulty', DifficultyView.as_view(), name="select-difficulty-page"),
    path('play/', PlayView.as_view(), name="play-page"),
]
