from django.contrib import admin
from .models import Pattern, PatternElement, MyValueField, Composition, CompositionElement  # noqa
# Register your models here.


# @admin.register(Pattern)
class PatternAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']


# @admin.register(PatternElement)
class PatternElementAdmin(admin.ModelAdmin):
    list_display = ['id', 'pattern_name']

    def pattern_name(self, obj):
        return obj.pattern.name


# @admin.register(Composition)
class CompositionAdmin(admin.ModelAdmin):
    pass


# @admin.register(CompositionElement)
class CompositionElementAdmin(admin.ModelAdmin):
    pass
