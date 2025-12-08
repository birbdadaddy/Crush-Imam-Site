from django import forms
from .models import News, ConfessionRequest, HallPost


class NewsForm(forms.ModelForm):
    class Meta:
        model = News
        fields = ['title', 'body', 'image']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 6}),
        }


class ConfessionRequestForm(forms.ModelForm):
    class Meta:
        model = ConfessionRequest
        fields = ['text', 'anonymous']
        widgets = {
            'text': forms.Textarea(attrs={
                'rows': 8,
                'placeholder': 'Share your confession here...',
                'class': 'form-control'
            }),
            'anonymous': forms.CheckboxInput(attrs={'class': 'form-checkbox'})
        }
        labels = {
            'text': 'Your Confession',
            'anonymous': 'Post Anonymously'
        }


class HallPostForm(forms.ModelForm):
    class Meta:
        model = HallPost
        fields = ['title', 'body', 'image', 'category']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 6}),
        }