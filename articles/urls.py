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

    # 기사 삭제 (staff only, POST)
    path(
        'article/<int:article_id>/delete/',
        views.article_delete,
        name='article_delete'
    ),

    # 아카이브 (년도+월)
    path(
        'archive/<int:year>/<int:month>/',
        views.ArchiveView.as_view(),
        name='archive_ym'
    ),

    # 아카이브 (년도별)
    path(
        'archive/<int:year>/',
        views.ArchiveView.as_view(),
        name='archive_y'
    ),

    # 아카이브 (카테고리별)
    path(
        'archive/<str:category>/',
        views.ArchiveView.as_view(),
        name='archive_cat'
    ),

    # 아카이브 (전체) — name='archive' 유지 (기존 템플릿 호환)
    path('archive/', views.ArchiveView.as_view(), name='archive'),

    # 소개 페이지
    path('about/', views.about_view, name='about'),

    # 검색 — 아카이브로 리다이렉트
    path('search/', views.search_view, name='search'),
]

# Honeypot
urlpatterns += [
    path('contact-old/', views.honeypot_view, name='honeypot'),
]

# 만평 상세
urlpatterns += [
    path(
        'manhwa/<int:article_id>-<slug:slug>/',
        views.ManhwaDetailView.as_view(),
        name='manhwa_detail'
    ),
]
