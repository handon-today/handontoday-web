"""
한돈투데이 Article 모델
- 기존 generated_articles 테이블과 매핑
- SYNC_DOC.md 기준 완전 구현
"""

from django.db import models
from django.utils import timezone
from django.urls import reverse


class Article(models.Model):
    """자동 생성 양돈 뉴스 기사"""
    
    # 카테고리 선택지
    CATEGORY_CHOICES = [
        ('국내', '국내'),
        ('글로벌', '글로벌'),
        ('시황', '시황'),
    ]
    
    # 발행 상태
    STATUS_CHOICES = [
        ('draft', '초안'),
        ('published', '발행됨'),
        ('archived', '보관됨'),
    ]
    
    # 기본 정보
    title = models.TextField(verbose_name='제목')
    deck = models.TextField(blank=True, null=True, verbose_name='부제목')
    slug = models.TextField(blank=True, null=True, verbose_name='URL 슬러그')
    
    # 본문
    image_url = models.URLField(max_length=500, blank=True, null=True, verbose_name='이미지 URL')
    body = models.TextField(verbose_name='본문 (레거시)')  # 기존 컬럼, deprecated 예정
    body_markdown = models.TextField(verbose_name='마크다운 본문')
    body_html = models.TextField(blank=True, null=True, verbose_name='HTML 본문')
    
    # 분류
    category = models.TextField(choices=CATEGORY_CHOICES, verbose_name='카테고리')
    tags = models.JSONField(default=list, verbose_name='태그')
    
    # 메타데이터
    match_reason = models.TextField(blank=True, null=True, verbose_name='짝짓기 사유')
    source_titles = models.JSONField(default=list, verbose_name='원본 제목들')
    source_urls = models.JSONField(default=list, verbose_name='원본 URL들')
    
    # 검수
    validation_passed = models.BooleanField(default=False, verbose_name='검수 통과')
    validation_issues = models.JSONField(blank=True, null=True, verbose_name='검수 이슈')
    
    # AI 비용
    input_tokens = models.IntegerField(blank=True, null=True, verbose_name='입력 토큰')
    output_tokens = models.IntegerField(blank=True, null=True, verbose_name='출력 토큰')
    cost_usd = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True, verbose_name='비용(USD)')
    
    # 발행
    publish_status = models.TextField(choices=STATUS_CHOICES, default='draft', verbose_name='발행 상태')
    published_at = models.DateTimeField(blank=True, null=True, verbose_name='발행 시각')
    
    # 플래그
    is_featured = models.BooleanField(default=False, verbose_name='추천 기사')
    is_hot = models.BooleanField(default=False, verbose_name='인기 기사')
    
    # 통계
    read_minutes = models.IntegerField(default=0, verbose_name='읽는 시간(분)')
    view_count = models.IntegerField(default=0, verbose_name='조회수')
    
    # 타임스탬프
    generated_at = models.DateTimeField(default=timezone.now, verbose_name='생성 시각')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='생성 시각')
    updated_at = models.DateTimeField(default=timezone.now, verbose_name='수정 시각')
    
    # 외래키
    pipeline_run_id = models.BigIntegerField(blank=True, null=True, verbose_name='파이프라인 실행 ID')
    
    class Meta:
        db_table = 'generated_articles'  # 기존 테이블 이름
        ordering = ['-created_at']
        verbose_name = '기사'
        verbose_name_plural = '기사들'
        indexes = [
            models.Index(fields=['-created_at'], name='idx_article_created'),
            models.Index(fields=['slug'], name='idx_article_slug'),
            models.Index(fields=['category'], name='idx_article_category'),
            models.Index(fields=['publish_status'], name='idx_article_status'),
        ]
    
    def __str__(self):
        return f"[{self.category}] {self.title[:50]}"
    
    def get_absolute_url(self):
        """기사 상세 페이지 URL"""
        return reverse('articles:detail', kwargs={
            'article_id': self.id,
            'slug': self.slug or 'no-slug',
        })
    
    def save(self, *args, **kwargs):
        """저장 시 updated_at 자동 갱신"""
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)
    
    @property
    def is_published(self):
        """발행 여부"""
        return self.publish_status == 'published' and self.published_at is not None
    
    @property
    def display_body(self):
        """표시용 본문 (HTML 우선, 없으면 마크다운)"""
        return self.body_html or self.body_markdown
