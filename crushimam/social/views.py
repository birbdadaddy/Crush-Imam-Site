"""
Views for social app: Feed, profiles, posts, messages, notifications
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q, Count, Prefetch
from django.core.paginator import Paginator
from django.utils import timezone
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from datetime import timedelta
import json
import os
from PIL import Image
import random
import string

from .models import (
    Post, Comment, Like, Follow, UserProfile, Story, StoryView,
    DirectMessage, Conversation, Notification, Bookmark,
    ContentReport, BlockedUser, FollowRequest, Hashtag, PostMedia
)
from .forms import (
    PostCreationForm, CommentForm, DirectMessageForm,
    StoryCreationForm, ContentReportForm, UserProfileForm,
    PostMediaForm, BlockUserForm
)


class FeedView(LoginRequiredMixin, ListView):
    """Home feed: chronological posts from followed users"""
    model = Post
    template_name = 'social/feed.html'
    context_object_name = 'posts'
    paginate_by = 10
    login_url = 'account_login'

    def get_queryset(self):
        """Get posts from followed users or all posts for discovery"""
        user = self.request.user
        
        # Get users that current user follows
        following_users = Follow.objects.filter(
            follower=user
        ).values_list('following', flat=True)

        # Get non-archived posts from followed users + own posts
        posts = Post.objects.filter(
            Q(author__in=following_users) | Q(author=user),
            is_archived=False
        ).select_related('author', 'author__social_profile').prefetch_related(
            'media', 'likes', 'comments'
        ).order_by('-created_at')

        # Filter out posts from blocked users
        blocked_users = BlockedUser.objects.filter(
            blocker=user
        ).values_list('blocked_user', flat=True)
        posts = posts.exclude(author__in=blocked_users)

        return posts

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        context['form'] = PostCreationForm()
        context['post_media_form'] = PostMediaForm()
        return context




class CreatePostView(LoginRequiredMixin, CreateView):
    """Create a new post"""
    model = Post
    form_class = PostCreationForm
    template_name = 'social/post_create.html'
    success_url = reverse_lazy('social:feed')
    login_url = 'account_login'

    def form_valid(self, form):
        form.instance.author = self.request.user
        response = super().form_valid(form)

        # Handle media uploads
        media_files = self.request.FILES.getlist('media_files')
        if media_files:
            self.handle_media_upload(media_files)

        return response

    def handle_media_upload(self, media_files):
        """Process and save uploaded media files"""
        for idx, media_file in enumerate(media_files):
            # Determine media type
            media_type = 'image' if media_file.content_type.startswith('image') else 'video'

            # Create PostMedia instance
            post_media = PostMedia.objects.create(
                post=self.object,
                media_file=media_file,
                media_type=media_type,
                order=idx
            )

            # Generate thumbnail for images
            if media_type == 'image':
                self.generate_thumbnail(post_media)

    def generate_thumbnail(self, post_media):
        """Generate thumbnail for image media"""
        try:
            img = Image.open(post_media.media_file)
            img.thumbnail((300, 300))
            thumbnail_path = f"social/thumbnails/{post_media.id}.jpg"
            img.save(thumbnail_path)
            post_media.thumbnail = thumbnail_path
            post_media.save(update_fields=['thumbnail'])
        except Exception as e:
            print(f"Error generating thumbnail: {e}")


class PostDetailView(LoginRequiredMixin, DetailView):
    """View a single post with all comments"""
    model = Post
    template_name = 'social/post_detail.html'
    context_object_name = 'post'
    login_url = 'account_login'
    pk_url_kwarg = 'post_id'

    def get_queryset(self):
        return Post.objects.select_related(
            'author', 'author__social_profile'
        ).prefetch_related('media', 'likes', 'comments')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.object

        # Get comments with nested replies
        comments = post.comments.filter(
            parent_comment__isnull=True
        ).prefetch_related('replies').order_by('-created_at')

        context['comments'] = comments
        context['comment_form'] = CommentForm()
        context['user_liked'] = post.likes.filter(user=self.request.user).exists()
        context['user_saved'] = post.saved_by.filter(user=self.request.user).exists()

        return context


class UpdatePostView(LoginRequiredMixin, UpdateView):
    """Update a post (caption only)"""
    model = Post
    fields = ['caption']
    template_name = 'social/post_update.html'
    pk_url_kwarg = 'post_id'

    def get_queryset(self):
        return Post.objects.filter(author=self.request.user)

    def get_success_url(self):
        return reverse_lazy('social:post_detail', kwargs={'post_id': self.object.id})


class DeletePostView(LoginRequiredMixin, DeleteView):
    """Delete a post"""
    model = Post
    template_name = 'social/post_delete.html'
    success_url = reverse_lazy('social:feed')
    pk_url_kwarg = 'post_id'

    def get_queryset(self):
        return Post.objects.filter(author=self.request.user)


@login_required
@require_POST
def like_post(request, post_id):
    """Like/unlike a post"""
    post = get_object_or_404(Post, id=post_id)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # AJAX request
        like_obj, created = Like.objects.get_or_create(user=request.user, post=post)

        post_likes = Like.objects.filter(post=post).count()
        if not created:
            like_obj.delete()
            return JsonResponse({'liked': False, 'count': post_likes})
        else:
            return JsonResponse({'liked': True, 'count': post_likes})

    # Regular form submission
    like_obj, created = Like.objects.get_or_create(user=request.user, post=post)
    if not created:
        like_obj.delete()

    return redirect('social:post_detail', post_id=post_id)


@login_required
@require_POST
def add_comment(request, post_id):
    """Add a comment to a post"""
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'comment_id': str(comment.id),
                'author': comment.author.username,
                'text': comment.text,
                'created_at': comment.created_at.isoformat(),
            })

    return redirect('social:post_detail', post_id=post_id)


@login_required
@require_POST
def delete_comment(request, comment_id):
    """Delete a comment"""
    comment = get_object_or_404(Comment, id=comment_id)

    # Check permission
    if comment.author != request.user and comment.post.author != request.user:
        return HttpResponse('Unauthorized', status=403)

    post_id = comment.post.id
    comment.delete()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})

    return redirect('social:post_detail', post_id=post_id)


@login_required
@require_POST
def bookmark_post(request, post_id):
    """Save/bookmark a post"""
    post = get_object_or_404(Post, id=post_id)

    bookmark, created = Bookmark.objects.get_or_create(user=request.user, post=post)

    if not created:
        bookmark.delete()
        saved = False
    else:
        saved = True

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'saved': saved})

    return redirect('social:post_detail', post_id=post_id)


@login_required
def user_profile(request, username):
    """View user profile"""
    user = get_object_or_404(User, username=username)
    profile = UserProfile.objects.get_or_create(user=user)[0]

    # Check if blocked
    if BlockedUser.objects.filter(blocker=request.user, blocked_user=user).exists():
        return render(request, 'social/blocked.html')

    # Get user's posts
    if profile.privacy == 'private':
        # Only show posts if following (or is own profile)
        is_following = Follow.objects.filter(
            follower=request.user,
            following=user
        ).exists()
        if user != request.user and not is_following:
            posts = Post.objects.none()
        else:
            posts = Post.objects.filter(author=user, is_archived=False)
    else:
        posts = Post.objects.filter(author=user, is_archived=False)

    posts = posts.select_related('author', 'author__social_profile').prefetch_related(
        'media', 'likes'
    ).order_by('-created_at')

    # Pagination
    paginator = Paginator(posts, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Follow status
    is_following = Follow.objects.filter(follower=request.user, following=user).exists()
    is_blocked = BlockedUser.objects.filter(blocker=request.user, blocked_user=user).exists()

    # Stats
    followers_count = Follow.objects.filter(following=user).count()
    following_count = Follow.objects.filter(follower=user).count()
    posts_count = Post.objects.filter(author=user, is_archived=False).count()

    context = {
        'profile_user': user,
        'profile': profile,
        'posts': page_obj.object_list,
        'page_obj': page_obj,
        'is_following': is_following,
        'is_blocked': is_blocked,
        'is_own_profile': user == request.user,
        'followers_count': followers_count,
        'following_count': following_count,
        'posts_count': posts_count,
    }

    return render(request, 'social/profile.html', context)


@login_required
def edit_profile(request):
    """Edit own profile"""
    profile = request.user.social_profile

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('social:profile', username=request.user.username)
    else:
        form = UserProfileForm(instance=profile)

    return render(request, 'social/profile_edit.html', {'form': form})


@login_required
@require_POST
def follow_user(request, username):
    """Follow a user"""
    user_to_follow = get_object_or_404(User, username=username)

    if user_to_follow == request.user:
        return HttpResponse('Cannot follow yourself', status=400)

    profile = UserProfile.objects.get(user=user_to_follow)

    if profile.privacy == 'private':
        # Create follow request
        follow_req, created = FollowRequest.objects.get_or_create(
            from_user=request.user,
            to_user=user_to_follow
        )
        message = "Follow request sent" if created else "Follow request already sent"
    else:
        # Direct follow
        follow, created = Follow.objects.get_or_create(
            follower=request.user,
            following=user_to_follow
        )
        message = "Following" if created else "Already following"

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'message': message, 'following': True})

    return redirect('social:profile', username=username)


@login_required
@require_POST
def unfollow_user(request, username):
    """Unfollow a user"""
    user_to_unfollow = get_object_or_404(User, username=username)
    Follow.objects.filter(
        follower=request.user,
        following=user_to_unfollow
    ).delete()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'following': False})

    return redirect('social:profile', username=username)


@login_required
def messages_view(request):
    """View all conversations"""
    conversations = Conversation.objects.filter(
        participants=request.user
    ).annotate(
        unread_count=Count('last_message__id', filter=Q(last_message__is_read=False))
    ).select_related('last_message', 'last_message__sender').order_by('-updated_at')

    paginator = Paginator(conversations, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'social/messages.html', {
        'page_obj': page_obj,
        'conversations': page_obj.object_list,
    })


@login_required
def conversation_detail(request, conversation_id):
    """View conversation messages"""
    conversation = get_object_or_404(Conversation, id=conversation_id)

    # Check permission
    print(conversation.participants.all())
    if request.user not in conversation.participants.all():
        return HttpResponse('Unauthorized', status=403)

    # Get other participant
    other_user = conversation.participants.exclude(id=request.user.id).first()

    # Mark messages as read
    DirectMessage.objects.filter(
        recipient=request.user,
        conversation__id=conversation_id,
        is_read=False
    ).update(is_read=True, read_at=timezone.now())

    messages = DirectMessage.objects.filter(
        Q(sender=request.user, recipient=other_user) |
        Q(sender=other_user, recipient=request.user)
    ).order_by('-created_at')[:100]
    messages = list(reversed(messages))

    return render(request, 'social/conversation_detail.html', {
        'conversation': conversation,
        'other_user': other_user,
        'messages': messages,
        'form': DirectMessageForm(),
    })


@login_required
@require_POST
def send_message(request, conversation_id):
    """Send a direct message"""
    conversation = get_object_or_404(Conversation, id=conversation_id)

    if request.user not in conversation.participants.all():
        return HttpResponse('Unauthorized', status=403)

    other_user = conversation.participants.exclude(id=request.user.id).first()
    text = request.POST.get('text', '').strip()

    if text:
        message = DirectMessage.objects.create(
            sender=request.user,
            recipient=other_user,
            text=text,
            message_type='text'
        )

        # Update conversation
        conversation.last_message = message
        conversation.save(update_fields=['last_message', 'updated_at'])

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message_id': str(message.id),
                'sender': message.sender.username,
                'text': message.text,
                'created_at': message.created_at.isoformat(),
            })

    return redirect('social:conversation_detail', conversation_id=conversation_id)


@login_required
def start_conversation(request, username):
    """Start a new conversation with a user"""
    other_user = get_object_or_404(User, username=username)

    if other_user == request.user:
        return HttpResponse('Cannot message yourself', status=400)

    # Get or create conversation using the proper class method
    conversation, created = Conversation.get_or_create_for_users(request.user, other_user)

    return redirect('social:conversation_detail', conversation_id=conversation.id)


@login_required
def notifications_view(request):
    """View all notifications"""
    notifications = Notification.objects.filter(
        recipient=request.user
    ).select_related('actor', 'post', 'comment', 'message').order_by('-created_at')

    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Mark as read
    unread = Notification.objects.filter(recipient=request.user, is_read=False)
    unread.update(is_read=True)

    return render(request, 'social/notifications.html', {
        'page_obj': page_obj,
        'notifications': page_obj.object_list,
    })


@login_required
@require_POST
def report_content(request, content_type, content_id):
    """Report inappropriate content"""
    form = ContentReportForm(request.POST)

    if form.is_valid():
        report = form.save(commit=False)
        report.reporter = request.user

        if content_type == 'post':
            report.post = get_object_or_404(Post, id=content_id)
        elif content_type == 'comment':
            report.comment = get_object_or_404(Comment, id=content_id)
        elif content_type == 'message':
            report.message = get_object_or_404(DirectMessage, id=content_id)

        report.save()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Content reported'})

    return redirect('social:feed')


@login_required
@require_POST
def block_user(request, username):
    """Block a user"""
    user_to_block = get_object_or_404(User, username=username)

    if user_to_block == request.user:
        return HttpResponse('Cannot block yourself', status=400)

    blocked, created = BlockedUser.objects.get_or_create(
        blocker=request.user,
        blocked_user=user_to_block
    )

    # Remove follow relationships
    Follow.objects.filter(
        Q(follower=request.user, following=user_to_block) |
        Q(follower=user_to_block, following=request.user)
    ).delete()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': 'User blocked'})

    return redirect('social:profile', username=username)


@login_required
@require_POST
def unblock_user(request, username):
    """Unblock a user"""
    user_to_unblock = get_object_or_404(User, username=username)
    BlockedUser.objects.filter(
        blocker=request.user,
        blocked_user=user_to_unblock
    ).delete()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': 'User unblocked'})

    return redirect('social:profile', username=username)


@login_required
def search_view(request):
    """Search for users, posts, hashtags"""
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'all')
    results = {}

    if query:
        # Search users
        if search_type in ['all', 'users']:
            results['users'] = User.objects.filter(
                Q(username__icontains=query) | Q(first_name__icontains=query)
            ).exclude(blocked_by__blocker=request.user)[:10]

        # Search posts
        if search_type in ['all', 'posts']:
            results['posts'] = Post.objects.filter(
                Q(caption__icontains=query),
                is_archived=False
            ).exclude(author__blocked_by__blocker=request.user)[:10]

        # Search hashtags
        if search_type in ['all', 'hashtags']:
            results['hashtags'] = Hashtag.objects.filter(
                tag__icontains=query
            ).order_by('-usage_count')[:10]

    return render(request, 'social/search.html', {
        'query': query,
        'search_type': search_type,
        'results': results,
    })
