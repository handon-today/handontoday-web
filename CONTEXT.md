# 한돈투데이 프로젝트 컨텍스트

## 시스템 구조
- GCP Cloud Functions: ~/handon-functions (GitHub: handon-today/handontoday-functions)
- Django 웹사이트: ~/handontoday-web (GitHub: handon-today/handontoday-web)
- DB: Cloud SQL PostgreSQL (handontoday-db, DB: handontoday_db)
- AI: OpenRouter + Gemini 2.5 Flash Lite
- 이미지: Unsplash API (기사 제목 → Gemini 키워드 → 랜덤 선택)
- 알림: Slack #handontoday-bot

## 현재 상태
- 매일 10회 자동 실행, 회당 4건 생성
- Django 홈: 15건씩 페이지네이션
- 통계 바: 국내/글로벌/특집/총방문 (footer 위)
- Unsplash 이미지 자동 추가 완료

## Secret Manager 키
- openrouter-api-key
- slack-webhook-url
- unsplash-api-key
- cloud-sql-password

## 배포 명령
gcloud functions deploy handon-news-pipeline \
  --gen2 --runtime=python311 --region=asia-northeast3 \
  --source=. --entry-point=run_pipeline \
  --trigger-http --allow-unauthenticated \
  --memory=512MB --timeout=540s \
  --set-secrets='OPENROUTER_API_KEY=openrouter-api-key:latest,SLACK_WEBHOOK_URL=slack-webhook-url:latest,UNSPLASH_API_KEY=unsplash-api-key:latest,CLOUD_SQL_PASSWORD=cloud-sql-password:latest' \
  --set-env-vars='DB_HOST=/cloudsql/handontoday:asia-northeast3:handontoday-db,DB_NAME=handontoday_db,DB_USER=handontoday-user,GCS_BUCKET=handontoday-articles'
