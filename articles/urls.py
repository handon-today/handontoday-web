"""
articles 앱 URL 패턴
"""
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'articles'

urlpatterns = [
    # 인증
    path('signup/', views.SignupView.as_view(), name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='articles/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),

    # 메인 페이지
    path('', views.HomeView.as_view(), name='home'),
    
    # 기사 상세 (id + slug)
    path(
        'article/<int:article_id>-<slug:slug>/',
        views.ArticleDetailView.as_view(),
        name='detail'
    ),
    
    # 아카이브 (년도+월)
    path(
        'archive/<int:year>/<int:month>/',
        views.ArchiveView.as_view(),
        name='archive'
    ),
    
    # 아카이브 (년도별)
    path(
        'archive/<int:year>/',
        views.ArchiveView.as_view(),
        name='archive'
    ),
    
    # 아카이브 (카테고리별)
    path(
        'archive/<str:category>/',
        views.ArchiveView.as_view(),
        name='archive'
    ),
    
    # 아카이브 (전체)
    path('archive/', views.ArchiveView.as_view(), name='archive'),
]
