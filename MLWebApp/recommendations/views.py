from django.contrib.auth.mixins import  LoginRequiredMixin
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views import View
from .forms import PreferenceForm
from keras.models import load_model
import tensorflow as tf
import numpy as np
import os
from .models import Movie, MovieGenreModel, Recommendation  # Import the model class we just created


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
        self.load_model()

    def load_model(self):
        print("Starting model loading process...")
        
        # Get vocabulary FIRST
        movie_ids = list(Movie.objects.values_list('movie_id', flat=True))
        vocabulary = [str(mid) for mid in sorted(movie_ids)]
        
        print(f"Created vocabulary with {len(vocabulary)} items")
        print(f"Sample vocabulary: {vocabulary[:5]}")
        
        model_path = os.path.join(os.path.dirname(__file__), 'genreModel.keras')
        
        try:
            # Create model instance with vocabulary first
            custom_model = MovieGenreModel(vocabulary=vocabulary)
            
            # Load saved weights
            custom_model.load_weights(model_path)
            
            # Compile model
            custom_model.compile(
                optimizer=tf.keras.optimizers.Adam(0.001),
                loss=tf.keras.losses.MeanSquaredError()
            )
            
            self.model = custom_model
            print("Model loaded successfully!")
            
        except Exception as e:
            print(f"Error loading model: {e}")
            print(f"Current frame locals: {locals()}")
            raise

    def get(self, request):
        form = PreferenceForm()
        return render(request, 'recommendations/recommendation_engine.html', {'form': form})

    def post(self, request):
        form = PreferenceForm(request.POST)
        if form.is_valid():
            preference = form.save(commit=False)
            genre_preferences = self.prepare_genre_preferences(preference)
            
            try:
                # Get all movies
                all_movies = list(Movie.objects.all())
                movie_ids = [str(movie.movie_id) for movie in all_movies]
                
                # Convert inputs to appropriate tensors
                movie_id_tensor = tf.convert_to_tensor(movie_ids)
                genre_preferences_tensor = tf.convert_to_tensor([genre_preferences], dtype=tf.float32)
                
                # Prepare input dictionary
                model_input = {
                    'movieId': movie_id_tensor,
                    'genre_preferences': tf.repeat(
                        genre_preferences_tensor,
                        repeats=[len(movie_ids)],
                        axis=0
                    )
                }
                
                print("Model input shapes:")
                print("movieId shape:", tf.shape(model_input['movieId']))
                print("genre_preferences shape:", tf.shape(model_input['genre_preferences']))
                
                # Make predictions in batches to avoid memory issues
                BATCH_SIZE = 1000
                all_predictions = []
                
                for i in range(0, len(movie_ids), BATCH_SIZE):
                    batch_movies = movie_ids[i:i + BATCH_SIZE]
                    batch_input = {
                        'movieId': tf.convert_to_tensor(batch_movies),
                        'genre_preferences': tf.convert_to_tensor(
                            [genre_preferences] * len(batch_movies),
                            dtype=tf.float32
                        )
                    }
                    batch_predictions = self.model.predict(batch_input, verbose=0)
                    all_predictions.extend(batch_predictions.flatten())
                
                # Convert predictions to numpy array
                predictions = np.array(all_predictions)
                
                # Get top 10 movies
                top_indices = np.argsort(predictions)[-10:][::-1]
                recommended_movies = [all_movies[i] for i in top_indices]
                
                print("Found recommendations:", [m.title for m in recommended_movies])
                
                # Save preference
                preference.save()
                
                # Create recommendation
                recommendation = Recommendation.objects.create(
                    user=request.user,
                    preference=preference
                )
                
                # Add recommended movies
                recommendation.movies.add(*recommended_movies)
                
                return redirect('recommendations:recommendation_detail', recommendation_id=recommendation.id)
                
            except Exception as e:
                print(f"Error getting recommendations: {e}")
                print(f"Type of error: {type(e)}")
                import traceback
                traceback.print_exc()
                form.add_error(None, f"Error generating recommendations: {str(e)}")
                
        return render(request, 'recommendations/recommendation_engine.html', {'form': form})
    
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
        
        # Remove None or empty values
        selected_genres = [g for g in selected_genres if g]
        
        # Set 1 for selected genres
        for genre in selected_genres:
            try:
                index = [g[0] for g in GENRE_CHOICES].index(genre)
                genre_preferences[index] = 1
            except ValueError:
                continue
        
        # If include_other_genres is False, set -1 for unselected genres
        if not preference.include_other_genres:
            genre_preferences = np.where(genre_preferences == 0, -1, genre_preferences)
            
        print("Generated genre preferences:", genre_preferences)
        return genre_preferences
    

class RecommendationDetailView(View):
    def get(self, request, recommendation_id):
        recommendation = Recommendation.objects.get(id=recommendation_id)
        return render(request, 'recommendations/recommendation_detail.html', {'recommendation': recommendation})

