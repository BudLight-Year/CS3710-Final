from django.db import models
import tensorflow as tf
from keras.saving import register_keras_serializable
import numpy as np


# Create your models here.

class Movie(models.Model):
    movie_id = models.IntegerField(primary_key=True)
    title = models.CharField(max_length=255)
    genres = models.CharField(max_length=255)

    def __str__(self):
        return self.title


class Recommendation(models.Model):
    user = models.ForeignKey('user.Myuser', on_delete=models.DO_NOTHING, related_name="recommendations")
    preference = models.ForeignKey('recommendations.Preference', on_delete=models.CASCADE, related_name="recommendation")
    movies = models.ManyToManyField(Movie, related_name="recommendations")

    def __str__(self): 
        return f"Recommendation for {self.user.username}"


class Preference(models.Model):
    genre1 = models.CharField(max_length=255)
    genre2 = models.CharField(max_length=255, blank=True, null=True)
    genre3 = models.CharField(max_length=255, blank=True, null=True)
    genre4 = models.CharField(max_length=255, blank=True, null=True)
    genre5 = models.CharField(max_length=255, blank=True, null=True)
    include_other_genres = models.BooleanField(default=False)



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
    def __init__(self, vocabulary=None, **kwargs):
        super().__init__(**kwargs)
        self.vocabulary = vocabulary if vocabulary else []
        
        # Initialize layers
        self.string_lookup = tf.keras.layers.StringLookup(
            vocabulary=self.vocabulary,
            mask_token=None)
            
        self.embedding = tf.keras.layers.Embedding(
            input_dim=len(self.vocabulary) + 1 if vocabulary else 1000,
            output_dim=32
        )
        
        self.genre_dense1 = tf.keras.layers.Dense(64, activation='relu')
        self.genre_dense2 = tf.keras.layers.Dense(32)
        self.predictor_dense1 = tf.keras.layers.Dense(32, activation='relu')
        self.predictor_dense2 = tf.keras.layers.Dense(16, activation='relu')
        self.predictor_dense3 = tf.keras.layers.Dense(1)

    def call(self, inputs):
        # Process movie IDs
        x_movie = self.string_lookup(inputs['movieId'])
        x_movie = self.embedding(x_movie)
        
        # Process genre preferences
        x_genre = self.genre_dense1(inputs['genre_preferences'])
        x_genre = self.genre_dense2(x_genre)
        
        # Combine and predict
        if len(x_movie.shape) > 2:
            x_movie = tf.squeeze(x_movie, axis=1)
        combined = tf.concat([x_movie, x_genre], axis=1)
        
        x = self.predictor_dense1(combined)
        x = self.predictor_dense2(x)
        return self.predictor_dense3(x)

    def get_config(self):
        config = super().get_config()
        config.update({
            'vocabulary': self.vocabulary
        })
        return config
    
