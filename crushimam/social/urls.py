"""
URL routing for social app
"""
from django.urls import path
from . import views

app_name = 'social'

urlpatterns = [
    # Feed
    path('', views.FeedView.as_view(), name='feed'),

    # Posts
    path('post/create/', views.CreatePostView.as_view(), name='create_post'),
    path('post/<uuid:post_id>/', views.PostDetailView.as_view(), name='post_detail'),
    path('post/<uuid:post_id>/edit/', views.UpdatePostView.as_view(), name='update_post'),
    path('post/<uuid:post_id>/delete/', views.DeletePostView.as_view(), name='delete_post'),
    path('post/<uuid:post_id>/like/', views.like_post, name='like_post'),
    path('post/<uuid:post_id>/save/', views.bookmark_post, name='bookmark_post'),

    # Comments
    path('post/<uuid:post_id>/comment/', views.add_comment, name='add_comment'),
    path('comment/<uuid:comment_id>/delete/', views.delete_comment, name='delete_comment'),

    # Profile
    path('profile/<str:username>/', views.user_profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/<str:username>/follow/', views.follow_user, name='follow_user'),
    path('profile/<str:username>/unfollow/', views.unfollow_user, name='unfollow_user'),
    path('profile/<str:username>/block/', views.block_user, name='block_user'),
    path('profile/<str:username>/unblock/', views.unblock_user, name='unblock_user'),

    # Messaging
    path('messages/', views.messages_view, name='messages'),
    path('messages/<uuid:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('messages/<uuid:conversation_id>/send/', views.send_message, name='send_message'),
    path('messages/start/<str:username>/', views.start_conversation, name='start_conversation'),

    # Notifications
    path('notifications/', views.notifications_view, name='notifications'),

    # Search
    path('search/', views.search_view, name='search'),

    # Reports
    path('report/<str:content_type>/<uuid:content_id>/', views.report_content, name='report_content'),
]
