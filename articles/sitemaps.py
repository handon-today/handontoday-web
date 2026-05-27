from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Article

SITE_URL = 'https://handontoday.com'

class ArticleSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8
    protocol = 'https'

    def items(self):
        return Article.objects.filter(publish_status='published').order_by('-published_at')

    def lastmod(self, obj):
        return obj.published_at

    def location(self, obj):
        slug = obj.slug or 'no-slug'
        return f'/article/{obj.id}-{slug}/'

    def get_urls(self, page=1, site=None, protocol=None):
        from django.contrib.sitemaps import SitemapNotFound
        from django.utils.http import http_date
        urls = []
        for item in self.paginator.page(page).object_list:
            loc = f"{SITE_URL}{self.location(item)}"
            priority = self.get_priority(item)
            lastmod = self.lastmod(item) if callable(self.lastmod) else self.lastmod
            if hasattr(lastmod, '__call__'):
                lastmod = lastmod(item)
            urls.append({
                'item': item,
                'location': loc,
                'lastmod': lastmod,
                'changefreq': self.changefreq,
                'priority': str(priority if priority is not None else ''),
                'alternates': [],
                'x_default': None,
            })
        return urls


class StaticSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.5
    protocol = 'https'

    def items(self):
        return ['articles:home', 'articles:archive']

    def location(self, item):
        return reverse(item)

    def get_urls(self, page=1, site=None, protocol=None):
        urls = []
        for item in self.items():
            loc = f"{SITE_URL}{self.location(item)}"
            urls.append({
                'item': item,
                'location': loc,
                'lastmod': None,
                'changefreq': self.changefreq,
                'priority': str(self.priority),
                'alternates': [],
                'x_default': None,
            })
        return urls
