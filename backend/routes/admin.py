from django.contrib import admin

from .models import Route

class PointAdmin(admin.TabularInline):
    model = Route.points.through

class RouteAdmin(admin.ModelAdmin):
    inlines = [PointAdmin]
    list_display = ('id', 'user', )
    list_filter = ('user',)
    exclude = ('points', )

admin.site.register(Route, RouteAdmin)
