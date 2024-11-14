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

class MyUserSignupForm(SignupForm):
    email = forms.EmailField(max_length=255, label='Email')
    username = forms.CharField(max_length=30, label='Username')
    password1 = forms.CharField(widget=forms.PasswordInput, label='Password')
    password2 = forms.CharField(widget=forms.PasswordInput, label='Password confirmation')
    description = forms.CharField(widget=forms.Textarea, label='Profile Description', required=False)

    def save(self, request):
        email = self.cleaned_data['email']
        username = self.cleaned_data['username']
        password = self.cleaned_data['password1']
        description = self.cleaned_data['description']
        user = MyUser.objects.create_user(email, username, password)
        user.save()
        Profile.objects.create(user=user, description=description)
        return user
    
class CustomAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label="Email", max_length=254)

class AdvertiserForm(forms.Form):
    is_advertiser = forms.CharField(max_length=10)

    def clean_is_advertiser(self):
        data = self.cleaned_data['is_advertiser']
        if data.lower() != 'yes':
            raise forms.ValidationError("You must type 'yes' to become an advertiser.")
        return data

