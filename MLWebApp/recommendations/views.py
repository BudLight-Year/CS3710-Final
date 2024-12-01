from django.contrib.auth.mixins import  LoginRequiredMixin
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse
from django.views import View
from .forms import FeedbackForm, PreferenceForm
from keras.models import load_model
import tensorflow as tf
import numpy as np
import os
from .models import EnhancedRecommender, Feedback, Movie, Recommendation
import pandas as pd
from django.views.generic import ListView
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator 
import time
from django.db.models import Avg, Count


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
        
        # Load movies data - using only fields from Movie model
        movies_data = pd.DataFrame(
            list(Movie.objects.values('movie_id', 'title', 'genres', 'mean', 'count', 'year'))
        )
        
        # Create genre columns from GENRE_CHOICES
        genres_list = movies_data['genres'].str.get_dummies(sep='|')
        
        # Ensure all GENRE_CHOICES exist as columns
        for genre in GENRE_CHOICES:
            if genre not in genres_list.columns:
                genres_list[genre] = 0
                
        # Add genre columns to dataframe
        movies_data = pd.concat([
            movies_data,
            genres_list[GENRE_CHOICES].astype(np.float32)
        ], axis=1)
        
        # Add normalized features needed by model
        movies_data['year_normalized'] = (movies_data['year'] - movies_data['year'].min()) / (
            movies_data['year'].max() - movies_data['year'].min())
        
        max_ratings = movies_data['count'].max()
        movies_data['popularity'] = (
            0.3 * movies_data['count'].div(max_ratings) +
            0.7 * movies_data['mean'].div(5.0)
        ).astype(np.float32)
        
        self.movies_df = movies_data
        
        base_dir = os.path.dirname(__file__)
        try:
            self.model = tf.keras.models.load_model(
                os.path.join(base_dir, 'movie_recommender.keras'),
                custom_objects={'EnhancedRecommender': EnhancedRecommender},
                compile=False
            )
            print("Model loaded successfully!")
            # In load_model after loading:
            print("Model architecture:")
            self.model.summary()
        except Exception as e:
            print(f"Error loading model: {e}")
            raise

    def prepare_genre_preferences(self, preference):
        """Convert Preference model data to model input format"""
        genre_preferences = np.zeros(len(GENRE_CHOICES), dtype=np.float32)
        
        # Get selected genres from Preference model fields
        selected_genres = [
            preference.genre1,
            preference.genre2,
            preference.genre3,
            preference.genre4,
            preference.genre5
        ]
        
        # Remove empty/None values
        selected_genres = [g for g in selected_genres if g]
        
        # Set selected genres to 1
        for genre in selected_genres:
            if genre in GENRE_CHOICES:
                idx = GENRE_CHOICES.index(genre)
                genre_preferences[idx] = 1
        
        # If not including other genres, set unselected to -1
        if not preference.include_other_genres:
            genre_preferences = np.where(genre_preferences == 0, -1, genre_preferences)
        
        return genre_preferences

    def get_recommendations(self, genre_preferences, top_k=10):
        """Get recommendations matching test script implementation"""
        print("Starting recommendation generation...")
        
        # Convert 1's to selected genres list
        selected_genres = [
            genre for i, genre in enumerate(GENRE_CHOICES) 
            if genre_preferences[i] == 1
        ]
        print(f"Selected genres: {selected_genres}")
        
        # Convert -1's to excluded genres list
        excluded_genres = [
            genre for i, genre in enumerate(GENRE_CHOICES) 
            if genre_preferences[i] == -1
        ]
        if excluded_genres:
            print(f"Excluding movies with genres: {excluded_genres}")
        
        # Filter out movies with excluded genres
        filtered_df = self.movies_df.copy()
        if excluded_genres:
            exclude_mask = ~filtered_df[excluded_genres].any(axis=1)
            filtered_df = filtered_df[exclude_mask]
            print(f"Filtered from {len(self.movies_df)} to {len(filtered_df)} movies after excluding genres")
        
        # Filter for minimum ratings like test script
        filtered_df = filtered_df[filtered_df['count'] >= 50]
        
        print("\nYear distribution:")
        print(filtered_df['year'].describe())
        print("\nYear normalized distribution:")
        print(filtered_df['year_normalized'].describe())

        # For a specific movie (Star Wars)
        sw = filtered_df[filtered_df['movie_id'] == 260]
        if not sw.empty:
            print("\nStar Wars details:")
            print(f"Year: {sw['year'].iloc[0]}")
            print(f"Year normalized: {sw['year_normalized'].iloc[0]}")
            print(f"Mean rating: {sw['mean'].iloc[0]}")
            print(f"Count: {sw['count'].iloc[0]}")
        
        if len(filtered_df) == 0:
            print("No movies match the criteria!")
            return None
        
        batch_size = 1000
        all_scores = []
        
        for i in range(0, len(filtered_df), batch_size):
            batch_df = filtered_df.iloc[i:i+batch_size]
            
            batch_inputs = {
                'user_preferences': tf.constant(np.repeat([genre_preferences], len(batch_df), axis=0), dtype=tf.float32),
                'movie_genres': tf.constant(batch_df[GENRE_CHOICES].values, dtype=tf.float32),
                'year': tf.constant(batch_df[['year_normalized']].values, dtype=tf.float32),
                'rating': tf.constant(batch_df[['mean']].values / 5.0, dtype=tf.float32),
                'popularity': tf.constant(batch_df[['popularity']].values, dtype=tf.float32)
            }
            
            # Debug prints for input shapes and values
            print(f"\nBatch {i//batch_size + 1}:")
            for key, value in batch_inputs.items():
                print(f"{key} shape: {value.shape}")
                print(f"{key} contains nan: {tf.reduce_any(tf.math.is_nan(value))}")
                if tf.reduce_any(tf.math.is_nan(value)):
                    print(f"First few values: {value[:5]}")

            # Need training to be true to let dropouts work.
            # but training being on causes model to not work appropiately
            batch_scores = self.model.predict(batch_inputs, verbose=0).flatten()
            #batch_scores = self.model(batch_inputs, training=True).numpy().flatten()

            print("Batch predictions contain nan:", np.any(np.isnan(batch_scores)))
            all_scores.extend(batch_scores)
        
        scores = np.array(all_scores)
        print("\nInitial scores shape:", scores.shape)
        print("Any nans in initial scores?", np.any(np.isnan(scores)))
        
        scores = (scores - scores.min()) / (scores.max() - scores.min() + 1e-10)
        print("Any nans after normalization?", np.any(np.isnan(scores)))
        
        filtered_df['weighted_rating'] = filtered_df['mean'] * \
            np.log1p(filtered_df['count']) / np.log1p(filtered_df['count'].max())
        print("Any nans in weighted_rating?", np.any(np.isnan(filtered_df['weighted_rating'])))
        
        scores = 0.7 * scores + 0.3 * filtered_df['weighted_rating'].values
        print("Any nans in final scores?", np.any(np.isnan(scores)))
        
        top_indices = np.argsort(scores)[-top_k:][::-1]
        recommendations = filtered_df.iloc[top_indices].copy()
        recommendations['match_score'] = scores[top_indices]
        recommendations['matched_genres'] = recommendations.apply(
            lambda x: [g for g in selected_genres if x[g] == 1],
            axis=1
        )
        
        print("\nExample top recommendations:")
        for _, movie in recommendations.head(3).iterrows():
            print(f"{movie['title']}")
            print(f"Rating: {movie['mean']:.1f} ({movie['count']} ratings)")
            print(f"Genres: {movie['genres']}")
            print(f"Match score: {movie['match_score']:.3f}\n")
        
        return recommendations[['movie_id', 'match_score']]
    
    def get(self, request):
        form = PreferenceForm()
        return render(request, 'recommendations/recommendation_engine.html', {'form': form})

    def post(self, request):
        form = PreferenceForm(request.POST)
        if form.is_valid():
            preference = form.save(commit=False)
            genre_preferences = self.prepare_genre_preferences(preference)
            
            try:
                recommended_movies_df = self.get_recommendations(genre_preferences)
                
                if recommended_movies_df is None or len(recommended_movies_df) == 0:
                    form.add_error(None, "No movies found matching your criteria. Try different preferences.")
                    return render(request, 'recommendations/recommendation_engine.html', {'form': form})
                
                # Save preference
                preference.save()
                
                # Create recommendation
                recommendation = Recommendation.objects.create(
                    user=request.user,
                    preference=preference
                )
                
                # Get Movie objects and add to recommendation
                recommended_movies = Movie.objects.filter(
                    movie_id__in=recommended_movies_df['movie_id'].tolist()
                )
                recommendation.movies.add(*recommended_movies)
                
                return redirect('recommendations:recommendation_detail', recommendation_id=recommendation.id)
                
            except Exception as e:
                print(f"Error getting recommendations: {e}")
                import traceback
                traceback.print_exc()
                form.add_error(None, f"Error generating recommendations: {str(e)}")
                
        return render(request, 'recommendations/recommendation_engine.html', {'form': form})
    
# Shows single recommendation
class RecommendationDetailView(View):
    def get(self, request, recommendation_id):
        # Queries database for the specific recommendation based on it's id
        recommendation = get_object_or_404(Recommendation, id=recommendation_id)
        form = FeedbackForm()
        return render(request, 'recommendations/recommendation_detail.html', {
            'recommendation': recommendation,
            'form': form,
            'submitted': False
        })

    def post(self, request, recommendation_id):
        recommendation = get_object_or_404(Recommendation, id=recommendation_id)
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback_value = form.cleaned_data['feedback']
            feedback = Feedback(feedback=feedback_value, recommendation=recommendation)
            feedback.save()
            return render(request, 'recommendations/recommendation_detail.html', {
                'recommendation': recommendation,
                'form': FeedbackForm(),  # Reset the form
                'submitted': True
            })
        return render(request, 'recommendations/recommendation_detail.html', {
            'recommendation': recommendation,
            'form': form,
            'submitted': False
        })

# Shows all recommendations
class RecommendationsListView(ListView):
    # Django's ListView automatically queries all entities for the selected model
    model = Recommendation
    template_name = 'recommendations/recommendation_list.html'
    context_object_name = 'recommendations'
    paginate_by = 10  # Number of recommendations per page

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        paginator = Paginator(self.get_queryset(), self.paginate_by)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context['page_obj'] = page_obj
        return context


# recommendation deletion view
@login_required
def delete_recommendation(request, recommendation_id):
    # Ensures recommendation exists for current user, prevents users from deleting other users recommendations
    recommendation = get_object_or_404(Recommendation, id=recommendation_id, user=request.user) 
    recommendation.delete()
    return redirect('user:profile', username = request.user.username)  
