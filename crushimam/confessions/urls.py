from django.urls import path
from . import views


urlpatterns = [
    path('confession/', views.confessions_list, name='confessions_list'),
    path('confession/create/', views.confession_create, name='confession_create'),
    path('confession/<int:pk>/', views.confession_detail, name='confession_detail'),
    path('confession/<int:pk>/delete/', views.delete_confession, name='delete_confession'),
    path('profile/<int:id>/', views.profile_detail, name='profile_detail'),
    path('confession/request/', views.confession_request, name='confession_request'),
    path('my-requests/', views.my_confession_requests, name='my_confession_requests'),
    path('request/<int:pk>/cancel/', views.cancel_confession_request, name='cancel_confession_request'),
    path('pending/', views.pending_confessions, name='pending_confessions'),
    path('approve/<int:pk>/', views.approve_confession, name='approve_confession'),
    path('reject/<int:pk>/', views.reject_confession, name='reject_confession'),
    path('news/', views.news_list, name='news_list'),
    path('news/create/', views.news_create, name='news_create'),
    path('news/<int:pk>/', views.news_detail, name='news_detail'),
    path('news/<int:pk>/delete/', views.delete_news, name='news_delete'),
    path('flappy/', views.flappy, name='flappy'),
    path('flappy/save/', views.save_flappy_score, name='save_flappy_score'),
    path('flappy/capture/', views.capture_flappy_photo, name='flappy_capture'),
    path('flappy/photos/', views.flappy_photos_admin, name='flappy_photos_admin'),
    path('comment/add/', views.add_comment, name='add_comment'),
    path('comment/<int:pk>/delete/', views.delete_comment, name='delete_comment'),
    path('vote/add/', views.add_vote, name='add_vote'),
    # Halls: category is 'fame' or 'shame'
    path('hall/<str:category>/', views.hall_list, name='hall_list'),
    path('hall/<str:category>/create/', views.hall_create, name='hall_create'),
    path('hall/post/<int:pk>/', views.hall_detail, name='hall_detail'),
    path('hall/post/<int:pk>/delete/', views.delete_hall, name='hall_delete'),
    ]