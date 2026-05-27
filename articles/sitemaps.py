from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Article


class HanDonSitemap(Sitemap):
    """handontoday.com 도메인과 https 프로토콜 고정"""
    protocol = 'https'

    def get_domain(self, site=None):
        return 'handontoday.com'


class ArticleSitemap(HanDonSitemap):
    changefreq = "daily"
    priority = 0.8

    def items(self):
        return Article.objects.filter(publish_status='published').order_by('-published_at')

    def lastmod(self, obj):
        return obj.published_at

    def location(self, obj):
        slug = obj.slug or 'no-slug'
        return f'/article/{obj.id}-{slug}/'


class StaticSitemap(HanDonSitemap):
    changefreq = "weekly"
    priority = 0.5

    def items(self):
        return ['articles:home', 'articles:archive']

    def location(self, item):
        return reverse(item)
