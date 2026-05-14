-- ================================================================
-- Step 6-4: generated_articles 테이블에 새 컬럼 추가
-- ================================================================

BEGIN;

-- 1. 부제목
ALTER TABLE generated_articles 
ADD COLUMN deck TEXT;

-- 2. 마크다운/HTML 본문 (body_markdown은 나중에 body 복사)
ALTER TABLE generated_articles 
ADD COLUMN body_markdown TEXT;

ALTER TABLE generated_articles 
ADD COLUMN body_html TEXT;

-- 3. 태그 (JSONB 배열)
ALTER TABLE generated_articles 
ADD COLUMN tags JSONB DEFAULT '[]'::jsonb;

-- 4. 원본 출처 정보
ALTER TABLE generated_articles 
ADD COLUMN source_titles JSONB DEFAULT '[]'::jsonb;

ALTER TABLE generated_articles 
ADD COLUMN source_urls JSONB DEFAULT '[]'::jsonb;

-- 5. 플래그 (추천/인기)
ALTER TABLE generated_articles 
ADD COLUMN is_featured BOOLEAN DEFAULT FALSE NOT NULL;

ALTER TABLE generated_articles 
ADD COLUMN is_hot BOOLEAN DEFAULT FALSE NOT NULL;

-- 6. 메타 정보
ALTER TABLE generated_articles 
ADD COLUMN read_minutes INTEGER DEFAULT 0 NOT NULL;

ALTER TABLE generated_articles 
ADD COLUMN view_count INTEGER DEFAULT 0 NOT NULL;

-- 7. 타임스탬프
ALTER TABLE generated_articles 
ADD COLUMN created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL;

ALTER TABLE generated_articles 
ADD COLUMN updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL;

-- 8. 기존 body 내용을 body_markdown으로 복사
UPDATE generated_articles 
SET body_markdown = body;

-- 9. body_markdown을 NOT NULL로 변경
ALTER TABLE generated_articles 
ALTER COLUMN body_markdown SET NOT NULL;

-- 10. created_at을 generated_at 값으로 채우기 (기존 데이터 보정)
UPDATE generated_articles 
SET created_at = generated_at,
    updated_at = generated_at;

-- 11. read_minutes 계산 (body_markdown 기준, 분당 200자 가정)
UPDATE generated_articles 
SET read_minutes = GREATEST(1, LENGTH(body_markdown) / 200);

COMMIT;

-- 검증 쿼리
SELECT 
  'Total columns' AS check_type,
  COUNT(*) AS count
FROM information_schema.columns 
WHERE table_name = 'generated_articles';

SELECT 
  'Rows with body_markdown' AS check_type,
  COUNT(*) AS count
FROM generated_articles 
WHERE body_markdown IS NOT NULL;

SELECT 
  'Average read_minutes' AS check_type,
  ROUND(AVG(read_minutes)) AS count
FROM generated_articles;
