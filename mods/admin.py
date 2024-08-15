from django.contrib import admin

from .models import Category, Gender, Mod, ModCompatibility, ModImage, Race, Tag, User


class ModCompatibilityInline(admin.TabularInline):
    model = ModCompatibility
    extra = 1


@admin.register(Mod)
class ModAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "version", "upload_date", "approved")
    list_filter = ("approved", "categories", "tags")
    search_fields = ("title", "description", "user__username", "categories__name", "tags__name")
    actions = ["approve_mods", "reject_mods"]
    inlines = [ModCompatibilityInline]

    @admin.action(description="Approve selected mods")
    def approve_mods(self, request, queryset):
        queryset.update(approved=True)

    @admin.action(description="Reject selected mods")
    def reject_mods(self, request, queryset):
        # Delete associated files for the mod while keeping metadata just in case
        for mod in queryset:
            if mod.file:
                mod.file.delete(save=False)

            # Delete all images
            for image in mod.modimage_set.all():
                image.image.delete(save=False)
                image.delete()
        # Mark as rejected to keep track
        queryset.update(approved=False)


class CategoryAdmin(admin.ModelAdmin):
    list_display = "name"
    search_fields = "name"


class TagAdmin(admin.ModelAdmin):
    list_display = "name"
    search_fields = "name"


class RaceAdmin(admin.ModelAdmin):
    list_display = "name"
    search_fields = "name"


class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "date_joined")
    search_fields = ("username", "email")


admin.site.register(Category)
admin.site.register(Tag)
admin.site.register(Race)
admin.site.register(Gender)
admin.site.register(ModImage)
admin.site.register(ModCompatibility)
admin.site.register(User)
