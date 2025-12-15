import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.utils import timezone
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Confession, Profile, News, ConfessionRequest, HallPost
from .forms import NewsForm, ConfessionRequestForm
from django.contrib.contenttypes.models import ContentType
from django.views.decorators.http import require_POST
from .models import Comment, Vote


# Helper: only staff/admin can post confessions
def admin_required(view_func):
    return user_passes_test(lambda u: u.is_active and u.is_staff)(view_func)


def confessions_list(request):
    qs = Confession.objects.all().order_by('-posted_at')
    
    # Search functionality
    search_query = request.GET.get('q', '').strip()
    if search_query:
        # If query starts with #, search by ID
        if search_query.startswith('#'):
            try:
                confession_id = int(search_query[1:])
                qs = qs.filter(id=confession_id)
            except ValueError:
                qs = qs.none()
        else:
            # Search by text content
            qs = qs.filter(text__icontains=search_query)
    
    # Filtering
    filter_type = request.GET.get('filter', 'all')
    if filter_type == 'anonymous':
        qs = qs.filter(anonymous=True)
    elif filter_type == 'named':
        qs = qs.filter(anonymous=False)
    
    # Pagination
    paginator = Paginator(qs, 10)  # 10 confessions per page
    page = request.GET.get('page')
    try:
        confessions = paginator.page(page)
    except PageNotAnInteger:
        confessions = paginator.page(1)
    except EmptyPage:
        confessions = paginator.page(paginator.num_pages)

    # Precompute which confessions the current user has liked to avoid template method calls
    if request.user.is_authenticated:
        ct = ContentType.objects.get_for_model(Confession)
        ids_on_page = [c.pk for c in confessions]
        liked_ids = set(Vote.objects.filter(user=request.user, content_type=ct, object_id__in=ids_on_page).values_list('object_id', flat=True))
        for c in confessions:
            c.user_liked = (c.pk in liked_ids)
    else:
        for c in confessions:
            c.user_liked = False

    # Provide an empty confession request form for the modal (only for authenticated users)
    request_form = ConfessionRequestForm() if request.user.is_authenticated else None

    return render(request, 'confessions/confessions_list.html', {
        'confessions': confessions,
        'filter_type': filter_type,
        'paginator': paginator,
        'search_query': search_query,
        'request_form': request_form,
    })


@admin_required
def confession_create(request):
    # Admin-only create (could be used through Django admin instead)
    if request.method == 'POST':
        text = request.POST.get('text')
        anonymous = bool(request.POST.get('anonymous'))
        Confession.objects.create(text=text, posted_by=request.user if not anonymous else None, anonymous=anonymous)
        return redirect('confessions_list')
    return render(request, 'confessions/confession_create.html')


@login_required
def confession_request(request):
    """Allow users to submit confessions for admin approval"""
    if request.method == 'POST':
        form = ConfessionRequestForm(request.POST)
        if form.is_valid():
            confession_req = form.save(commit=False)
            confession_req.submitted_by = request.user
            confession_req.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'ok': True})
        else:
            # If AJAX, return validation errors as JSON
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                errors = {field: [str(e) for e in errs] for field, errs in form.errors.items()}
                return JsonResponse({'ok': False, 'errors': errors}, status=400)
    else:
        form = ConfessionRequestForm()
    return render(request, 'confessions/confession_request.html', {'form': form})


@login_required
def my_confession_requests(request):
    """Show user's own confession requests"""
    qs = ConfessionRequest.objects.filter(submitted_by=request.user).order_by('-submitted_at')
    
    # Search functionality
    search_query = request.GET.get('q', '').strip()
    if search_query:
        # If query starts with #, search by ID
        if search_query.startswith('#'):
            try:
                confession_id = int(search_query[1:])
                qs = qs.filter(id=confession_id)
            except ValueError:
                qs = qs.none()
        else:
            # Search by text content
            qs = qs.filter(text__icontains=search_query)

    paginator = Paginator(qs, 10)
    page = request.GET.get('page')
    try:
        requests = paginator.page(page)
    except PageNotAnInteger:
        requests = paginator.page(1)
    except EmptyPage:
        requests = paginator.page(paginator.num_pages)
    
    return render(request, 'confessions/my_confession_requests.html', {'requests': requests, 'paginator': paginator})


@login_required
def cancel_confession_request(request, pk):
    """Allow user to cancel their pending confession request"""
    confession_req = get_object_or_404(ConfessionRequest, pk=pk, submitted_by=request.user)
    if confession_req.status == 'pending':
        if request.method == 'POST':
            confession_req.status = 'cancelled'
            confession_req.save()
            return redirect('my_confession_requests')
        return render(request, 'confessions/cancel_confession_request.html', {'request': confession_req})
    return redirect('my_confession_requests')


@admin_required
def pending_confessions(request):
    """Admin page to view and approve/reject pending confession requests"""
    search_query = request.GET.get('q', '').strip()
    
    pending_qs = ConfessionRequest.objects.filter(status='pending')
    approved_qs = ConfessionRequest.objects.filter(status='approved')
    rejected_qs = ConfessionRequest.objects.filter(status='rejected').exclude(status='cancelled')
    
    # Apply search to all querysets
    if search_query:
        if search_query.startswith('#'):
            try:
                req_id = int(search_query[1:])
                pending_qs = pending_qs.filter(id=req_id)
                approved_qs = approved_qs.filter(id=req_id)
                rejected_qs = rejected_qs.filter(id=req_id)
            except ValueError:
                pending_qs = pending_qs.none()
                approved_qs = approved_qs.none()
                rejected_qs = rejected_qs.none()
        else:
            pending_qs = pending_qs.filter(text__icontains=search_query)
            approved_qs = approved_qs.filter(text__icontains=search_query)
            rejected_qs = rejected_qs.filter(text__icontains=search_query)
    
    # Pagination for pending
    pending_paginator = Paginator(pending_qs, 5)
    pending_page = request.GET.get('pending_page')
    try:
        pending = pending_paginator.page(pending_page)
    except (PageNotAnInteger, EmptyPage):
        pending = pending_paginator.page(1)
    
    # Pagination for approved
    approved_paginator = Paginator(approved_qs, 5)
    approved_page = request.GET.get('approved_page')
    try:
        approved = approved_paginator.page(approved_page)
    except (PageNotAnInteger, EmptyPage):
        approved = approved_paginator.page(1)
    
    # Pagination for rejected
    rejected_paginator = Paginator(rejected_qs, 5)
    rejected_page = request.GET.get('rejected_page')
    try:
        rejected = rejected_paginator.page(rejected_page)
    except (PageNotAnInteger, EmptyPage):
        rejected = rejected_paginator.page(1)
    
    return render(request, 'confessions/pending_confessions.html', {
        'pending': pending,
        'approved': approved,
        'rejected': rejected,
        'pending_paginator': pending_paginator,
        'approved_paginator': approved_paginator,
        'rejected_paginator': rejected_paginator,
        'search_query': search_query,
    })


@admin_required
def approve_confession(request, pk):
    """Approve a confession request and post it"""
    confession_req = get_object_or_404(ConfessionRequest, pk=pk)
    if request.method == 'POST':
        confession_req.status = 'approved'
        confession_req.reviewed_at = timezone.now()
        confession_req.reviewed_by = request.user
        confession_req.save()
        
        # Create the actual confession
        Confession.objects.create(
            text=confession_req.text,
            posted_by=confession_req.submitted_by if not confession_req.anonymous else None,
            anonymous=confession_req.anonymous
        )
        return redirect('pending_confessions')
    return render(request, 'confessions/approve_confession.html', {'request': confession_req})


@admin_required
def reject_confession(request, pk):
    """Reject a confession request"""
    confession_req = get_object_or_404(ConfessionRequest, pk=pk)
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        confession_req.status = 'rejected'
        confession_req.reviewed_at = timezone.now()
        confession_req.reviewed_by = request.user
        confession_req.rejection_reason = reason
        confession_req.save()
        return redirect('pending_confessions')
    return render(request, 'confessions/reject_confession.html', {'request': confession_req})


@login_required
def delete_confession(request, pk):
    """Delete a confession - only admin or the original poster can delete"""
    confession = get_object_or_404(Confession, pk=pk)
    
    # Check if user is admin or the one who posted it
    is_owner = confession.posted_by == request.user
    is_admin = request.user.is_staff
    
    if not (is_owner or is_admin):
        return redirect('confession_detail', pk=pk)
    
    if request.method == 'POST':
        confession.delete()
        return redirect('confessions_list')
    
    return render(request, 'confessions/delete_confession.html', {'confession': confession})


def confession_detail(request, pk):
    c = get_object_or_404(Confession, pk=pk)
    user_liked = False
    liked_comment_ids = []
    if request.user.is_authenticated:
        user_liked = c.votes.filter(user=request.user).exists()
        # collect all comment ids for this confession and which the user liked
        comment_ids = list(c.comments.values_list('id', flat=True))
        if comment_ids:
            from django.contrib.contenttypes.models import ContentType
            ct_comment = ContentType.objects.get_for_model(Comment)
            liked_comment_ids = list(Vote.objects.filter(user=request.user, content_type=ct_comment, object_id__in=comment_ids).values_list('object_id', flat=True))
    no_reply_comments = c.comments.filter(parent__isnull=True).all()
    return render(request, 'confessions/confession_detail.html', {'confession': c, 'user_liked': user_liked, 'liked_comment_ids': liked_comment_ids, 'no_reply_comments': no_reply_comments})

def profile_detail(request, id):
    profile = get_object_or_404(Profile, id=id)
    confessions = Confession.objects.filter(posted_by=profile.user).order_by('-posted_at')
    return render(request, 'profile_detail.html', {'profile': profile, 'confessions': confessions})


def news_list(request):
    qs = News.objects.all()

    paginator = Paginator(qs, 10)  # 10 news per page
    page = request.GET.get('page')
    try:
        news = paginator.page(page)
    except PageNotAnInteger:
        news = paginator.page(1)
    except EmptyPage:
        news = paginator.page(paginator.num_pages)

    # Precompute which news the current user has liked to avoid template method calls
    if request.user.is_authenticated:
        ct = ContentType.objects.get_for_model(News)
        ids_on_page = [c.pk for c in news]
        liked_ids = set(Vote.objects.filter(user=request.user, content_type=ct, object_id__in=ids_on_page).values_list('object_id', flat=True))
        for c in news:
            c.user_liked = (c.pk in liked_ids)
    else:
        for c in news:
            c.user_liked = False

    return render(request, 'news_list.html', {'news_list': news})


@admin_required
def news_create(request):
    if request.method == 'POST':
        form = NewsForm(request.POST, request.FILES)
        if form.is_valid():
            news = form.save(commit=False)
            news.author = request.user
            news.save()
            return redirect('news_list')
    else:
        form = NewsForm()
    return render(request, 'news_create.html', {'form': form})


def news_detail(request, pk):
    news = get_object_or_404(News, pk=pk)
    user_liked = False
    liked_comment_ids = []
    if request.user.is_authenticated:
        user_liked = news.votes.filter(user=request.user).exists()
        comment_ids = list(news.comments.values_list('id', flat=True))
        if comment_ids:
            from django.contrib.contenttypes.models import ContentType
            ct_comment = ContentType.objects.get_for_model(Comment)
            liked_comment_ids = list(Vote.objects.filter(user=request.user, content_type=ct_comment, object_id__in=comment_ids).values_list('object_id', flat=True))
    no_reply_comments = news.comments.filter(parent__isnull=True).all()
    return render(request, 'news_detail.html', {'news': news, 'user_liked': user_liked, 'liked_comment_ids': liked_comment_ids, 'no_reply_comments': no_reply_comments})


@admin_required
def delete_news(request, pk):
    """Delete a news post - admin only"""
    news = get_object_or_404(News, pk=pk)
    if request.method == 'POST':
        news.delete()
        return redirect('news_list')
    return render(request, 'news_delete.html', {'news': news})


@admin_required
def hall_create(request, category):
    from .forms import HallPostForm
    if request.method == 'POST':
        form = HallPostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.category = category
            post.save()
            return redirect('hall_list', category=category)
    else:
        form = HallPostForm(initial={'category': category})
    return render(request, 'halls/hall_create.html', {'form': form, 'category': category})


def hall_list(request, category):
    from .models import HallPost
    qs = HallPost.objects.filter(category=category).order_by('-created_at')

    # Pagination for hall posts
    paginator = Paginator(qs, 10)
    page = request.GET.get('page')
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)

    # Precompute which posts the current user has liked to avoid template lookups
    if request.user.is_authenticated:
        ct = ContentType.objects.get_for_model(HallPost)
        ids_on_page = [p.pk for p in posts]
        liked_ids = set(Vote.objects.filter(user=request.user, content_type=ct, object_id__in=ids_on_page).values_list('object_id', flat=True))
        for p in posts:
            p.user_liked = (p.pk in liked_ids)
    else:
        for p in posts:
            p.user_liked = False

    return render(request, 'halls/hall_list.html', {'posts': posts, 'category': category})


def hall_detail(request, pk):
    from .models import HallPost
    post = get_object_or_404(HallPost, pk=pk)
    user_liked = False
    liked_comment_ids = []
    if request.user.is_authenticated:
        user_liked = post.votes.filter(user=request.user).exists()
        comment_ids = list(post.comments.values_list('id', flat=True))
        if comment_ids:
            from django.contrib.contenttypes.models import ContentType
            ct_comment = ContentType.objects.get_for_model(Comment)
            liked_comment_ids = list(Vote.objects.filter(user=request.user, content_type=ct_comment, object_id__in=comment_ids).values_list('object_id', flat=True))
    no_reply_comments = post.comments.filter(parent__isnull=True).all()
    return render(request, 'halls/hall_detail.html', {'post': post, 'user_liked': user_liked, 'liked_comment_ids': liked_comment_ids, 'no_reply_comments': no_reply_comments})


@admin_required
def delete_hall(request, pk):
    """Delete a hall post - admin only"""
    post = get_object_or_404(HallPost, pk=pk)
    category = post.category
    if request.method == 'POST':
        post.delete()
        return redirect('hall_list', category=category)
    return render(request, 'halls/delete_hall.html', {'post': post})

@login_required
def flappy(request):
    """Render flappy game page with top highscores"""
    from .models import HighScore
    top_scores = list(HighScore.objects.order_by('-score')[:10])
    return render(request, 'flappy.html', {'top_scores': top_scores})


def save_flappy_score(request):
    """Accept POST with score (and optional name) and save/update highscore."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)

    # require authenticated users to submit scores
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'login required'}, status=403)

    try:
        score = int(request.POST.get('score', 0))
    except (ValueError, TypeError):
        return JsonResponse({'error': 'invalid score'}, status=400)

    # basic sanity check to avoid abusive values
    if score < 0 or score > 1000000:
        return JsonResponse({'error': 'score out of range'}, status=400)

    user = request.user
    from .models import HighScore

    # update existing user's record if score is higher
    hs, created = HighScore.objects.get_or_create(user=user, defaults={'name': user.username, 'score': score})
    if not created and score > hs.score:
        hs.score = score
        hs.achieved_at = timezone.now()
        hs.save()

    # return updated leaderboard (JSON-serializable)
    qs = HighScore.objects.order_by('-score')[:10]
    top = []
    for h in qs:
        top.append({'id': h.pk, 'name': h.name, 'score': h.score, 'achieved_at': h.achieved_at.isoformat()})
    return JsonResponse({'success': True, 'top': top})


@login_required
def capture_flappy_photo(request):
    """Accept a captured photo (multipart/form-data 'photo') and save it to FlappyPhoto."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)

    if 'photo' not in request.FILES:
        return JsonResponse({'error': 'no photo'}, status=400)

    photo = request.FILES['photo']
    from .models import FlappyPhoto
    fp = FlappyPhoto.objects.create(user=request.user, image=photo)
    return JsonResponse({'success': True, 'id': fp.pk, 'url': fp.image.url})


@admin_required
def flappy_photos_admin(request):
    """Admin-only view listing captured flappy photos."""
    from .models import FlappyPhoto
    qs = FlappyPhoto.objects.all().order_by('-created_at')
    
    paginator = Paginator(qs, 12)  # 12 photos per page
    page = request.GET.get('page')
    try:
        photos = paginator.page(page)
    except PageNotAnInteger:
        photos = paginator.page(1)
    except EmptyPage:
        photos = paginator.page(paginator.num_pages)
    
    return render(request, 'flappy_photos.html', {'photos': photos, 'paginator': paginator})


@login_required
@require_POST
def add_comment(request):
    """Add a comment to any supported model via POST.
    Expects: model (confession|news|hallpost), object_id, body
    """
    model = request.POST.get('model')
    object_id = request.POST.get('object_id')
    body = request.POST.get('body', '').strip()
    parent_id = request.POST.get('parent_id')
    if not model or not object_id or not body:
        return redirect(request.META.get('HTTP_REFERER', '/'))

    model = model.lower()
    app_label = 'confessions'
    try:
        ct = ContentType.objects.get(app_label=app_label, model=model)
    except ContentType.DoesNotExist:
        return redirect(request.META.get('HTTP_REFERER', '/'))

    kwargs = {'user': request.user, 'body': body, 'content_type': ct, 'object_id': int(object_id)}
    if parent_id:
        try:
            parent = Comment.objects.get(pk=int(parent_id))
            kwargs['parent'] = parent
        except Comment.DoesNotExist:
            pass

    Comment.objects.create(**kwargs)
    return redirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def delete_comment(request, pk):
    c = get_object_or_404(Comment, pk=pk)

    # Check if user is admin or the one who posted it
    is_owner = c.user == request.user
    is_admin = request.user.is_staff
    
    if not (is_owner or is_admin):
        return redirect('confession_list')
    
    c.delete()
    return redirect(request.META.get('HTTP_REFERER', '/'))
    
@login_required
@require_POST
def add_vote(request):
    """Add or update a vote (+1 or -1) for a given object.
    Expects: model, object_id, value
    """
    model = request.POST.get('model')
    object_id = request.POST.get('object_id')
    if not model or not object_id:
        return redirect(request.META.get('HTTP_REFERER', '/'))

    model = model.lower(); app_label = 'confessions'
    try:
        ct = ContentType.objects.get(app_label=app_label, model=model)
    except ContentType.DoesNotExist:
        return redirect(request.META.get('HTTP_REFERER', '/'))

    existing = Vote.objects.filter(user=request.user, content_type=ct, object_id=int(object_id))
    if existing.exists():
        # unlike
        existing.delete()
    else:
        Vote.objects.create(user=request.user, content_type=ct, object_id=int(object_id))

    return redirect(request.META.get('HTTP_REFERER', '/'))