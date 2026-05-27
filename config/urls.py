from django.contrib import admin
from django.urls import path, include
from django.contrib.sitemaps.views import sitemap

from django.http import HttpResponse
from articles.sitemaps import ArticleSitemap, StaticSitemap




sitemaps = {
    'articles': ArticleSitemap,
    'static': StaticSitemap,
}


def sitemap_view(request):
    """도메인을 handontoday.com으로 고정한 sitemap 뷰"""
    request.META['HTTP_HOST'] = 'handontoday.com'
    request.META['SERVER_NAME'] = 'handontoday.com'
    request.META['SERVER_PORT'] = '443'
    request.META['wsgi.url_scheme'] = 'https'
    return sitemap(request, sitemaps=sitemaps, sitemap_url_name='sitemap')


def robots_txt(request):
    content = (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /admin/\n"
        "Disallow: /login/\n"
        "Disallow: /signup/\n"
        "\n"
        "Sitemap: https://handontoday.com/sitemap.xml"
    )
    return HttpResponse(content, content_type='text/plain')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('sitemap.xml', sitemap_view, name='sitemap'),
    path('robots.txt', robots_txt),
    path('', include('articles.urls')),
]
