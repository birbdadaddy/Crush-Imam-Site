from django.contrib import admin
from .models import Profile, Confession, News, FlappyPhoto, Comment, Vote, Report


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'instagram_username')


@admin.register(Confession)
class ConfessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'short_text', 'posted_at', 'anonymous')
    readonly_fields = ('posted_at',)


    def short_text(self, obj):
            return obj.text[:50]


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'author')
    readonly_fields = ('created_at',)


@admin.register(FlappyPhoto)
class FlappyPhotoAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at')
    readonly_fields = ('created_at',)
    search_fields = ('user__username','user__email')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'short_body', 'user', 'created_at')
    readonly_fields = ('created_at',)
    search_fields = ('user__username','body')

    def short_body(self, obj):
        return obj.body[:80]


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'content_type', 'object_id', 'created_at')
    readonly_fields = ('created_at',)
    search_fields = ('user__username',)

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'room', 'timestamp', 'created_at')
    readonly_fields = ('created_at',)
    search_fields = ('room',)
    list_filter = ('created_at',)
