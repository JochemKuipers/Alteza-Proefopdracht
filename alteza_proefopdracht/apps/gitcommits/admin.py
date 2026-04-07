from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import GitUser


admin.site.register(GitUser, UserAdmin)
