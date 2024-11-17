from django import forms
from .models import Preference

GENRE_CHOICES = [
    ('Action', 'Action'),
    ('Adventure', 'Adventure'),
    ('Animation', 'Animation'),
    ('Children', 'Children'),
    ('Comedy', 'Comedy'),
    ('Crime', 'Crime'),
    ('Documentary', 'Documentary'),
    ('Drama', 'Drama'),
    ('Fantasy', 'Fantasy'),
    ('Film-Noir', 'Film-Noir'),
    ('Horror', 'Horror'),
    ('IMAX', 'IMAX'),
    ('Musical', 'Musical'),
    ('Mystery', 'Mystery'),
    ('Romance', 'Romance'),
    ('Sci-Fi', 'Sci-Fi'),
    ('Thriller', 'Thriller'),
    ('War', 'War'),
    ('Western', 'Western'),
]

class PreferenceForm(forms.ModelForm):
    genre1 = forms.ChoiceField(choices=GENRE_CHOICES)
    genre2 = forms.ChoiceField(choices=GENRE_CHOICES, required=False)
    genre3 = forms.ChoiceField(choices=GENRE_CHOICES, required=False)
    genre4 = forms.ChoiceField(choices=GENRE_CHOICES, required=False)
    genre5 = forms.ChoiceField(choices=GENRE_CHOICES, required=False)
    include_other_genres = forms.BooleanField(required=False, help_text="Include genres not listed above")
    
    class Meta:
        model = Preference
        fields = ['genre1', 'genre2', 'genre3', 'genre4', 'genre5', 'include_other_genres']
