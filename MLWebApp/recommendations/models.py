from django.db import models

# Create your models here.

class Movie(models.Model):
    movie_id = models.IntegerField(primary_key=True)
    title = models.CharField(max_length=255)
    genres = models.CharField(max_length=255)

    def __str__(self):
        return self.title


class Recommendation(models.Model):
    user = models.ForeignKey('user.Myuser', on_delete=models.DO_NOTHING, related_name="recommendations")
    movies = models.ManyToManyField(Movie, related_name="recommendations")

    def __str__(self): 
        return f"Recommendation for {self.user.username}"


class Preference(models.Model):
    recommendation = models.ForeignKey('recommendations.Recommendation', on_delete=models.CASCADE, related_name="recommendation")
    genre1 = models.CharField(max_length=255)
    genre2 = models.CharField(max_length=255, blank=True, null=True)
    genre3 = models.CharField(max_length=255, blank=True, null=True)
    genre4 = models.CharField(max_length=255, blank=True, null=True)
    genre5 = models.CharField(max_length=255, blank=True, null=True)



# Do this one last
class SimilarMovie(models.Model):
    pass

