"""
Signals for social app: Auto-create profiles, handle notifications, clean up expired stories
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import random
import string
from .models import (
    UserProfile, Post, Comment, Like, Follow, DirectMessage,
    Story, Notification, StoryView
)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Auto-create a UserProfile when a new user is created"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save user profile when user is saved"""
    if hasattr(instance, 'social_profile'):
        instance.social_profile.save()


@receiver(post_save, sender=Like)
def create_like_notification(sender, instance, created, **kwargs):
    """Create notification when someone likes a post"""
    if created:
        # Don't notify if user likes their own post
        if instance.post.author != instance.user:
            Notification.objects.create(
                recipient=instance.post.author,
                actor=instance.user,
                notification_type='like',
                post=instance.post,
                text=f"{instance.user.username} liked your post"
            )


@receiver(post_delete, sender=Like)
def delete_like_notification(sender, instance, **kwargs):
    """Delete notification when someone unlikes a post"""
    try:
        notification = Notification.objects.get(
            recipient=instance.post.author,
            actor=instance.user,
            notification_type='like',
            post=instance.post,
        )
        notification.delete()
    except Notification.DoesNotExist:
        pass


@receiver(post_save, sender=Comment)
def create_comment_notification(sender, instance, created, **kwargs):
    """Create notification when someone comments on a post"""
    if created and not instance.parent_comment:  # Top-level comment
        if instance.post.author != instance.author:
            Notification.objects.create(
                recipient=instance.post.author,
                actor=instance.author,
                notification_type='comment',
                post=instance.post,
                comment=instance,
                text=f"{instance.author.username} commented on your post"
            )


@receiver(post_save, sender=Comment)
def create_reply_notification(sender, instance, created, **kwargs):
    """Create notification when someone replies to a comment"""
    if created and instance.parent_comment:  # Reply to comment
        if instance.parent_comment.author != instance.author:
            Notification.objects.create(
                recipient=instance.parent_comment.author,
                actor=instance.author,
                notification_type='comment',
                comment=instance,
                text=f"{instance.author.username} replied to your comment"
            )


@receiver(post_save, sender=Follow)
def create_follow_notification(sender, instance, created, **kwargs):
    """Create notification when someone follows you"""
    if created:
        Notification.objects.create(
            recipient=instance.following,
            actor=instance.follower,
            notification_type='follow',
            text=f"{instance.follower.username} started following you"
        )


@receiver(post_save, sender=DirectMessage)
def create_message_notification(sender, instance, created, **kwargs):
    """Create notification when someone sends you a DM"""
    if created:
        Notification.objects.create(
            recipient=instance.recipient,
            actor=instance.sender,
            notification_type='message',
            message=instance,
            text=f"{instance.sender.username} sent you a message"
        )


@receiver(post_save, sender=DirectMessage)
def mark_message_as_read(sender, instance, **kwargs):
    """Update notification when message is read"""
    if instance.is_read and not instance.read_at:
        instance.read_at = timezone.now()
        instance.save(update_fields=['read_at'])


@receiver(post_save, sender=Story)
def set_story_expiry(sender, instance, created, **kwargs):
    """Set story expiration time to 24 hours from creation"""
    if created and not instance.expires_at:
        instance.expires_at = instance.created_at + timedelta(hours=24)
        instance.save(update_fields=['expires_at'])


@receiver(post_save, sender=StoryView)
def create_story_view_notification(sender, instance, created, **kwargs):
    """Create notification when someone views your story"""
    if created:
        if instance.story.author != instance.viewer:
            # Only create if notification doesn't exist
            if not Notification.objects.filter(
                recipient=instance.story.author,
                actor=instance.viewer,
                notification_type='story_view',
                story=instance.story,
            ).exists():
                Notification.objects.create(
                    recipient=instance.story.author,
                    actor=instance.viewer,
                    notification_type='story_view',
                    story=instance.story,
                    text=f"{instance.viewer.username} viewed your story"
                )


def generate_anonymous_name():
    """Generate a random anonymous name"""
    adjectives = ['Happy', 'Clever', 'Swift', 'Bright', 'Silent', 'Lucky', 'Bold', 'Calm']
    animals = ['Panda', 'Eagle', 'Fox', 'Wolf', 'Tiger', 'Bear', 'Hawk', 'Otter']
    return f"{random.choice(adjectives)}{random.choice(animals)}{random.randint(100, 999)}"


@receiver(post_save, sender=Post)
def set_anonymous_name(sender, instance, created, **kwargs):
    """Generate anonymous name if post is anonymous and name not set"""
    if created and instance.is_anonymous and not instance.anonymous_name:
        instance.anonymous_name = generate_anonymous_name()
        instance.save(update_fields=['anonymous_name'])


@receiver(post_save, sender=Comment)
def set_comment_anonymous_name(sender, instance, created, **kwargs):
    """Generate anonymous name if comment is anonymous and name not set"""
    if created and instance.is_anonymous and not instance.anonymous_name:
        instance.anonymous_name = generate_anonymous_name()
        instance.save(update_fields=['anonymous_name'])
