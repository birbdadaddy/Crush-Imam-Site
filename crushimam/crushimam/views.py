from django.shortcuts import render, get_object_or_404, redirect

def home(request):
    return render(request, 'crushimam/home.html')

def privacy_and_policy(request):
    return render(request, 'privacy_and_policy.html')