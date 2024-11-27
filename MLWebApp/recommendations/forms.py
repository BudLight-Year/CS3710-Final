from django import forms
from .models import Feedback, Preference
from .constants import GENRE_CHOICES


class PreferenceForm(forms.ModelForm):
    genre1 = forms.ChoiceField(choices=GENRE_CHOICES, required=False, initial='')
    genre2 = forms.ChoiceField(choices=GENRE_CHOICES, required=False, initial='')
    genre3 = forms.ChoiceField(choices=GENRE_CHOICES, required=False, initial='')
    genre4 = forms.ChoiceField(choices=GENRE_CHOICES, required=False, initial='')
    genre5 = forms.ChoiceField(choices=GENRE_CHOICES, required=False, initial='')
    include_other_genres = forms.BooleanField(
        required=False, 
        help_text="Include genres not listed above",
        initial=True
    )
    
    class Meta:
        model = Preference
        fields = ['genre1', 'genre2', 'genre3', 'genre4', 'genre5', 'include_other_genres']

    def clean(self):
        cleaned_data = super().clean()
        
        # Get all genre selections
        genres = [
            cleaned_data.get('genre1'),
            cleaned_data.get('genre2'),
            cleaned_data.get('genre3'),
            cleaned_data.get('genre4'),
            cleaned_data.get('genre5')
        ]
        
        # Check if at least one genre is selected (not empty)
        if not any(genre for genre in genres if genre):
            raise forms.ValidationError(
                "Please select at least one genre in any of the fields.",
                code='no_genre_selected'
            )
        
        return cleaned_data
    

class FeedbackForm(forms.Form):
    feedback = forms.ChoiceField(
        choices=[(True, 'Good'), (False, 'Bad')],
        widget=forms.RadioSelect
    )

