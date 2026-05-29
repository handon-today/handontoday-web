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

    # ── 아카이브 ──
    # name이 모두 'archive'면 Django는 마지막 것만 reverse()에 등록함.
    # 경로 파라미터(year/month/category)는 views.py 에서 kwargs로 처리하고,
    # 필터 대부분은 ?q=&cat=&sort= 쿼리스트링으로 처리하므로
    # URL 패턴은 날짜 경로(년/월)만 남기고 나머지는 쿼리스트링으로 통일.

    # 아카이브 — 년도+월 경로 (예: /archive/2025/11/)
    path(
        'archive/<int:year>/<int:month>/',
        views.ArchiveView.as_view(),
        name='archive_ym'          # ← 고유한 name
    ),

    # 아카이브 — 년도 경로 (예: /archive/2025/)
    path(
        'archive/<int:year>/',
        views.ArchiveView.as_view(),
        name='archive_y'           # ← 고유한 name
    ),

    # 아카이브 — 전체 (검색/카테고리/정렬은 쿼리스트링)
    # {% url 'articles:archive' %} 가 이 URL을 가리킴
    path('archive/', views.ArchiveView.as_view(), name='archive'),
]

# Honeypot
urlpatterns += [
    path('contact-old/', views.honeypot_view, name='honeypot'),
]
