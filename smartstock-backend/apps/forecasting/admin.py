from django.contrib import admin

from .models import ForecastResult, ReorderFlag

admin.site.register(ForecastResult)
admin.site.register(ReorderFlag)
