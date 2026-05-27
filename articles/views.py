"""
한돈투데이 뷰
"""
from django.views.generic import ListView, DetailView, CreateView, TemplateView
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy, reverse
from django.contrib.auth import logout
from django.shortcuts import redirect, get_object_or_404
from django.http import HttpResponsePermanentRedirect, HttpResponse
from .models import Article


class HomeView(ListView):
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
            self.object = self.get_object()
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

        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

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


class ArchiveView(ListView):
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
        context['archive_category'] = self.kwargs.get('category')
        context['archive_year'] = self.kwargs.get('year')
        context['archive_month'] = self.kwargs.get('month')
        context['available_dates'] = Article.objects.filter(
            publish_status='published'
        ).dates('created_at', 'month', order='DESC')
        context['domestic_count'] = Article.objects.filter(publish_status='published', category='국내').count()
        context['global_count'] = Article.objects.filter(publish_status='published', category='글로벌').count()
        return context


class AboutView(TemplateView):
    template_name = 'articles/about.html'


class SignupView(CreateView):
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


def robots_txt(request):
    content = "User-agent: *\nAllow: /\nDisallow: /admin/\nSitemap: https://handontoday.com/sitemap.xml"
    return HttpResponse(content, content_type='text/plain')


def honeypot_view(request):
    from django.core.cache import cache
    from django.http import HttpResponseNotFound
    import logging
    logger = logging.getLogger(__name__)
    ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', ''))
    if ip:
        ip = ip.split(',')[0].strip()
        cache.set(f'honeypot_blocked_{ip}', True, timeout=60 * 60 * 24)
        logger.warning(f'[Honeypot] 봇 감지 IP: {ip}')
    from django.http import HttpResponseNotFound
    return HttpResponseNotFound()
