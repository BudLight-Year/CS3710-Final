from django.db import models
import tensorflow as tf
from keras.saving import register_keras_serializable

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
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Initialize layers with None - they will be properly configured when the model is loaded
        self.movie_embedding = None
        self.genre_embedding = None
        self.rating_predictor = None
        
    def build(self, input_shape):
        # This method is called when the model is being built/loaded
        if self.movie_embedding is None:
            self.movie_embedding = tf.keras.Sequential([
                tf.keras.layers.StringLookup(mask_token=None),
                tf.keras.layers.Embedding(
                    input_dim=1000,  # This will be configured from saved weights
                    output_dim=32
                )
            ])
            
        if self.genre_embedding is None:
            self.genre_embedding = tf.keras.Sequential([
                tf.keras.layers.Dense(64, activation='relu'),
                tf.keras.layers.Dense(32)
            ])
            
        if self.rating_predictor is None:
            self.rating_predictor = tf.keras.Sequential([
                tf.keras.layers.Dense(32, activation='relu'),
                tf.keras.layers.Dense(16, activation='relu'),
                tf.keras.layers.Dense(1)
            ])
        
        super().build(input_shape)

    def call(self, inputs):
        movie_emb = self.movie_embedding(inputs['movieId'])
        genre_emb = self.genre_embedding(inputs['genre_preferences'])
        combined = tf.concat([movie_emb, genre_emb], axis=1)
        return self.rating_predictor(combined)

    def get_config(self):
        config = super().get_config()
        return config

