from django.contrib import admin
from .models import ActivationCode, Profile, Confession, News, FlappyPhoto, Comment, Vote, Report, HighScore, Partner, GradeCalculation


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

@admin.register(HighScore)
class HighScoreAdmin(admin.ModelAdmin):
    list_display = ('user', 'score', 'achieved_at')
    readonly_fields = ('achieved_at',)
    search_fields = ('user__username',)
    ordering = ('-score',)
    list_filter = ('achieved_at',)

@admin.register(ActivationCode)
class ActivationCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'used', 'hardware_id')
    search_fields = ('code', 'hardware_id')


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ('name', 'tier', 'is_active', 'order', 'created_at')
    list_filter = ('tier', 'is_active', 'created_at')
    search_fields = ('name', 'description', 'email')
    list_editable = ('order', 'is_active')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'tier', 'logo')
        }),
        ('Contact Information', {
            'fields': ('website', 'email', 'phone')
        }),
        ('Settings', {
            'fields': ('is_active', 'order')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(GradeCalculation)
class GradeCalculationAdmin(admin.ModelAdmin):
    list_display = ('user', 'level', 'get_branch_display', 'calculated_average', 'created_at')
    list_filter = ('level', 'branch', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Student Information', {
            'fields': ('user', 'level', 'branch')
        }),
        ('Grades', {
            'fields': ('subjects_data', 'calculated_average')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_branch_display(self, obj):
        return obj.branch or 'N/A'
    get_branch_display.short_description = 'Branch'