from django.contrib import admin

from .models import Team

class MembersAdmin(admin.TabularInline):
    model = Team.members.through

class RouteAdmin(admin.ModelAdmin):
    inlines = [MembersAdmin]
    list_display = ('id', 'name',)
    list_filter = ('name',)
    exclude = ('members',)

admin.site.register(Team, RouteAdmin)
