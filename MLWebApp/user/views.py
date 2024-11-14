
from django.contrib.auth import update_session_auth_hash, get_user_model
from django.contrib.auth.forms import  PasswordChangeForm
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from allauth.account.views import PasswordChangeView
from django.contrib import messages
from django.views.generic import DetailView
from django.contrib.auth.decorators import login_required
from user.forms import  AdvertiserForm, UpdateAccountForm, UpdateProfileForm


def index(request):
    current_user = request.user
    return render (request, 'user/index.html')

def update_account(request):
    # TODO add restricted access message
    if not request.user.is_authenticated:
        return redirect('index')
    if request.method == 'POST':
        form = UpdateAccountForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('user:index')
    else:
        form = UpdateAccountForm(instance=request.user)
    return render(request, 'user/update_account.html', {'form': form})

def update_profile(request):
    # TODO add restricted access message
    if not request.user.is_authenticated:
        return redirect('index')
    if request.method == 'POST':
        form = UpdateProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile', username=request.user.username) 
    else:
        form = UpdateProfileForm(instance=request.user)
    return render(request, 'user/update_account.html', {'form': form})

def change_password(request):
    if not request.user.is_authenticated:
        return redirect('index')
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important, to update the session with the new password
            return redirect('index')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'user/change_password.html', {'form': form})



class CustomPasswordChangeView(PasswordChangeView):
    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'Your password was changed successfully.')
        return HttpResponseRedirect('/users/')

class ProfileView(DetailView):
    model = get_user_model()
    template_name = 'user/profile.html'  # replace with your template
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        recipient = self.get_object()
        user = self.request.user
        return context

@login_required
def become_advertiser(request):
    if request.method == 'POST':
        form = AdvertiserForm(request.POST)
        if form.is_valid():
            request.user.is_advertiser = True
            request.user.save()
            return redirect('user:index')  # Redirect to a success page
    else:
        form = AdvertiserForm()

    return render(request, 'user/become_advertiser.html', {'form': form})
