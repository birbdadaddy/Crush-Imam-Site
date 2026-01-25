import uuid
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count

from django.conf import settings


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
    
def report_upload_path(instance, filename):
    # store under MEDIA_ROOT/reports/<report-id>/filename
    return f'reports/{instance.id}/{filename}'


class Report(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.CharField(max_length=255, blank=True, null=True)
    timestamp = models.DateTimeField()
    notes = models.TextField(blank=True)
    # link to users: the reporter (who clicked report) and the reported user (if known)
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='reports_made')
    reported_user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='reports_against')

    local_image = models.ImageField(upload_to=report_upload_path, blank=True, null=True)
    remote_image = models.ImageField(upload_to=report_upload_path, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Report {self.id} @ {self.timestamp}'

class ActivationCode(models.Model):
    code = models.CharField(max_length=100, unique=True)  # e.g., 'ABC123-XYZ' or UUID
    hardware_id = models.CharField(max_length=255, blank=True, null=True)  # Bound machine ID
    used = models.BooleanField(default=False)

    def __str__(self):
        return self.code


class Partner(models.Model):
    """Model for showcasing partners and sponsors."""
    TIER_CHOICES = [
        ('gold', 'Gold Partner'),
        ('silver', 'Silver Partner'),
        ('bronze', 'Bronze Partner'),
        ('sponsor', 'Sponsor'),
    ]
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='partners/', blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='sponsor')
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['tier', 'order', '-created_at']
        verbose_name = 'Partner'
        verbose_name_plural = 'Partners'

    def __str__(self):
        return f"{self.name} ({self.tier})"

    def get_absolute_url(self):
        return reverse('partner_detail', args=[self.pk])


class GradeCalculation(models.Model):
    """Model for storing student grade calculations in Moroccan grading system with exams and coefficients."""
    
    LEVEL_CHOICES = [
        ('5eme', '5ème année'),
        ('1bac', '1ère année BAC'),
        ('2bac', '2ème année BAC'),
    ]
    
    # Predefined subject coefficients for each level and branch
    SUBJECT_COEFFICIENTS = {

    # ───── 5ème ─────
    '5eme': {
        'sc': {
            'Behavior': 1,
            'Arabic': 2,
            'French': 3,
            'English': 3,
            'Mathematics': 4,
            'Physics & Chemistry': 4,
            'SVT': 4,
            'History & Geography': 2,
            'Islamic Studies': 2,
            'Philosophy': 2,
            'Physical Education': 2,
            'Informatique': 2,
        },
        'tc': {
            'Behavior': 1,
            'Arabic': 2,
            'French': 3,
            'English': 3,
            'Mathematics': 4,
            'Physics & Chemistry': 4,
            'Engineering Sciences': 4,
            'History & Geography': 2,
            'Islamic Studies': 2,
            'Philosophy': 2,
            'Physical Education': 2,
            'Informatique': 3,
        },
        'lettres': {
            'Behavior': 1,
            'Arabic': 4,
            'French': 4,
            'English': 3,
            'Mathematics': 2,
            'SVT': 2,
            'History & Geography': 4,
            'Islamic Studies': 2,
            'Philosophy': 2,
            'Physical Education': 1,
        },
    },

    # ───── 1ère Bac ─────
    '1bac': {
        'sc_math': {
            'Behavior': 1,
            'Arabic': 2,
            'French': 4,
            'English': 2,
            'Mathematics': 9,
            'Physics & Chemistry': 7,
            'SVT': 3,
            'History & Geography': 2,
            'Islamic Studies': 2,
            'Philosophy': 2,
            'Physical Education': 1,
        },
        'sc_exp': {
            'Behavior': 1,
            'Arabic': 2,
            'French': 4,
            'English': 2,
            'Mathematics': 7,
            'Physics & Chemistry': 7,
            'SVT': 7,
            'History & Geography': 2,
            'Islamic Studies': 2,
            'Philosophy': 2,
            'Physical Education': 1,
        },
        'sc_telectric': {
            'Behavior': 1,
            'Arabic': 2,
            'French': 4,
            'English': 2,
            'Mathematics': 7,
            'Physics & Chemistry': 5,
            'Engineering Sciences': 8,
            'Islamic Studies': 2,
            'Philosophy': 2,
            'Physical Education': 4,
        },
        'sc_tmechanic': {
            'Behavior': 1,
            'Arabic': 2,
            'French': 4,
            'English': 2,
            'Mathematics': 7,
            'Physics & Chemistry': 5,
            'Engineering Sciences': 8,
            'Islamic Studies': 2,
            'Philosophy': 2,
            'Physical Education': 4,
        },
        'sc_econ': {
            'Behavior': 1,
            'Mathematics': 4,
            'Arabic': 2,
            'French': 3,
            'English': 2,
            'Économie et Organisation': 3,
            'Comptabilité': 4,
            'Économie générale et Statistiques': 6,
            'Droit': 1,
            'Informatique de gestion': 1,
            'History & Geography': 3,
            'Islamic Studies': 2,
            'Philosophy': 2,
            'Physical Education': 1,
        },
        'lettres': {
            'Behavior': 1,
            'Arabic': 4,
            'French': 4,
            'English': 4,
            'Mathematics': 1,
            'SVT': 1,
            'Philosophy': 3,
            'History & Geography': 3,
            'Islamic Studies': 2,
            'Physical Education': 4,
        },
    },

    # ───── 2ème Bac ─────
    '2bac': {
        'sc_math_a': {
            'Behavior': 1,
            'Arabic': 2,
            'French': 4,
            'English': 2,
            'Mathematics': 9,
            'Physics & Chemistry': 7,
            'SVT': 3,
            'Islamic Studies': 2,
            'Philosophy': 2,
            'Physical Education': 4,
        },
        'sc_math_b': {
            'Behavior': 1,
            'Arabic': 2,
            'French': 4,
            'English': 2,
            'Mathematics': 9,
            'Physics & Chemistry': 7,
            'Engineering Sciences': 3,
            'Islamic Studies': 2,
            'Philosophy': 2,
            'Physical Education': 4,
        },
        'sc_phys': {
            'Behavior': 1,
            'Arabic': 2,
            'French': 4,
            'English': 2,
            'Mathematics': 7,
            'Physics & Chemistry': 7,
            'SVT': 5,
            'Islamic Studies': 2,
            'Philosophy': 2,
            'Physical Education': 4,
        },
        'sc_svt': {
            'Behavior': 1,
            'Arabic': 2,
            'French': 4,
            'English': 2,
            'Mathematics': 7,
            'SVT': 7,
            'Physics & Chemistry': 5,
            'Islamic Studies': 2,
            'Philosophy': 2,
            'Physical Education': 4,
        },
        'sc_agronomic': {
            'Behavior': 1,
            'Arabic': 2,
            'French': 4,
            'English': 2,
            'Mathematics': 7,
            'Physics & Chemistry': 7,
            'SVT': 5,
            'SVA': 5,
            'Islamic Studies': 2,
            'Philosophy': 2,
            'History & Geography': 2,
            'Physical Education': 4
        },
        'sc_electric': {
            'Behavior': 1,
            'Arabic': 2,
            'French': 2,
            'English': 2,
            'Mathematics': 3,
            'Engineering Sciences': 6,
            'Physics & Chemistry': 3,
            'Islamic Studies': 2,
            'Philosophy': 2,
        },
        'sc_mechanic': {
            'Behavior': 1,
            'Arabic': 2,
            'French': 2,
            'English': 2,
            'Mathematics': 3,
            'Engineering Sciences': 6,
            'Physics & Chemistry': 3,
            'Islamic Studies': 2,
            'Philosophy': 2,
            'Physical Education': 1,
        },
        'sc_econ': {
            'Behavior': 1,
            'Mathematics': 4,
            'Arabic': 2,
            'French': 3,
            'English': 2,
            'Économie et Organisation': 3,
            'Comptabilité': 4,
            'Économie générale et Statistiques': 6,
            'Droit': 4,
            'Informatique de gestion': 4,
            'Philosophy': 2,
            'History & Geography': 3,
            'Islamic Studies': 2,
            'Physical Education': 4,
        },
        'lettres': {
            'Behavior': 1,
            'Mathematics': 1,
            'Arabic': 4,
            'French': 4,
            'English': 4,
            'Philosophy': 3,
            'History & Geography': 3,
            'Islamic Studies': 2,
            'Physical Education': 4,
        },
        'sc_humaines': {
            'Behavior': 1,
            'Mathematics': 1,
            'Arabic': 3,
            'French': 4,
            'English': 3,
            'Philosophy': 4,
            'History & Geography': 4,
            'Islamic Studies': 2,
            'Physical Education': 4,
        },
    }
}
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='grade_calculations')
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES)
    branch = models.CharField(max_length=50, blank=True)
    
    subjects_data = models.JSONField(default=dict)
    
    calculated_average = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Grade Calculation'
        verbose_name_plural = 'Grade Calculations'
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.level} ({self.calculated_average or 'N/A'})"
    
    def get_branch_display(self):
        """Get the display name for the branch"""
        branch_choices = {
            '5eme': {
                'general': 'Cursus général',
                'sc': 'Sciences',
                'tc': 'Sciences & Tech',
                'lettres': 'Lettres',
            },
            '1bac': {
                'sc_exp': 'Sciences Expérimentales',
                'sc_math': 'Sciences Mathématiques',
                'sc_tech': 'Sciences et Technologies',
                'lettres': 'Lettres Modernes',
                'lettres_ar': 'Lettres Arabes',
                'sc_telectric': 'Sciences Tech Électrique',
                'sc_tmechanic': 'Sciences Tech Mécanique',
                'sc_econ': 'Économie',
            },
            '2bac': {
                'sc_math_a': 'Sciences Math A',
                'sc_math_b': 'Sciences Math B',
                'sc_phys': 'Sciences Physique',
                'sc_svt': 'Sciences SVT',
                'sc_argon': 'Sciences Agronomiques',
                'sc_electric': 'Sciences Électrique',
                'sc_mechanic': 'Sciences Mécanique',
                'sc_econ': 'Économie',
                'lettres': 'Lettres Modernes',
                'sc_humaines': 'Sciences Humaines',
            }
        }
        
        if self.level in branch_choices and self.branch in branch_choices[self.level]:
            return branch_choices[self.level][self.branch]
        return self.branch or 'General'
    
    def calculate_subject_average(self, subject_data):
        """Calculate average for a subject including exams and behavior."""
        if not subject_data or 'exams' not in subject_data:
            return 0
        
        exams = subject_data.get('exams', [])
        behavior = subject_data.get('behavior', 0)
        
        if not exams:
            return 0
        
        # Average of exams
        exam_average = sum(exams) / len(exams)
        
        # If behavior exists, include it in the average (e.g., weighted by 1 out of exam count)
        if behavior:
            # Combine exam average with behavior (behavior counts as one exam)
            total_average = (exam_average * len(exams) + behavior) / (len(exams) + 1)
        else:
            total_average = exam_average
        
        return total_average
    
    def calculate_average(self):
        """Calculate weighted average of all subjects."""
        if not self.subjects_data:
            return 0
        
        total_weighted = 0
        total_coefficient = 0
        
        for subject, data in self.subjects_data.items():
            coefficient = data.get('coefficient', 1)
            subject_avg = self.calculate_subject_average(data)
            
            total_weighted += subject_avg * coefficient
            total_coefficient += coefficient
        
        if total_coefficient == 0:
            return 0
        
        self.calculated_average = total_weighted / total_coefficient
        return self.calculated_average
    
    def get_absolute_url(self):
        return reverse('grade_detail', args=[self.pk])