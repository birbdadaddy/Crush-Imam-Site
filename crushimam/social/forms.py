"""
Forms for social app: Post creation, comments, profile updates, messaging
"""
from django import forms
from django.contrib.auth.models import User
from .models import (
    Post, Comment, DirectMessage, UserProfile, Story, ContentReport
)


class UserProfileForm(forms.ModelForm):
    """Form for editing user profile"""
    class Meta:
        model = UserProfile
        fields = ['bio', 'profile_picture', 'cover_photo', 'privacy', 'website', 'location']
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Write your bio...',
                'rows': 3,
                'maxlength': 500,
            }),
            'profile_picture': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
            }),
            'cover_photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
            }),
            'privacy': forms.RadioSelect(attrs={
                'class': 'form-check-input',
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com',
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City, Country',
            }),
        }


class PostCreationForm(forms.ModelForm):
    """Form for creating a new post"""
    caption = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'What\'s on your mind?',
            'rows': 4,
            'maxlength': 2200,
        })
    )
    is_anonymous = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        }),
        label='Post as Anonymous'
    )
    allow_comments = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        }),
        label='Allow Comments'
    )
    allow_likes = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        }),
        label='Allow Likes'
    )

    class Meta:
        model = Post
        fields = ['caption', 'is_anonymous', 'allow_comments', 'allow_likes']


class PostMediaForm(forms.Form):
    """Form for uploading multiple media items"""
    media_files = forms.CharField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*,video/*',
        }),
        label='Upload Images/Videos',
        help_text='You can upload multiple files at once',
        required=False
    )


class CommentForm(forms.ModelForm):
    """Form for creating a comment"""
    text = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Add a comment...',
            'rows': 2,
            'maxlength': 1000,
        }),
        label=''
    )
    is_anonymous = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        }),
        label='Comment as Anonymous'
    )

    class Meta:
        model = Comment
        fields = ['text', 'is_anonymous']


class DirectMessageForm(forms.ModelForm):
    """Form for sending a direct message"""
    text = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Type a message...',
            'rows': 2,
        }),
        label=''
    )

    class Meta:
        model = DirectMessage
        fields = ['text', 'message_type', 'media_file']
        widgets = {
            'message_type': forms.HiddenInput(),
            'media_file': forms.FileInput(attrs={
                'class': 'form-control d-none',
                'accept': 'image/*,video/*,audio/*',
                'id': 'message-media-input',
            }),
        }


class StoryCreationForm(forms.ModelForm):
    """Form for creating a story"""
    media_file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*,video/*',
        }),
        label='Upload Story Image/Video'
    )
    caption = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Add text to your story...',
            'rows': 2,
            'maxlength': 200,
        })
    )

    class Meta:
        model = Story
        fields = ['media_file', 'caption']


class ContentReportForm(forms.ModelForm):
    """Form for reporting inappropriate content"""
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Describe why you\'re reporting this content...',
            'rows': 4,
            'maxlength': 500,
        })
    )

    class Meta:
        model = ContentReport
        fields = ['reason', 'description']
        widgets = {
            'reason': forms.Select(attrs={
                'class': 'form-control',
            }),
        }


class SearchForm(forms.Form):
    """Form for searching users, posts, hashtags"""
    query = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search users, hashtags...',
        }),
        label=''
    )
    search_type = forms.ChoiceField(
        choices=[
            ('all', 'All'),
            ('users', 'Users'),
            ('posts', 'Posts'),
            ('hashtags', 'Hashtags'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-control',
        }),
        label='Filter By'
    )


class BlockUserForm(forms.Form):
    """Form for blocking a user"""
    user_id = forms.IntegerField(widget=forms.HiddenInput())
    confirm = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        }),
        label='I understand that this user won\'t be able to find my profile, posts, or stories.'
    )
