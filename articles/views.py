"""
한돈투데이 뷰
- HomeView: 메인 페이지 (최신 기사 목록)
- DetailView: 기사 상세
- ArchiveView: 아카이브 (필터링)
"""

from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy, reverse
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from django.http import HttpResponsePermanentRedirect
from django.db.models import Q
from .models import Article


class HomeView(ListView):
    """홈페이지"""
    model = Article
    template_name = 'articles/home.html'
    context_object_name = 'articles'
    paginate_by = 15
    
    def get_queryset(self):
        """카테고리 필터링"""
        queryset = Article.objects.filter(publish_status='published').order_by('-published_at')
        
        # URL 파라미터로 카테고리 필터
        category = self.request.GET.get('cat')
        if category:
            queryset = queryset.filter(category=category)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 카테고리별 active 상태
        category = self.request.GET.get('cat')
        if category == '국내':
            context['active_nav'] = 'domestic'
        elif category == '글로벌':
            context['active_nav'] = 'global'
        elif category == 'market':
            context['active_nav'] = 'market'
        elif category == 'policy':
            context['active_nav'] = 'policy'
        else:
            context['active_nav'] = 'home'
        
        # 통계 — aggregate로 DB 쿼리 최소화
        from django.db.models import Count, Sum, Q
        from django.utils import timezone
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
        """URL에서 id와 slug로 조회"""
        article_id = self.kwargs.get('article_id')
        slug = self.kwargs.get('slug')

        article = get_object_or_404(
            Article,
            id=article_id,
            publish_status='published'
        )

        # slug 불일치 시 올바른 URL로 301 redirect
        correct_slug = article.slug or 'no-slug'
        if slug != correct_slug:
            correct_url = reverse('articles:detail', kwargs={
                'article_id': article.id,
                'slug': correct_slug,
            })
            raise self._redirect_exception(correct_url)

        return article

    def _redirect_exception(self, url):
        """301 redirect를 위한 헬퍼"""
        class SlugRedirect(Exception):
            def __init__(self, redirect_url):
                self.redirect_url = redirect_url
        return SlugRedirect(url)

    def get(self, request, *args, **kwargs):
        try:
            return super().get(request, *args, **kwargs)
        except Exception as e:
            if hasattr(e, 'redirect_url'):
                return HttpResponsePermanentRedirect(e.redirect_url)
            raise
    
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        
        # 세션 기반 중복 방지 — 같은 기사 재방문 시 조회수 안 올림
        article = self.object
        session_key = f'viewed_article_{article.id}'
        if not request.session.get(session_key):
            article.view_count += 1
            article.save(update_fields=['view_count'])
            request.session[session_key] = True
        
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        article = self.object
        
        # 같은 카테고리 최신 기사 3개
        context['related_articles'] = Article.objects.filter(
            publish_status='published',
            category=article.category
        ).exclude(
            id=article.id
        ).order_by('-created_at')[:3]
        
        return context


class ArchiveView(ListView):
    """아카이브 - 날짜/카테고리 필터링"""
    model = Article
    template_name = 'articles/archive.html'
    context_object_name = 'articles'
    paginate_by = 15
    
    def get_queryset(self):
        """필터링된 기사 목록"""
        sort = self.request.GET.get('sort', 'latest')
        if sort == 'popular':
            order = '-view_count'
        else:
            order = '-created_at'
        queryset = Article.objects.filter(
            publish_status='published'
        ).order_by(order)
        
        # 카테고리
        category = self.kwargs.get('category')
        if category in ['국내', '글로벌']:
            queryset = queryset.filter(category=category)
        
        # 년도
        year = self.kwargs.get('year')
        if year:
            queryset = queryset.filter(created_at__year=year)
        
        # 월
        month = self.kwargs.get('month')
        if month:
            queryset = queryset.filter(created_at__month=month)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 필터 정보
        context['archive_sort'] = self.request.GET.get('sort', 'latest')
        context['archive_category'] = self.kwargs.get('category')
        context['archive_year'] = self.kwargs.get('year')
        context['archive_month'] = self.kwargs.get('month')
        
        # 사용 가능한 년도/월 목록
        dates = Article.objects.filter(
            publish_status='published'
        ).dates('created_at', 'month', order='DESC')
        
        context['available_dates'] = dates
        
        # 카테고리별 개수 (사이드바용)
        context['domestic_count'] = Article.objects.filter(
            publish_status='published',
            category='국내'
        ).count()
        
        context['global_count'] = Article.objects.filter(
            publish_status='published',
            category='글로벌'
        ).count()
        
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
    """로그아웃"""
    logout(request)
    return redirect('articles:home')


def honeypot_view(request):
    """Honeypot — 봇 감지 함정. 접근 시 IP를 캐시에 24시간 등록."""
    from django.core.cache import cache
    from django.http import HttpResponseNotFound
    import logging
    logger = logging.getLogger(__name__)

    ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', ''))
    if ip:
        ip = ip.split(',')[0].strip()
        cache_key = f'honeypot_blocked_{ip}'
        cache.set(cache_key, True, timeout=60 * 60 * 24)  # 24시간
        logger.warning(f'[Honeypot] 봇 감지 IP: {ip}')

    return HttpResponseNotFound()
