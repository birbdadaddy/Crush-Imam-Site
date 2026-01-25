"""
Social app models: Posts, Stories, Comments, Likes, Follow System, Direct Messaging, Notifications
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MaxValueValidator, MinValueValidator
import uuid


class UserProfile(models.Model):
    """Extended user profile with social features"""
    PRIVACY_CHOICES = [
        ('public', 'Public'),
        ('private', 'Private'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='social_profile')
    bio = models.TextField(blank=True, max_length=500)
    profile_picture = models.ImageField(upload_to='social/profiles/', null=True, blank=True)
    cover_photo = models.ImageField(upload_to='social/covers/', null=True, blank=True)
    privacy = models.CharField(max_length=10, choices=PRIVACY_CHOICES, default='public')
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    website = models.URLField(blank=True)
    location = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.user.username} Profile"

    class Meta:
        ordering = ['-created_at']


class Follow(models.Model):
    """Follow relationship between users"""
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')
        indexes = [
            models.Index(fields=['follower', 'following']),
        ]

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"


class FollowRequest(models.Model):
    """Follow request for private accounts"""
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_follow_requests')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_follow_requests')
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=[
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ], default='pending')

    class Meta:
        unique_together = ('from_user', 'to_user')

    def __str__(self):
        return f"{self.from_user.username} -> {self.to_user.username}: {self.status}"


class BlockedUser(models.Model):
    """Block user relationship"""
    blocker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocked_users')
    blocked_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocked_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('blocker', 'blocked_user')

    def __str__(self):
        return f"{self.blocker.username} blocked {self.blocked_user.username}"


class Post(models.Model):
    """User posts with text, images, or videos"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='social_posts')
    caption = models.TextField(blank=True, max_length=2200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_anonymous = models.BooleanField(default=False)
    anonymous_name = models.CharField(max_length=50, blank=True)  # Random name if anonymous
    is_archived = models.BooleanField(default=False)
    allow_comments = models.BooleanField(default=True)
    allow_likes = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['author']),
        ]

    def __str__(self):
        author_name = self.anonymous_name if self.is_anonymous else self.author.username
        return f"Post by {author_name} - {self.created_at}"

    @property
    def media_count(self):
        return self.media.count()


class PostMedia(models.Model):
    """Media items (images/videos) for a post - supports carousel"""
    MEDIA_TYPE = [
        ('image', 'Image'),
        ('video', 'Video'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='media')
    media_file = models.FileField(upload_to='social/posts/')
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE)
    order = models.PositiveIntegerField(default=0)
    thumbnail = models.ImageField(upload_to='social/thumbnails/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.media_type} in Post {self.post.id}"


class Like(models.Model):
    """Like a post"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='social_likes')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')
        indexes = [
            models.Index(fields=['post']),
        ]

    def __str__(self):
        return f"{self.user.username} liked post {self.post.id}"

    def toggle(self, user, post):
        """Toggle like status for a user on a post"""
        like, created = Like.objects.get_or_create(user=user, post=post)
        if not created:
            like.delete()
            return False
        return True


class Comment(models.Model):
    """Comment on a post with nested reply support"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='social_comments')
    parent_comment = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies'
    )
    text = models.TextField(max_length=1000)
    is_anonymous = models.BooleanField(default=False)
    anonymous_name = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_edited = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['post']),
        ]

    def __str__(self):
        author_name = self.anonymous_name if self.is_anonymous else self.author.username
        return f"Comment by {author_name} on Post {self.post.id}"


class CommentLike(models.Model):
    """Like a comment"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'comment')

    def __str__(self):
        return f"{self.user.username} liked comment {self.comment.id}"


class Bookmark(models.Model):
    """Save/Bookmark posts"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='saved_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} bookmarked {self.post.id}"


class Story(models.Model):
    """24-hour temporary content stories"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='social_stories')
    media_file = models.FileField(upload_to='social/stories/')
    media_type = models.CharField(max_length=10, choices=[
        ('image', 'Image'),
        ('video', 'Video'),
    ])
    caption = models.TextField(blank=True, max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()  # Auto-calculated as created_at + 24h
    thumbnail = models.ImageField(upload_to='social/story-thumbnails/', null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Story by {self.author.username}"

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at


class StoryView(models.Model):
    """Track who viewed a story"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='views')
    viewer = models.ForeignKey(User, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('story', 'viewer')
        ordering = ['-viewed_at']

    def __str__(self):
        return f"{self.viewer.username} viewed story {self.story.id}"


class DirectMessage(models.Model):
    """Private messages between users"""
    MESSAGE_TYPE = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('voice', 'Voice Note'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    text = models.TextField(blank=True)
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPE, default='text')
    media_file = models.FileField(upload_to='social/messages/', null=True, blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sender', 'recipient']),
        ]

    def __str__(self):
        return f"DM from {self.sender.username} to {self.recipient.username}"


class Conversation(models.Model):
    """Track active conversations for DMs"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    participants = models.ManyToManyField(User, related_name='conversations')
    last_message = models.ForeignKey(
        DirectMessage, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_muted = models.ManyToManyField(User, related_name='muted_conversations', blank=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        users = ', '.join([u.username for u in self.participants.all()])
        return f"Conversation: {users}"

    @classmethod
    def get_or_create_for_users(cls, user1, user2):
        """Get or create a conversation between two users"""
        # Check if conversation already exists
        conversation = cls.objects.filter(
            participants=user1
        ).filter(
            participants=user2
        ).first()

        if conversation:
            return conversation, False

        # Create new conversation
        conversation = cls.objects.create()
        conversation.participants.add(user1, user2)
        return conversation, True


class Notification(models.Model):
    """Real-time notifications"""
    NOTIFICATION_TYPES = [
        ('like', 'Like'),
        ('comment', 'Comment'),
        ('follow', 'Follow'),
        ('message', 'Message'),
        ('mention', 'Mention'),
        ('story_view', 'Story View'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    actor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='actions')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True)
    message = models.ForeignKey(DirectMessage, on_delete=models.CASCADE, null=True, blank=True)
    story = models.ForeignKey(Story, on_delete=models.CASCADE, null=True, blank=True)
    text = models.CharField(max_length=255)  # Notification description
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
        ]

    def __str__(self):
        return f"Notification for {self.recipient.username}: {self.notification_type}"


class ContentReport(models.Model):
    """Report inappropriate content"""
    REPORT_REASONS = [
        ('spam', 'Spam'),
        ('harassment', 'Harassment'),
        ('hate_speech', 'Hate Speech'),
        ('violence', 'Violence'),
        ('nsfw', 'NSFW Content'),
        ('fake_info', 'Misinformation'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='social_reports_made')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True, related_name='social_reports')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True, related_name='social_reports')
    message = models.ForeignKey(DirectMessage, on_delete=models.CASCADE, null=True, blank=True, related_name='social_reports')
    reason = models.CharField(max_length=20, choices=REPORT_REASONS)
    description = models.TextField(blank=True, max_length=500)
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Report #{self.id} - {self.reason}"


class MutedUser(models.Model):
    """Mute notifications from a user without unfollowing"""
    muter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='muted_users')
    muted_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='muted_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('muter', 'muted_user')

    def __str__(self):
        return f"{self.muter.username} muted {self.muted_user.username}"


class Hashtag(models.Model):
    """Track popular hashtags"""
    tag = models.CharField(max_length=100, unique=True)
    posts = models.ManyToManyField(Post, related_name='hashtags')
    usage_count = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-usage_count']

    def __str__(self):
        return f"#{self.tag}"
