from django.urls import path, reverse_lazy
from .views import RecommendationDetailView, RecommendationEngineView, RecommendationsListView

app_name = "recommendations"
urlpatterns = [
    path("engine", RecommendationEngineView.as_view(), name='engine'),
    path('<int:recommendation_id>/', RecommendationDetailView.as_view(), name='recommendation_detail'),
    path('', RecommendationsListView.as_view(), name='recommendations_list'),
]
