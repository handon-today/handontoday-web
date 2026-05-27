"""
articles 앱 URL 패턴
"""
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'articles'

urlpatterns = [
    path('signup/', views.SignupView.as_view(), name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='articles/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.HomeView.as_view(), name='home'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('article/<int:article_id>-<slug:slug>/', views.ArticleDetailView.as_view(), name='detail'),
    path('archive/<int:year>/<int:month>/', views.ArchiveView.as_view(), name='archive'),
    path('archive/<int:year>/', views.ArchiveView.as_view(), name='archive'),
    path('archive/<str:category>/', views.ArchiveView.as_view(), name='archive'),
    path('archive/', views.ArchiveView.as_view(), name='archive'),
    path('contact-old/', views.honeypot_view, name='honeypot'),
]
