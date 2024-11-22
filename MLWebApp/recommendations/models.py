from django.db import models
import tensorflow as tf
from keras.saving import register_keras_serializable
import numpy as np


# Create your models here.

class Movie(models.Model):
    movie_id = models.IntegerField(primary_key=True)
    title = models.CharField(max_length=255)
    genres = models.CharField(max_length=255)
    mean = models.FloatField(default=0)  # Average rating
    count = models.IntegerField(default=0)  # Number of ratings

    def __str__(self):
        return self.title


class Recommendation(models.Model):
    user = models.ForeignKey('user.Myuser', on_delete=models.DO_NOTHING, related_name="recommendations")
    preference = models.ForeignKey('recommendations.Preference', on_delete=models.CASCADE, related_name="recommendation")
    movies = models.ManyToManyField(Movie, related_name="recommendations")
    date_created = models.DateTimeField(auto_now_add=True)


    def __str__(self): 
        return f"Recommendation for {self.user.username}"


class Preference(models.Model):
    genre1 = models.CharField(max_length=255, blank=True, null=True)
    genre2 = models.CharField(max_length=255, blank=True, null=True)
    genre3 = models.CharField(max_length=255, blank=True, null=True)
    genre4 = models.CharField(max_length=255, blank=True, null=True)
    genre5 = models.CharField(max_length=255, blank=True, null=True)
    include_other_genres = models.BooleanField(default=True)
    
    def __str__(self):
        # Get all non-empty genres
        genres = [
            self.genre1, self.genre2, self.genre3, 
            self.genre4, self.genre5
        ]
        selected_genres = [g for g in genres if g]
        return f"Preference: {', '.join(selected_genres)}"


# Do this one last
class SimilarMovie(models.Model):
    pass


#------------------------#
#                        #
#      ML MODEL          #
#                        #
#------------------------#

@register_keras_serializable()
class MovieGenreModel(tf.keras.Model):
    def __init__(self, movies=None, **kwargs):
        super().__init__(**kwargs)
        self.vocabulary = None if movies is None else movies['movie_id'].unique().astype(str)
        
        # Initialize layers to match training architecture
        self.movie_embedding = tf.keras.Sequential([
            tf.keras.layers.StringLookup(
                vocabulary=self.vocabulary,
                mask_token=None),
            tf.keras.layers.Embedding(
                input_dim=len(self.vocabulary) + 1 if self.vocabulary is not None else 1000,
                output_dim=32)
        ])
        
        self.genre_embedding = tf.keras.Sequential([
            tf.keras.layers.Dense(64, activation='relu'),
            tf.keras.layers.Dense(32)
        ])
        
        self.rating_predictor = tf.keras.Sequential([
            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.Dense(16, activation='relu'),
            tf.keras.layers.Dense(1)
        ])

    def call(self, inputs):
        movie_emb = self.movie_embedding(inputs['movieId'])
        genre_emb = self.genre_embedding(inputs['genre_preferences'])
        combined = tf.concat([movie_emb, genre_emb], axis=1)
        return self.rating_predictor(combined)

    def get_config(self):
        config = super().get_config()
        config.update({
            'vocabulary': self.vocabulary.tolist() if self.vocabulary is not None else None
        })
        return config

    @classmethod
    def from_config(cls, config):
        # Convert vocabulary back to numpy array if it exists
        if config['vocabulary'] is not None:
            config['vocabulary'] = np.array(config['vocabulary'])
        return cls(**config)
    
