"""
slug 자동 생성 스크립트
- 기존 68건의 NULL slug를 title 기반으로 생성
- 중복 방지: slug가 이미 있으면 뒤에 숫자 붙임
"""

import os
import re
from decouple import config
from google.cloud.sql.connector import Connector
import sqlalchemy
from slugify import slugify

# DB 연결 정보 (.env에서 읽기)
CONNECTION_NAME = config("CLOUD_SQL_CONNECTION_NAME")
DB_NAME = config("DB_NAME")
DB_USER = config("DB_USER")
DB_PASSWORD = config("DB_PASSWORD")

def get_db_engine():
    """Cloud SQL 연결"""
    connector = Connector()
    
    def getconn():
        return connector.connect(
            CONNECTION_NAME,
            "pg8000",
            user=DB_USER,
            password=DB_PASSWORD,
            db=DB_NAME,
        )
    
    return sqlalchemy.create_engine(
        "postgresql+pg8000://",
        creator=getconn,
    )

def clean_title_for_slug(title):
    """제목에서 이모지·특수문자 제거 후 slug 생성"""
    # 이모지 제거
    title = re.sub(r'[^\w\s가-힣a-zA-Z0-9-]', '', title)
    # 앞뒤 공백 제거
    title = title.strip()
    # slugify (한글 지원)
    return slugify(title, max_length=100, word_boundary=True)

def main():
    print(f"\n연결 정보:")
    print(f"  CONNECTION_NAME: {CONNECTION_NAME}")
    print(f"  DB_NAME: {DB_NAME}")
    print(f"  DB_USER: {DB_USER}\n")
    
    engine = get_db_engine()
    
    with engine.connect() as conn:
        # 1. slug가 NULL인 기사들 가져오기
        result = conn.execute(
            sqlalchemy.text(
                "SELECT id, title FROM generated_articles WHERE slug IS NULL ORDER BY id"
            )
        )
        rows = result.fetchall()
        
        print(f"총 {len(rows)}건의 slug 생성 시작...\n")
        
        existing_slugs = set()
        updated_count = 0
        
        for row in rows:
            article_id = row[0]
            title = row[1]
            
            # slug 생성
            base_slug = clean_title_for_slug(title)
            
            if not base_slug:
                base_slug = f"article-{article_id}"
            
            # 중복 체크
            slug = base_slug
            counter = 1
            while slug in existing_slugs:
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            existing_slugs.add(slug)
            
            # DB 업데이트
            conn.execute(
                sqlalchemy.text(
                    "UPDATE generated_articles SET slug = :slug WHERE id = :id"
                ),
                {"slug": slug, "id": article_id}
            )
            conn.commit()
            
            updated_count += 1
            if updated_count <= 5 or updated_count % 10 == 0 or updated_count == len(rows):
                print(f"  [{updated_count}/{len(rows)}] id={article_id:3d} | {slug[:60]}")
        
        print(f"\n✅ 완료: {updated_count}건 slug 생성")
        
        # 검증
        result = conn.execute(
            sqlalchemy.text(
                "SELECT COUNT(*) FROM generated_articles WHERE slug IS NULL"
            )
        )
        null_count = result.fetchone()[0]
        
        result = conn.execute(
            sqlalchemy.text(
                "SELECT COUNT(DISTINCT slug) FROM generated_articles WHERE slug IS NOT NULL"
            )
        )
        unique_count = result.fetchone()[0]
        
        print(f"\n검증:")
        print(f"  - slug NULL 개수: {null_count} (0이어야 함)")
        print(f"  - slug UNIQUE 개수: {unique_count} ({len(rows)}이어야 함)")

if __name__ == "__main__":
    main()
