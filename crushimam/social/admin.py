"""
Admin configuration for social app: Moderation, content management
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    UserProfile, Follow, FollowRequest, BlockedUser, Post, PostMedia,
    Like, Comment, CommentLike, Bookmark, Story, StoryView,
    DirectMessage, Conversation, Notification, ContentReport,
    MutedUser, Hashtag
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'privacy', 'verified', 'created_at']
    list_filter = ['privacy', 'verified', 'created_at']
    search_fields = ['user__username', 'bio']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('User Info', {'fields': ('user', 'verified')}),
        ('Profile Details', {'fields': ('bio', 'profile_picture', 'cover_photo', 'website', 'location')}),
        ('Settings', {'fields': ('privacy',)}),
        ('Dates', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ['follower', 'following', 'created_at']
    list_filter = ['created_at']
    search_fields = ['follower__username', 'following__username']
    readonly_fields = ['created_at']


@admin.register(FollowRequest)
class FollowRequestAdmin(admin.ModelAdmin):
    list_display = ['from_user', 'to_user', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['from_user__username', 'to_user__username']
    actions = ['accept_requests', 'reject_requests']

    def accept_requests(self, request, queryset):
        updated = queryset.update(status='accepted')
        # Create Follow entries for accepted requests
        for follow_req in queryset:
            Follow.objects.get_or_create(
                follower=follow_req.from_user,
                following=follow_req.to_user
            )
        self.message_user(request, f'{updated} follow requests accepted.')

    def reject_requests(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} follow requests rejected.')

    accept_requests.short_description = "Accept selected requests"
    reject_requests.short_description = "Reject selected requests"


@admin.register(BlockedUser)
class BlockedUserAdmin(admin.ModelAdmin):
    list_display = ['blocker', 'blocked_user', 'created_at']
    list_filter = ['created_at']
    search_fields = ['blocker__username', 'blocked_user__username']
    readonly_fields = ['created_at']


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['author_display', 'caption_preview', 'is_anonymous', 'created_at', 'likes_count']
    list_filter = ['is_anonymous', 'is_archived', 'allow_comments', 'created_at']
    search_fields = ['author__username', 'caption', 'anonymous_name']
    readonly_fields = ['created_at', 'updated_at', 'id']
    actions = ['archive_posts', 'unarchive_posts', 'delete_selected']

    fieldsets = (
        ('Post Info', {'fields': ('id', 'author', 'caption')}),
        ('Visibility', {'fields': ('is_anonymous', 'anonymous_name', 'is_archived')}),
        ('Settings', {'fields': ('allow_comments', 'allow_likes')}),
        ('Dates', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    def author_display(self, obj):
        if obj.is_anonymous:
            return format_html('<i>{}</i>', obj.anonymous_name or 'Anonymous')
        return obj.author.username

    def caption_preview(self, obj):
        return (obj.caption[:50] + '...') if len(obj.caption) > 50 else obj.caption

    def likes_count(self, obj):
        return obj.likes.count()

    def archive_posts(self, request, queryset):
        updated = queryset.update(is_archived=True)
        self.message_user(request, f'{updated} posts archived.')

    def unarchive_posts(self, request, queryset):
        updated = queryset.update(is_archived=False)
        self.message_user(request, f'{updated} posts restored.')

    author_display.short_description = "Author"
    caption_preview.short_description = "Caption"
    likes_count.short_description = "Likes"


@admin.register(PostMedia)
class PostMediaAdmin(admin.ModelAdmin):
    list_display = ['post', 'media_type', 'order', 'created_at']
    list_filter = ['media_type', 'created_at']
    search_fields = ['post__id', 'post__author__username']
    readonly_fields = ['created_at', 'id']


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'post_author', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'post__author__username']
    readonly_fields = ['created_at', 'id']

    def post_author(self, obj):
        return obj.post.author.username


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['author_display', 'post_author', 'text_preview', 'is_anonymous', 'created_at']
    list_filter = ['is_anonymous', 'created_at', 'is_edited']
    search_fields = ['author__username', 'text', 'post__id']
    readonly_fields = ['created_at', 'updated_at', 'id']
    actions = ['delete_selected']

    def author_display(self, obj):
        if obj.is_anonymous:
            return format_html('<i>{}</i>', obj.anonymous_name or 'Anonymous')
        return obj.author.username

    def post_author(self, obj):
        return obj.post.author.username

    def text_preview(self, obj):
        return (obj.text[:50] + '...') if len(obj.text) > 50 else obj.text

    author_display.short_description = "Author"
    post_author.short_description = "Post Author"


@admin.register(CommentLike)
class CommentLikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'comment_author', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'comment__author__username']
    readonly_fields = ['created_at', 'id']

    def comment_author(self, obj):
        return obj.comment.author.username


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ['user', 'post_author', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'post__author__username']
    readonly_fields = ['created_at', 'id']

    def post_author(self, obj):
        return obj.post.author.username


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ['author', 'media_type', 'is_expired_display', 'views_count', 'created_at']
    list_filter = ['media_type', 'created_at']
    search_fields = ['author__username']
    readonly_fields = ['created_at', 'expires_at', 'id']

    def is_expired_display(self, obj):
        expired = obj.is_expired
        color = 'red' if expired else 'green'
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            'Expired' if expired else 'Active'
        )

    def views_count(self, obj):
        return obj.views.count()

    is_expired_display.short_description = "Status"
    views_count.short_description = "Views"


@admin.register(StoryView)
class StoryViewAdmin(admin.ModelAdmin):
    list_display = ['viewer', 'story_author', 'viewed_at']
    list_filter = ['viewed_at']
    search_fields = ['viewer__username', 'story__author__username']
    readonly_fields = ['viewed_at', 'id']

    def story_author(self, obj):
        return obj.story.author.username


@admin.register(DirectMessage)
class DirectMessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'recipient', 'message_type', 'is_read', 'created_at']
    list_filter = ['message_type', 'is_read', 'created_at']
    search_fields = ['sender__username', 'recipient__username', 'text']
    readonly_fields = ['created_at', 'read_at', 'id']
    actions = ['mark_as_read']

    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} messages marked as read.')


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['conversation_participants', 'last_message_display', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['participants__username']
    readonly_fields = ['created_at', 'updated_at', 'id']

    def conversation_participants(self, obj):
        return ', '.join([u.username for u in obj.participants.all()])

    def last_message_display(self, obj):
        if obj.last_message:
            return f"{obj.last_message.sender.username}: {obj.last_message.text[:30]}..."
        return "No messages"

    conversation_participants.short_description = "Participants"
    last_message_display.short_description = "Last Message"


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'actor', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['recipient__username', 'actor__username', 'text']
    readonly_fields = ['created_at', 'id']
    actions = ['mark_as_read']

    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} notifications marked as read.')


@admin.register(ContentReport)
class ContentReportAdmin(admin.ModelAdmin):
    list_display = ['id', 'reason', 'reporter', 'is_resolved', 'created_at']
    list_filter = ['reason', 'is_resolved', 'created_at']
    search_fields = ['reporter__username', 'description']
    readonly_fields = ['created_at', 'id']
    actions = ['mark_resolved', 'mark_unresolved']

    fieldsets = (
        ('Report Info', {'fields': ('id', 'reporter', 'reason', 'description')}),
        ('Content', {'fields': ('post', 'comment', 'message')}),
        ('Status', {'fields': ('is_resolved',)}),
        ('Dates', {'fields': ('created_at',), 'classes': ('collapse',)}),
    )

    def mark_resolved(self, request, queryset):
        updated = queryset.update(is_resolved=True)
        self.message_user(request, f'{updated} reports marked as resolved.')

    def mark_unresolved(self, request, queryset):
        updated = queryset.update(is_resolved=False)
        self.message_user(request, f'{updated} reports marked as unresolved.')


@admin.register(MutedUser)
class MutedUserAdmin(admin.ModelAdmin):
    list_display = ['muter', 'muted_user', 'created_at']
    list_filter = ['created_at']
    search_fields = ['muter__username', 'muted_user__username']
    readonly_fields = ['created_at']


@admin.register(Hashtag)
class HashtagAdmin(admin.ModelAdmin):
    list_display = ['tag', 'usage_count', 'created_at']
    list_filter = ['usage_count', 'created_at']
    search_fields = ['tag']
    readonly_fields = ['created_at', 'usage_count']
