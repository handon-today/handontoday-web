"""
한돈투데이 뷰
- HomeView: 메인 페이지 (최신 기사 목록)
- ArticleDetailView: 기사 상세
- ArchiveView: 아카이브 (검색 + 필터링)
"""

import re
import logging

from django.views.generic import ListView, DetailView, CreateView, TemplateView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import logout
from django.urls import reverse_lazy, reverse
from django.shortcuts import redirect, get_object_or_404
from django.http import HttpResponsePermanentRedirect, HttpResponseNotFound
from django.db.models import Q, Count, Sum
from django.utils import timezone

from .models import Article

logger = logging.getLogger(__name__)


class HomeView(ListView):
    """홈페이지"""
    model = Article
    template_name = 'articles/home.html'
    context_object_name = 'articles'
    paginate_by = 15

    def get_queryset(self):
        queryset = Article.objects.filter(
            publish_status='published'
        ).order_by('-published_at')

        category = self.request.GET.get('cat')
        if category:
            queryset = queryset.filter(category=category)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        category = self.request.GET.get('cat')
        nav_map = {'국내': 'domestic', '글로벌': 'global', 'market': 'market', 'policy': 'policy'}
        context['active_nav'] = nav_map.get(category, 'home')

        # 통계 — aggregate로 쿼리 1번
        stats = Article.objects.filter(publish_status='published').aggregate(
            korea_count=Count('id', filter=Q(category='국내')),
            global_count=Count('id', filter=Q(category='글로벌')),
            total_views=Sum('view_count'),
        )
        context['korea_count'] = stats['korea_count'] or 0
        context['global_count'] = stats['global_count'] or 0
        context['total_views'] = stats['total_views'] or 0

        today = timezone.localdate()
        context['today_views'] = Article.objects.filter(
            publish_status='published',
            published_at__date=today
        ).aggregate(s=Sum('view_count'))['s'] or 0

        return context


class ArticleDetailView(DetailView):
    """기사 상세 페이지"""
    model = Article
    template_name = 'articles/detail.html'
    context_object_name = 'article'

    def get_object(self):
        article_id = self.kwargs.get('article_id')
        slug = self.kwargs.get('slug')

        article = get_object_or_404(
            Article,
            id=article_id,
            publish_status='published'
        )

        # slug 불일치 시 redirect URL 세팅 (get()에서 처리)
        correct_slug = article.slug or 'no-slug'
        if slug != correct_slug:
            self._redirect_url = reverse('articles:detail', kwargs={
                'article_id': article.id,
                'slug': correct_slug,
            })

        return article

    def get(self, request, *args, **kwargs):
        """slug 불일치 시 301 redirect, 정상 시 조회수 처리 후 응답"""
        self._redirect_url = None
        self.object = self.get_object()

        if self._redirect_url:
            return HttpResponsePermanentRedirect(self._redirect_url)

        # 세션 기반 중복 방지
        session_key = f'viewed_article_{self.object.id}'
        if not request.session.get(session_key):
            self.object.view_count += 1
            self.object.save(update_fields=['view_count'])
            request.session[session_key] = True

        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        article = self.object
        match = re.search(
            r'<blockquote>.*?</blockquote>',
            article.body_html or '',
            re.DOTALL
        )
        context['summary_html'] = match.group(0) if match else None

        context['related_articles'] = Article.objects.filter(
            publish_status='published',
            category=article.category
        ).exclude(id=article.id).order_by('-published_at')[:3]

        return context


class ArchiveView(ListView):
    """아카이브 — 검색 + 날짜/카테고리 필터링"""
    model = Article
    template_name = 'articles/archive.html'
    context_object_name = 'articles'
    paginate_by = 20

    def get_queryset(self):
        sort = self.request.GET.get('sort', 'latest')
        order = '-view_count' if sort == 'popular' else '-published_at'

        queryset = Article.objects.filter(
            publish_status='published'
        ).order_by(order)

        # 카테고리: URL 경로 우선, 없으면 쿼리스트링
        category = self.kwargs.get('category') or self.request.GET.get('cat')
        if category in ['국내', '글로벌']:
            queryset = queryset.filter(category=category)

        # 날짜 필터
        year = self.kwargs.get('year')
        if year:
            queryset = queryset.filter(published_at__year=year)

        month = self.kwargs.get('month')
        if month:
            queryset = queryset.filter(published_at__month=month)

        # 검색어 (제목 + 부제목)
        q = self.request.GET.get('q', '').strip()
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q) | Q(deck__icontains=q)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['archive_sort'] = self.request.GET.get('sort', 'latest')
        context['archive_category'] = (
            self.kwargs.get('category') or self.request.GET.get('cat', '')
        )
        context['archive_year'] = self.kwargs.get('year')
        context['archive_month'] = self.kwargs.get('month')
        context['search_query'] = self.request.GET.get('q', '').strip()

        # 날짜별 목록 (사이드바)
        context['available_dates'] = Article.objects.filter(
            publish_status='published'
        ).dates('published_at', 'month', order='DESC')

        # 카테고리별 기사 수 — aggregate로 쿼리 1번
        counts = Article.objects.filter(publish_status='published').aggregate(
            total=Count('id'),
            domestic=Count('id', filter=Q(category='국내')),
            global_=Count('id', filter=Q(category='글로벌')),
        )
        context['total_count'] = counts['total'] or 0
        context['domestic_count'] = counts['domestic'] or 0
        context['global_count'] = counts['global_'] or 0

        return context


class AboutView(TemplateView):
    """소개 페이지"""
    template_name = "articles/about.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_nav"] = "about"
        return context


class SignupView(CreateView):
    """회원가입"""
    form_class = UserCreationForm
    template_name = 'articles/signup.html'
    success_url = reverse_lazy('articles:login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_nav'] = None
        return context


def logout_view(request):
    """로그아웃 — POST 전용 (Django 5.x 권장)"""
    if request.method == 'POST':
        logout(request)
    return redirect('articles:home')


def honeypot_view(request):
    """Honeypot — 봇 감지 함정 (로그 기록만, Cloud Run 캐시 미사용)"""
    ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', ''))
    if ip:
        ip = ip.split(',')[0].strip()
        logger.warning(f'[Honeypot] 봇 감지 IP: {ip}')
    return HttpResponseNotFound()
