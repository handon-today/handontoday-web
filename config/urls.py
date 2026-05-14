"""
한돈투데이 URL 설정 (config/urls.py)
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('articles.urls')),
]
