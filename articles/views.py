"""
한돈투데이 뷰
- HomeView: 메인 페이지 (최신 기사 목록, 만평/웹툰 제외)
- DetailView: 기사 상세
- ManhwaDetailView: 만평 전용 상세
- ArchiveView: 아카이브 (필터링, 만평/웹툰 포함)
- AboutView: 소개 페이지
"""

from django.views.generic import ListView, DetailView, CreateView, TemplateView
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy, reverse
from django.contrib.auth import logout
from django.shortcuts import redirect, get_object_or_404
from django.http import HttpResponsePermanentRedirect
from django.db.models import Q, Count, Sum
from django.utils import timezone
from .models import Article


# 홈/헤더에 노출하지 않을 카테고리
HIDDEN_CATEGORIES = []


class HomeView(ListView):
    """홈페이지 — 만평/웹툰 제외"""
    model = Article
    template_name = 'articles/home.html'
    context_object_name = 'articles'
    paginate_by = 15

    def get_queryset(self):
        queryset = Article.objects.filter(
            publish_status='published',
            published_at__lte=timezone.now(),
        ).exclude(
            category__in=HIDDEN_CATEGORIES,
        ).order_by('-published_at')

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
        elif category == '시황':
            context['active_nav'] = 'market'
        else:
            context['active_nav'] = 'home'

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
            published_at__date=today,
        ).aggregate(s=Sum('view_count'))['s'] or 0

        return context


class ArticleDetailView(DetailView):
    """기사 상세 페이지 (국내/글로벌/시황)"""
    model = Article
    template_name = 'articles/detail.html'
    context_object_name = 'article'

    def get_object(self):
        article_id = self.kwargs.get('article_id')
        slug = self.kwargs.get('slug')

        article = get_object_or_404(
            Article,
            id=article_id,
            publish_status='published',
        )

        correct_slug = article.slug or 'no-slug'
        if slug != correct_slug:
            if article.category == '만평':
                correct_url = reverse('articles:manhwa_detail', kwargs={
                    'article_id': article.id,
                    'slug': correct_slug,
                })
            else:
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
            article = self.object
            session_key = f'viewed_article_{article.id}'
            if not request.session.get(session_key):
                article.view_count += 1
                article.save(update_fields=['view_count'])
                request.session[session_key] = True
            return response
        except Exception as e:
            if hasattr(e, 'redirect_url'):
                return HttpResponsePermanentRedirect(e.redirect_url)
            raise

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        article = self.object

        import re
        match = re.search(r'<blockquote>.*?</blockquote>', article.body_html or '', re.DOTALL)
        context['summary_html'] = match.group(0) if match else None

        context['related_articles'] = Article.objects.filter(
            publish_status='published',
            category=article.category,
        ).exclude(id=article.id).order_by('-created_at')[:3]

        return context


class ManhwaDetailView(DetailView):
    """만평 전용 상세 페이지"""
    model = Article
    template_name = 'articles/manhwa_detail.html'
    context_object_name = 'article'

    def get_object(self):
        article_id = self.kwargs.get('article_id')
        slug = self.kwargs.get('slug')

        article = get_object_or_404(
            Article,
            id=article_id,
            category='만평',
            publish_status='published',
        )

        correct_slug = article.slug or 'no-slug'
        if slug != correct_slug:
            correct_url = reverse('articles:manhwa_detail', kwargs={
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
            article = self.object
            session_key = f'viewed_article_{article.id}'
            if not request.session.get(session_key):
                article.view_count += 1
                article.save(update_fields=['view_count'])
                request.session[session_key] = True
            return response
        except Exception as e:
            if hasattr(e, 'redirect_url'):
                return HttpResponsePermanentRedirect(e.redirect_url)
            raise

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        article = self.object

        context['prev_manhwa'] = Article.objects.filter(
            category='만평',
            publish_status='published',
            published_at__lt=article.published_at,
        ).order_by('-published_at').first()

        context['next_manhwa'] = Article.objects.filter(
            category='만평',
            publish_status='published',
            published_at__gt=article.published_at,
        ).order_by('published_at').first()

        return context


class ArchiveView(ListView):
    """아카이브 — 만평/웹툰 포함 전체 카테고리"""
    model = Article
    template_name = 'articles/archive.html'
    context_object_name = 'articles'
    paginate_by = 15

    def get_queryset(self):
        sort = self.request.GET.get('sort', 'latest')
        order = '-view_count' if sort == 'popular' else '-created_at'

        queryset = Article.objects.filter(
            publish_status='published',
            published_at__lte=timezone.now(),
        ).order_by(order)

        category = self.kwargs.get('category') or self.request.GET.get('cat')
        if category in ['국내', '글로벌', '시황', '만평', '웹툰']:
            queryset = queryset.filter(category=category)

        q = self.request.GET.get('q', '').strip()
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q) | Q(body_markdown__icontains=q)
            )

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
        context['archive_category'] = self.kwargs.get('category') or self.request.GET.get('cat')
        context['archive_year'] = self.kwargs.get('year')
        context['archive_month'] = self.kwargs.get('month')
        context['search_query'] = self.request.GET.get('q', '')

        dates = Article.objects.filter(
            publish_status='published',
        ).dates('created_at', 'month', order='DESC')
        context['available_dates'] = dates

        counts = Article.objects.filter(
            publish_status='published',
        ).aggregate(
            total=Count('id'),
            domestic=Count('id', filter=Q(category='국내')),
            global_=Count('id', filter=Q(category='글로벌')),
            briefing=Count('id', filter=Q(category='시황')),
            manhwa=Count('id', filter=Q(category='만평')),
            webtoon=Count('id', filter=Q(category='웹툰')),
        )
        context['total_count'] = counts['total'] or 0
        context['domestic_count'] = counts['domestic'] or 0
        context['global_count'] = counts['global_'] or 0
        context['briefing_count'] = counts['briefing'] or 0
        context['manhwa_count'] = counts['manhwa'] or 0
        context['webtoon_count'] = counts['webtoon'] or 0

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
    logout(request)
    return redirect('articles:home')


def honeypot_view(request):
    from django.core.cache import cache
    from django.http import HttpResponseNotFound
    import logging
    logger = logging.getLogger(__name__)

    ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', ''))
    if ip:
        ip = ip.split(',')[0].strip()
        cache_key = f'honeypot_blocked_{ip}'
        cache.set(cache_key, True, timeout=60 * 60 * 24)
        logger.warning(f'[Honeypot] 봇 감지 IP: {ip}')

    return HttpResponseNotFound()
