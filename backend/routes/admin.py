from django.contrib import admin

from .models import Route, PointOfInterest

class PointAdmin(admin.TabularInline):
    model = Route.points.through

class RouteAdmin(admin.ModelAdmin):
    inlines = [PointAdmin]
    list_display = ('id', 'owner', )
    list_filter = ('owner',)
    exclude = ('points', )

admin.site.register(Route, RouteAdmin)
