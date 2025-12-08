from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    instagram_username = models.CharField(max_length=100, blank=True, null=True)
    bio = models.TextField(blank=True)
    photo = models.ImageField(upload_to='profiles/', blank=True, null=True)


    def __str__(self):
        return self.user.get_full_name() or self.instagram_username or self.user.username


    def get_absolute_url(self):
        return reverse('profile_detail', args=[self.pk])


class Confession(models.Model):
    text = models.TextField()
    posted_at = models.DateTimeField(auto_now_add=True)
    posted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    anonymous = models.BooleanField(default=True)
    # relations
    comments = GenericRelation('Comment', related_query_name='confession')
    votes = GenericRelation('Vote', related_query_name='confession')


    class Meta:
        ordering = ['-posted_at']


    def __str__(self):
        return f"Confession {self.pk} - {'anon' if self.anonymous else self.posted_by}\n"

    @property
    def vote_total(self):
        res = self.votes.aggregate(total=Count('id'))
        return res.get('total') or 0


class HallPost(models.Model):
    CATEGORY_CHOICES = [
        ('fame', 'Hall of Fame'),
        ('shame', 'Hall of Shame'),
    ]

    title = models.CharField(max_length=255)
    body = models.TextField()
    image = models.ImageField(upload_to='halls/', blank=True, null=True)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    comments = GenericRelation('Comment', related_query_name='hallpost')
    votes = GenericRelation('Vote', related_query_name='hallpost')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title}"

    @property
    def vote_total(self):
        res = self.votes.aggregate(total=Count('id'))
        return res.get('total') or 0


class News(models.Model):
    title = models.CharField(max_length=255)
    body = models.TextField()
    image = models.ImageField(upload_to='news/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    comments = GenericRelation('Comment', related_query_name='news')
    votes = GenericRelation('Vote', related_query_name='news')


    class Meta:
            ordering = ['-created_at']


    def __str__(self):  
        return self.title

    @property
    def vote_total(self):
        res = self.votes.aggregate(total=Count('id'))
        return res.get('total') or 0


class ConfessionRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    text = models.TextField()
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='confession_requests')
    anonymous = models.BooleanField(default=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_confession_requests')
    rejection_reason = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"Request {self.pk} - {self.status}"


class HighScore(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=100, blank=True)
    score = models.IntegerField(default=0)
    achieved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-score', 'achieved_at']

    def __str__(self):
        return f"{self.name or (self.user.username if self.user else 'Guest')} - {self.score}"


class FlappyPhoto(models.Model):
    """Stores photos captured from the Flappy page. Only admins should view these."""
    user = models.ForeignKey('auth.User', null=True, blank=True, on_delete=models.SET_NULL)
    image = models.ImageField(upload_to='flappy_photos/')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        if self.user:
            return f"Photo by {self.user.username} @ {self.created_at:%Y-%m-%d %H:%M}"
        return f"Photo @ {self.created_at:%Y-%m-%d %H:%M}"


class Comment(models.Model):
    """Generic comment model for Confession, News, HallPost."""
    user = models.ForeignKey('auth.User', null=True, blank=True, on_delete=models.SET_NULL)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='replies', on_delete=models.CASCADE)

    # allow likes on comments via generic relation to Vote
    likes = GenericRelation('Vote', related_query_name='comment')

    # generic relation to any model
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        who = self.user.username if self.user else 'Guest'
        return f"Comment by {who} on {self.content_type} #{self.object_id}"

    @property
    def like_count(self):
        return self.likes.count()


class Vote(models.Model):
    """Generic vote model storing +1 or -1 per user per object."""
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        unique_together = ('user', 'content_type', 'object_id')

    def __str__(self):
        return f"Like by {self.user.username} on {self.content_type}#{self.object_id}"