from django.db import models

# Create your models here.
class Gomoku(models.Model):
    # every attribute is a string form of json data type
    grid = models.TextField()
    number_turns = models.TextField()
    whose_turn = models.TextField()
    difficulty_level = models.TextField(default=None)  # used when playing game against computer player
    player1_name = models.TextField()
    player1_color = models.TextField()
    player2_name = models.TextField()
    player2_color = models.TextField()
