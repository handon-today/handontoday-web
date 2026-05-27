from django.contrib import admin
from django.urls import path, include
from django.contrib.sitemaps.views import sitemap
from django.http import HttpResponse
from articles.sitemaps import ArticleSitemap, StaticSitemap

sitemaps = {
    'articles': ArticleSitemap,
    'static': StaticSitemap,
}

def robots_txt(request):
    content = "User-agent: *\nAllow: /\nDisallow: /admin/\nSitemap: https://handontoday.com/sitemap.xml"
    return HttpResponse(content, content_type='text/plain')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
    path('robots.txt', robots_txt),
    path('', include('articles.urls')),
]
