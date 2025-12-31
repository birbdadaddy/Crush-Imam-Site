from django.shortcuts import render, get_object_or_404, redirect
from confessions.models import Confession, News, Partner
from django.contrib.auth.models import User

def home(request):
    news_list = News.objects.order_by('-created_at')[:2]
    confessions_count = Confession.objects.all().count()
    news_count = News.objects.all().count()
    user_count = User.objects.all().count()
    
    # Get featured partners (gold and silver partners)
    featured_partners = Partner.objects.filter(is_active=True, tier__in=['gold', 'silver']).order_by('tier', 'order')[:6]
    
    context = {'news_list': news_list,
                'confessions_count': confessions_count,
                'news_count': news_count,
                'user_count': user_count,
                'featured_partners': featured_partners,
    }
    return render(request, 'crushimam/home.html', context)

def privacy_and_policy(request):
    return render(request, 'privacy_and_policy.html')


def chat(request):
    """Render the anonymous chat page (no login required).

    Template provides UI for text + video chat and includes the WebSocket
    client logic which performs matchmaking and WebRTC signaling.
    """
    return render(request, 'crushimam/chat.html')