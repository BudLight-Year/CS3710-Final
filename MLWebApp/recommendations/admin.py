from django.contrib import admin
from .models import Preference, Recommendation, Movie, Feedback

# Register your models here.
admin.site.register(Preference)
admin.site.register(Recommendation)
admin.site.register(Movie)
admin.site.register(Feedback)
