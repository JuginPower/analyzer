from django.contrib import admin
from .models import Category, Keyword


admin.site.register([Category, Keyword])
