"""
한돈투데이 뷰
- HomeView: 메인 페이지 (최신 기사 목록)
- DetailView: 기사 상세
- ArchiveView: 아카이브 (필터링)
- ArticleDeleteView: 기사 삭제 (staff only)
- ManhwaDetailView: 만평 상세
"""

from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy, reverse
from django.contrib.auth import logout
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect, get_object_or_404, render
from django.http import HttpResponsePermanentRedirect, JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q
from .models import Article


def is_staff(user):
    return user.is_active and user.is_staff


class HomeView(ListView):
    """홈페이지"""
    model = Article
    template_name = 'articles/home.html'
    context_object_name = 'articles'
    paginate_by = 15
    
    def get_queryset(self):
        queryset = Article.objects.filter(publish_status='published').order_by('-published_at')
        category = self.request.GET.get('cat')
        if category:
            queryset = queryset.filter(category=category)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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
        article_id = self.kwargs.get('article_id')
        slug = self.kwargs.get('slug')
        article = get_object_or_404(Article, id=article_id, publish_status='published')
        correct_slug = article.slug or 'no-slug'
        if slug != correct_slug:
            correct_url = reverse('articles:detail', kwargs={
                'article_id': article.id,
                'slug': correct_slug,
            })
            raise self._redirect_exception(correct_url)
        return article

    def _redirect_exception(self, url):
        class SlugRedirect(Exception):
            def __init__(self, redirect_url):
                self.redirect_url = redirect_url
        return SlugRedirect(url)

    def get(self, request, *args, **kwargs):
        try:
            response = super().get(request, *args, **kwargs)
        except Exception as e:
            if hasattr(e, 'redirect_url'):
                return HttpResponsePermanentRedirect(e.redirect_url)
            raise
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
        import re
        match = re.search(r'<blockquote>.*?</blockquote>', article.body_html or '', re.DOTALL)
        context['summary_html'] = match.group(0) if match else None
        context['related_articles'] = Article.objects.filter(
            publish_status='published',
            category=article.category
        ).exclude(id=article.id).order_by('-created_at')[:3]
        return context


class ManhwaDetailView(DetailView):
    """만평 상세 페이지"""
    model = Article
    template_name = 'articles/manhwa_detail.html'
    context_object_name = 'article'

    def get_object(self):
        article_id = self.kwargs.get('article_id')
        slug = self.kwargs.get('slug')
        article = get_object_or_404(Article, id=article_id, publish_status='published', category='만평')
        correct_slug = article.slug or 'no-slug'
        if slug != correct_slug:
            correct_url = reverse('articles:manhwa_detail', kwargs={
                'article_id': article.id,
                'slug': correct_slug,
            })
            return HttpResponsePermanentRedirect(correct_url)
        return article

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
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
        # 이전/다음 만평
        context['prev_manhwa'] = Article.objects.filter(
            publish_status='published',
            category='만평',
            published_at__lt=article.published_at
        ).order_by('-published_at').first()
        context['next_manhwa'] = Article.objects.filter(
            publish_status='published',
            category='만평',
            published_at__gt=article.published_at
        ).order_by('published_at').first()
        return context


class ArchiveView(ListView):
    """아카이브 - 날짜/카테고리 필터링"""
    model = Article
    template_name = 'articles/archive.html'
    context_object_name = 'articles'
    paginate_by = 15
    
    def get_queryset(self):
        sort = self.request.GET.get('sort', 'latest')
        order = '-view_count' if sort == 'popular' else '-created_at'
        queryset = Article.objects.filter(publish_status='published').order_by(order)
        
        category = self.kwargs.get('category')
        if category in ['국내', '글로벌']:
            queryset = queryset.filter(category=category)
        
        q = self.request.GET.get('q', '').strip()
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q) | Q(body_markdown__icontains=q)
            )

        cat = self.request.GET.get('cat', '').strip()
        if cat and not category:
            queryset = queryset.filter(category=cat)

        year = self.kwargs.get('year')
        if year:
            queryset = queryset.filter(created_at__year=year)
        
        month = self.kwargs.get('month')
        if month:
            queryset = queryset.filter(created_at__month=month)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['archive_sort'] = self.request.GET.get('sort', 'latest')
        context['archive_category'] = self.request.GET.get('cat') or self.kwargs.get('category')
        context['archive_year'] = self.kwargs.get('year')
        context['archive_month'] = self.kwargs.get('month')
        context['search_query'] = self.request.GET.get('q', '').strip()
        
        dates = Article.objects.filter(publish_status='published').dates('created_at', 'month', order='DESC')
        context['available_dates'] = dates
        
        context['domestic_count'] = Article.objects.filter(publish_status='published', category='국내').count()
        context['global_count'] = Article.objects.filter(publish_status='published', category='글로벌').count()
        context['briefing_count'] = Article.objects.filter(publish_status='published', category='시황').count()
        context['manhwa_count'] = Article.objects.filter(publish_status='published', category='만평').count()
        context['webtoon_count'] = Article.objects.filter(publish_status='published', category='웹툰').count()
        context['total_count'] = Article.objects.filter(publish_status='published').count()
        
        return context


@require_POST
@user_passes_test(is_staff, login_url='/login/')
def article_delete(request, article_id):
    """기사 삭제 — staff 전용. JSON 응답 반환."""
    article = get_object_or_404(Article, id=article_id)
    title = article.title[:60]
    article.delete()
    return JsonResponse({'ok': True, 'message': f'삭제 완료: {title}'})


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
    """Honeypot — 봇 감지 함정."""
    from django.core.cache import cache
    from django.http import HttpResponseNotFound
    import logging
    logger = logging.getLogger(__name__)
    ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', ''))
    if ip:
        ip = ip.split(',')[0].strip()
        cache.set(f'honeypot_blocked_{ip}', True, timeout=60 * 60 * 24)
        logger.warning(f'[Honeypot] 봇 감지 IP: {ip}')
    return HttpResponseNotFound()


def about_view(request):
    """소개 페이지"""
    return render(request, 'articles/about.html')


def search_view(request):
    """검색 — 아카이브로 리다이렉트"""
    q = request.GET.get('q', '')
    url = reverse('articles:archive')
    if q:
        url += f'?q={q}'
    return redirect(url)
