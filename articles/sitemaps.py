from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Article

class ArticleSitemap(Sitemap):
    changefreq = 'daily'
    priority = 0.8
    protocol = 'https'

    def items(self):
        return Article.objects.filter(publish_status='published').order_by('-published_at')

    def lastmod(self, obj):
        return obj.published_at

    def location(self, obj):
        return f'/article/{obj.id}/{obj.slug}/'

    def get_urls(self, page=1, site=None, protocol=None):
        from django.contrib.sites.requests import RequestSite
        class FakeSite:
            domain = 'handontoday.com'
            name = 'handontoday.com'
        return super().get_urls(page=page, site=FakeSite(), protocol='https')

class StaticSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.5
    protocol = 'https'

    def items(self):
        return ['articles:home', 'articles:archive']

    def location(self, item):
        return reverse(item)

    def get_urls(self, page=1, site=None, protocol=None):
        class FakeSite:
            domain = 'handontoday.com'
            name = 'handontoday.com'
        return super().get_urls(page=page, site=FakeSite(), protocol='https')
