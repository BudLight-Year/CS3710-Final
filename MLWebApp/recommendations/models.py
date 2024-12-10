from django.db import models
import tensorflow as tf
from keras.saving import register_keras_serializable
import numpy as np


# Create your models here.

from django.db import models

GENRE_CHOICES = [
    'Action', 'Adventure', 'Animation', 'Children', 'Comedy',
    'Crime', 'Documentary', 'Drama', 'Fantasy', 'Film-Noir',
    'Horror', 'IMAX', 'Musical', 'Mystery', 'Romance', 'Sci-Fi',
    'Thriller', 'War', 'Western'
]
# Movie model to load MoviLens movie data into
class Movie(models.Model):
    movie_id = models.IntegerField(primary_key=True)
    title = models.CharField(max_length=255)
    genres = models.CharField(max_length=255)
    mean = models.FloatField(default=0)  # Average rating
    count = models.IntegerField(default=0)  # Number of ratings
    year = models.IntegerField(default=0)

    def __str__(self):
        return self.title

    # Use this for user view, shows rounded mean 
    def rounded_mean(self, decimals=2):
        """Return the average rating rounded to the specified number of decimal places."""
        return round(self.mean, decimals)



# Model to save recommendations into
class Recommendation(models.Model):
    user = models.ForeignKey('user.Myuser', on_delete=models.DO_NOTHING, related_name="recommendations")
    preference = models.ForeignKey('recommendations.Preference', on_delete=models.CASCADE, related_name="recommendation")
    movies = models.ManyToManyField(Movie, related_name="recommendations")
    date_created = models.DateTimeField(auto_now_add=True)


    def __str__(self): 
        return f"Recommendation for {self.user.username}"

# Model to save user preference into
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

# Logs user feedback on how good recommendation was.
class Feedback(models.Model):
    feedback = models.BooleanField()
    recommendation = models.ForeignKey('recommendations.Recommendation', on_delete=models.CASCADE, related_name='feedback')
        

#------------------------#
#                        #
#      ML MODEL          #
#                        # 
#------------------------#

# Multi Layered Neural Network which takes user genre preferences and matches movies primarily based on genres and ratings

@register_keras_serializable()
class EnhancedRecommender(tf.keras.Model):
    def __init__(self, trainable=True, dtype=None, **kwargs):
        super().__init__(trainable=trainable, dtype=dtype, **kwargs)
        
        self.dropout1 = tf.keras.layers.Dropout(0.2)
        self.dropout2 = tf.keras.layers.Dropout(0.1)
        self.dropout3 = tf.keras.layers.Dropout(0.15)
        
        self.genre_matching = tf.keras.Sequential([
            tf.keras.layers.InputLayer(input_shape=(len(GENRE_CHOICES) * 2,)),
            tf.keras.layers.Dense(128, activation='relu'),
            tf.keras.layers.BatchNormalization(),
            tf.keras.layers.Dense(64, activation='relu'),
            tf.keras.layers.Dense(1)
        ])
        
        self.preference_net = tf.keras.Sequential([
            tf.keras.layers.InputLayer(input_shape=(len(GENRE_CHOICES),)),
            tf.keras.layers.Dense(256, activation='relu'),
            tf.keras.layers.BatchNormalization(),
            tf.keras.layers.Dropout(0.3),
            tf.keras.layers.Dense(128, activation='relu'),
            tf.keras.layers.Dense(64, activation='relu')
        ])
        
        self.movie_net = tf.keras.Sequential([
            tf.keras.layers.InputLayer(input_shape=(len(GENRE_CHOICES),)),
            tf.keras.layers.Dense(256, activation='relu'),
            tf.keras.layers.BatchNormalization(),
            tf.keras.layers.Dropout(0.3),
            tf.keras.layers.Dense(128, activation='relu'),
            tf.keras.layers.Dense(64, activation='relu')
        ])
        
        # Changed input shape to 2 to match trained model
        self.metadata_net = tf.keras.Sequential([
            tf.keras.layers.InputLayer(input_shape=(2,)),  # year and popularity only
            tf.keras.layers.Dense(64, activation='relu'),
            tf.keras.layers.BatchNormalization(),
            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.Dense(16, activation='relu')
        ])
        
        self.match_net = tf.keras.Sequential([
            tf.keras.layers.Dense(256, activation='relu'),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(128, activation='relu'),
            tf.keras.layers.Dense(64, activation='relu'),
            tf.keras.layers.Dense(1)
        ])

    def call(self, inputs, training=True):
        genre_concat = tf.concat([inputs['user_preferences'], inputs['movie_genres']], axis=1)
        genre_match_score = self.genre_matching(genre_concat)
        
        pref_features = self.preference_net(inputs['user_preferences'])
        pref_features = self.dropout1(pref_features, training=training)
        
        movie_features = self.movie_net(inputs['movie_genres'])
        movie_features = self.dropout2(movie_features, training=training)
        
        # Changed to match trained model (removed rating)
        metadata = tf.concat([inputs['year'], inputs['popularity']], axis=1)
        metadata_features = self.metadata_net(metadata)
        metadata_features = self.dropout3(metadata_features, training=training)
        
        combined = tf.concat([
            pref_features,
            movie_features,
            metadata_features,
            genre_match_score  # Removed the * 0.1 scaling factor to match trained model
        ], axis=1)
        
        return self.match_net(combined)

    def get_config(self):
        config = super().get_config()
        return config

    @classmethod
    def from_config(cls, config):
        return cls(**config)


    
