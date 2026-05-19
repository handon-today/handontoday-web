"""
한돈투데이 뷰
- HomeView: 메인 페이지 (최신 기사 목록)
- DetailView: 기사 상세
- ArchiveView: 아카이브 (필터링)
"""

from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
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
        
        # 통계
        context['korea_count'] = Article.objects.filter(publish_status='published', category='국내').count()
        context['global_count'] = Article.objects.filter(publish_status='published', category='글로벌').count()
        context['total_views'] = sum(Article.objects.filter(publish_status='published').values_list('view_count', flat=True))
        from django.utils import timezone
        today = timezone.localdate()
        context['today_views'] = sum(Article.objects.filter(publish_status='published', published_at__date=today).values_list('view_count', flat=True))
        
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
        
        # id로 기사 찾기
        article = get_object_or_404(
            Article,
            id=article_id,
            publish_status='published'
        )
        
        # slug 불일치 시에도 표시 (redirect는 나중에 추가)
        return article
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 조회수 증가
        article = self.object
        article.view_count += 1
        article.save(update_fields=['view_count'])
        
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

