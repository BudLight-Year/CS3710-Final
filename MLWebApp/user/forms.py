from django import forms
from allauth.account.forms import SignupForm
from .models import MyUser, Profile
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError


class UpdateAccountForm(forms.ModelForm):
    class Meta:
        model = MyUser
        fields = ('username',)

class UpdateProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('description',)


# Remove signals.py entirely and just use the form handling

class MyUserSignupForm(SignupForm):
    username = forms.CharField(max_length=30, label='Username')
    description = forms.CharField(
        widget=forms.Textarea, 
        label='Profile Description', 
        required=False
    )

    def save(self, request):
        user = super().save(request)
        description = self.cleaned_data.get('description', '')
        Profile.objects.update_or_create(
            user=user,
            defaults={'description': description}
        )
        return user
    
class CustomAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label="Email", max_length=254)


