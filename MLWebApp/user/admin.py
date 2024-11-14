from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from .models import MyUser
from allauth.account.models import EmailConfirmation, EmailConfirmationHMAC, EmailAddress
from allauth.account.adapter import get_adapter
from django.utils import timezone
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth.models import Group


class UserAdmin(DefaultUserAdmin):
    list_display = ('email', 'username', 'is_staff', 'is_active')
    list_filter = ('is_staff',)
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Permissions', {'fields': ('is_staff',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2')}
        ),
    )
    search_fields = ('email', 'username')
    ordering = ('email',)
    filter_horizontal = ()

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        # If the user is being created (and not changed)
        if not change:
            # Create EmailAddress object
            email_address = EmailAddress.objects.create(user=obj, email=obj.email, verified=True, primary=True)

            # Create email confirmation object
            #email_confirmation = EmailConfirmation.create(email_address)
            #email_confirmation.sent = timezone.now()
            #email_confirmation.save()

            # Send confirmation email
            # get_adapter().send_confirmation_mail(request, email_confirmation, True)
        else:
            # If the user is being changed and the email is not verified
            if not obj.emailaddress_set.filter(email=obj.email, verified=True).exists():
                # Create a new EmailConfirmation object
                email_confirmation = EmailConfirmation.create(email_address)
                email_confirmation.sent = timezone.now()
                email_confirmation.save()

                # Resend the confirmation email
                get_adapter().send_confirmation_mail(request, email_confirmation, False)

#admin.site.unregister(MyUser)
admin.site.register(MyUser, UserAdmin)

User = get_user_model()

class GroupAdminForm(forms.ModelForm):
    class Meta:
        model = Group
        exclude = []

    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=FilteredSelectMultiple('users', False)
    )

    def __init__(self, *args, **kwargs):
        super(GroupAdminForm, self).__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['users'].initial = self.instance.user_set.all()

    def save_m2m(self):
        self.instance.user_set.set(self.cleaned_data['users'])

    def save(self, *args, **kwargs):
        instance = super(GroupAdminForm, self).save()
        self.save_m2m()
        return instance


admin.site.unregister(Group)

class GroupAdmin(admin.ModelAdmin):
    form = GroupAdminForm
    filter_horizontal = ['permissions']

admin.site.register(Group, GroupAdmin)
