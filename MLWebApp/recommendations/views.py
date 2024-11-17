from django.contrib.auth.mixins import  LoginRequiredMixin
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views import View
from .forms import PreferenceForm
from keras.models import load_model
import tensorflow as tf
import numpy as np
import os
from .models import Movie, MovieGenreModel, Recommendation
import pandas as pd

GENRE_CHOICES = [
    'Action', 'Adventure', 'Animation', 'Children', 'Comedy',
    'Crime', 'Documentary', 'Drama', 'Fantasy', 'Film-Noir',
    'Horror', 'IMAX', 'Musical', 'Mystery', 'Romance', 'Sci-Fi',
    'Thriller', 'War', 'Western'
]


class RecommendationEngineView(LoginRequiredMixin, View):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model = None
        self.movies_df = None
        self.load_model()

    def load_model(self):
        print("Starting model loading process...")
        
        # Get movies data and create genre columns
        movies_data = pd.DataFrame(
            list(Movie.objects.values('movie_id', 'title', 'genres', 'mean', 'count'))
        )
        movies_data['movie_id'] = movies_data['movie_id'].astype(str)
        
        # Convert genres string to binary columns
        for genre in GENRE_CHOICES:
            movies_data[genre] = movies_data['genres'].str.contains(genre, regex=False).astype(float)
        
        self.movies_df = movies_data
        
        model_path = os.path.join(os.path.dirname(__file__), 'genreModel.keras')
        
        try:
            # Create model instance with movies data
            self.model = MovieGenreModel(movies=movies_data)
            
            # Load saved weights
            self.model.load_weights(model_path)
            
            # Compile model with same parameters as training
            self.model.compile(
                optimizer=tf.keras.optimizers.Adam(0.001),
                loss=tf.keras.losses.MeanSquaredError()
            )
            
            print("Model loaded successfully!")
            
        except Exception as e:
            print(f"Error loading model: {e}")
            raise

    def prepare_genre_preferences(self, preference):
        # Create a zero array for all genres
        genre_preferences = np.zeros(len(GENRE_CHOICES))
        
        # Get all selected genres
        selected_genres = [
            preference.genre1,
            preference.genre2,
            preference.genre3,
            preference.genre4,
            preference.genre5
        ]
        
        # Remove None, empty values or empty strings
        selected_genres = [g for g in selected_genres if g and g.strip()]
        print(f"Selected genres: {selected_genres}")
        
        # Set 1 for selected genres using the correct index
        for genre in selected_genres:
            try:
                index = GENRE_CHOICES.index(genre)
                genre_preferences[index] = 1
                print(f"Setting preference 1 for {genre} at index {index}")
            except ValueError:
                print(f"Genre {genre} not found in GENRE_CHOICES")
                continue
        
        # If include_other_genres is False, set -1 for unselected genres
        if not preference.include_other_genres:
            genre_preferences = np.where(genre_preferences == 0, -1, genre_preferences)
            
        print("Generated genre preferences array:", genre_preferences)
        print("Genres with preference 1:", [GENRE_CHOICES[i] for i in range(len(genre_preferences)) if genre_preferences[i] == 1])
        return genre_preferences, selected_genres

    def get_recommendations(self, genre_preferences, top_k=10, min_ratings=50):
        """Exact implementation from training script"""
        # Filter movies with minimum number of ratings
        popular_movies = self.movies_df[self.movies_df['count'] >= min_ratings].copy()
        
        if len(popular_movies) == 0:
            print("No movies found with minimum rating count. Reducing minimum ratings requirement.")
            popular_movies = self.movies_df[self.movies_df['count'] > 0].copy()
        
        # Get model predictions
        features = {
            'movieId': tf.constant(popular_movies['movie_id'].values),
            'genre_preferences': tf.repeat(
                tf.convert_to_tensor([genre_preferences], dtype=tf.float32),
                repeats=[len(popular_movies)],
                axis=0
            )
        }
        
        predicted_scores = self.model(features)
        
        # Create preference boost scores exactly as in training
        preference_scores = np.zeros(len(popular_movies))
        for idx, pref in enumerate(genre_preferences):
            genre_name = GENRE_CHOICES[idx]
            if pref == 1:  # Preferred genres get a boost
                preference_scores += popular_movies[genre_name].values * 0.5
            elif pref == -1:  # Avoided genres get a penalty
                preference_scores -= popular_movies[genre_name].values * 1.0
        
        # Normalize preference scores to 0-1 range
        if np.ptp(preference_scores) > 0:
            preference_scores = (preference_scores - np.min(preference_scores)) / (np.ptp(preference_scores))
        
        # Convert all values to float32
        predicted_scores = tf.cast(predicted_scores, tf.float32)
        avg_ratings = tf.cast(popular_movies['mean'].values, tf.float32)
        preference_scores = tf.cast(preference_scores, tf.float32)
        
        # Normalize model predictions and average ratings
        predicted_scores = (predicted_scores - tf.reduce_min(predicted_scores)) / (
            tf.reduce_max(predicted_scores) - tf.reduce_min(predicted_scores) + 1e-8)
        avg_ratings_normalized = (avg_ratings - tf.reduce_min(avg_ratings)) / (
            tf.reduce_max(avg_ratings) - tf.reduce_min(avg_ratings) + 1e-8)
        
        # Combine scores with exact same weights as training
        final_scores = (
            0.4 * tf.squeeze(predicted_scores) +  # Model predictions
            0.3 * avg_ratings_normalized +        # Historical ratings
            0.3 * preference_scores               # Genre preferences
        )
        
        # Create and apply avoidance mask for explicitly avoided genres
        avoid_mask = np.ones(len(popular_movies), dtype=bool)
        for idx, pref in enumerate(genre_preferences):
            if pref == -1:
                genre_name = GENRE_CHOICES[idx]
                avoid_mask = avoid_mask & (popular_movies[genre_name] == 0)
        
        final_scores = tf.where(
            tf.constant(avoid_mask),
            final_scores,
            tf.fill(final_scores.shape, tf.float32.min)
        )
        
        # Get top k movies
        k = min(top_k, tf.reduce_sum(tf.cast(avoid_mask, tf.int32)))
        if k == 0:
            print("No movies found matching the avoidance criteria")
            return None
        
        _, indices = tf.math.top_k(final_scores, k=k)
        return popular_movies.iloc[indices.numpy()]

    def get(self, request):
        form = PreferenceForm()
        return render(request, 'recommendations/recommendation_engine.html', {'form': form})

    def post(self, request):
        form = PreferenceForm(request.POST)
        if form.is_valid():
            preference = form.save(commit=False)
            genre_preferences, _ = self.prepare_genre_preferences(preference)
            
            try:
                # Get recommendations using exact training implementation
                recommended_movies_df = self.get_recommendations(genre_preferences)
                
                if recommended_movies_df is None or len(recommended_movies_df) == 0:
                    form.add_error(None, "No movies found matching your criteria. Try different preferences.")
                    return render(request, 'recommendations/recommendation_engine.html', {'form': form})
                
                # Save preference and create recommendation
                preference.save()
                recommendation = Recommendation.objects.create(
                    user=request.user,
                    preference=preference
                )
                
                # Get Movie objects for recommended movies
                movie_objects = Movie.objects.filter(
                    movie_id__in=recommended_movies_df['movie_id'].tolist()
                )
                recommendation.movies.add(*movie_objects)
                
                print("Final recommendations:", [m.title for m in movie_objects])
                
                return redirect('recommendations:recommendation_detail', recommendation_id=recommendation.id)
                
            except Exception as e:
                print(f"Error getting recommendations: {e}")
                import traceback
                traceback.print_exc()
                form.add_error(None, f"Error generating recommendations: {str(e)}")
                
        return render(request, 'recommendations/recommendation_engine.html', {'form': form})
    

class RecommendationDetailView(View):
    def get(self, request, recommendation_id):
        recommendation = Recommendation.objects.get(id=recommendation_id)
        return render(request, 'recommendations/recommendation_detail.html', {'recommendation': recommendation})

