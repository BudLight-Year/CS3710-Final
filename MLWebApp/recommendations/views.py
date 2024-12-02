from django.contrib.auth.mixins import  LoginRequiredMixin
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse
from django.views import View
from .forms import FeedbackForm, PreferenceForm
# from keras.models import load_model
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
from recommendations.utils import load_model, get_recommendations, prepare_genre_preferences 


GENRE_CHOICES = [
    'Action', 'Adventure', 'Animation', 'Children', 'Comedy',
    'Crime', 'Documentary', 'Drama', 'Fantasy', 'Film-Noir',
    'Horror', 'IMAX', 'Musical', 'Mystery', 'Romance', 'Sci-Fi',
    'Thriller', 'War', 'Western'
]


# views.py


class RecommendationEngineView(LoginRequiredMixin, View):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model, self.movies_df = load_model()
        if self.model is None or self.movies_df is None:
            raise Exception("Model or movies data could not be loaded.")

    def prepare_genre_preferences(self, preference):
        return prepare_genre_preferences(preference)

    def get_recommendations(self, genre_preferences, top_k=10):
        return get_recommendations(self.model, self.movies_df, genre_preferences, top_k)

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
                
                preference.save()
                
                recommendation = Recommendation.objects.create(
                    user=request.user,
                    preference=preference
                )
                
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
