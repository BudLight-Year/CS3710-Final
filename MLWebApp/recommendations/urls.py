from django.urls import path, reverse_lazy
from .views import RecommendationDetailView, RecommendationEngineView

app_name = "recommendations"
urlpatterns = [
    #path("", views.index, name="index"),
    path("engine", RecommendationEngineView.as_view(), name='engine'),
    path('<int:recommendation_id>/', RecommendationDetailView.as_view(), name='recommendation_detail'),
]
