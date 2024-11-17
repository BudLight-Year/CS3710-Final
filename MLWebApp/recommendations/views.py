from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views import View
from .forms import PreferenceForm
from keras.models import load_model
import tensorflow as tf
import numpy as np
import os
from .models import MovieGenreModel  # Import the model class we just created

# Load the Keras model (relative path) 
model_path = os.path.join(os.path.dirname(__file__), 'genreModel.keras')

try:
    # Load the model with compile=False first
    model = load_model(
        model_path, 
        custom_objects={'MovieGenreModel': MovieGenreModel}, 
        compile=False
    )
    
    # Then compile it after loading
    model.compile(
        optimizer=tf.keras.optimizers.Adam(0.001),
        loss=tf.keras.losses.MeanSquaredError()
    )
except Exception as e:
    print(f"Error loading model: {e}")
    raise


GENRE_CHOICES = [
    'Action', 'Adventure', 'Animation', 'Children', 'Comedy',
    'Crime', 'Documentary', 'Drama', 'Fantasy', 'Film-Noir',
    'Horror', 'IMAX', 'Musical', 'Mystery', 'Romance', 'Sci-Fi',
    'Thriller', 'War', 'Western'
]

class CreatePreferenceView(View):
    def get(self, request):
        form = PreferenceForm()
        return render(request, 'create_preference.html', {'form': form})

    def post(self, request):
        form = PreferenceForm(request.POST)
        if form.is_valid():
            preference = form.save(commit=False)
            genre_preferences = self.prepare_genre_preferences(preference)
            
            # Create the input structure the model expects
            model_input = {
                'movieId': tf.constant(['1']),  # Example movieId, adjust as needed
                'genre_preferences': tf.constant([genre_preferences], dtype=tf.float32)
            }
            
            predictions = model.predict(model_input)
            return HttpResponse(f'Model Predictions: {predictions}')
        return render(request, 'create_preference.html', {'form': form})

    def prepare_genre_preferences(self, preference):
        genre_preferences = np.zeros(len(GENRE_CHOICES))
        selected_genres = [
            preference.genre1, preference.genre2, preference.genre3,
            preference.genre4, preference.genre5
        ]
        
        for i, genre in enumerate(GENRE_CHOICES):
            if genre in selected_genres:
                genre_preferences[i] = 1
            elif preference.include_other_genres:
                genre_preferences[i] = 0
            else:
                genre_preferences[i] = -1
                
        return genre_preferences