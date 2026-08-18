# Sesli Asistan Paneli

LiveKit tabanlı, Türkçe konuşan bir sesli asistan (voice agent) ve bunu yönetmek için bir web paneli.
Kullanıcı tarayıcıdan mikrofonla asistanla canlı konuşabilir; sistem promptunu düzenleyebilir; geçmiş
konuşmaların transkriptini ve (yapılandırıldıysa) ses kaydını görüntüleyebilir.

## Mimari

Üç bağımsız süreç birlikte çalışır:

```
frontend/   Next.js — kullanıcı arayüzü (sistem promptu, konuşma listesi/detayı, canlı görüşme)
backend/    FastAPI — sistem promptu API'si, LiveKit token üretimi, konuşma kayıtları (Supabase)
agent.py    LiveKit Agents worker — STT/LLM/TTS ile asistanın kendisi (voice_agent/ paketini kullanır)
```

Veri akışı özet:

1. Frontend, backend'den bir LiveKit erişim token'ı ister (`POST /api/conversations`); backend aynı
   isteğe karşılık gelen bir `conversation_id` (= LiveKit oda adı) üretip Supabase'e kaydeder.
2. Kullanıcı bu token'la LiveKit odasına bağlanır; `agent.py` worker'ı LiveKit Cloud tarafından
   otomatik olarak bu odaya atanır ve görüşmeyi yürütür.
3. Görüşme bitince `agent.py`, transkripti hemen backend'e yazar (`PATCH /api/conversations/{id}`).
   Ses kaydı (varsa) LiveKit Egress üzerinden Supabase Storage'a doğrudan yüklenir; `agent.py` bu
   yüklemenin bittiğini kendisi doğrulayıp backend'e ayrıca haber verir
   (`POST /api/conversations/{id}/recording-ready`) — bu adım transkript kaydını geciktirmez.
4. Frontend, konuşma detay sayfasında backend'den transkripti ve (varsa) ses kaydının herkese açık
   URL'ini okur.

## Gereksinimler

- Python 3.14+ ve [uv](https://docs.astral.sh/uv/)
- Node.js 20+ ve npm
- Bir [LiveKit Cloud](https://cloud.livekit.io) projesi
- Bir [Supabase](https://supabase.com) projesi (veritabanı + dosya depolama için)
- Azure OpenAI (STT/LLM/TTS) ve [Tavily](https://tavily.com) (web araması aracı) erişimi

## Kurulum

### 1. Bağımlılıklar

```bash
uv sync                     # agent.py + backend için (aynı sanal ortamı paylaşırlar)
npm install --prefix frontend
```

### 2. `.env`

Proje kökünde **tek bir** `.env` dosyası kullanılır; hem `agent.py`/`backend` hem de
`frontend/next.config.ts` (build sırasında) buradan okur. Doldurulması gerekenler:

| Değişken | Açıklama |
| --- | --- |
| `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET` | LiveKit Cloud proje bilgileri |
| `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` | Supabase proje URL'i ve `service_role` anahtarı (Project Settings → API) |
| `SUPABASE_RECORDINGS_BUCKET` | Ses kayıtlarının tutulacağı bucket adı (bkz. Adım 3), varsayılan `recordings` |
| `RECORDING_S3_BUCKET`, `RECORDING_S3_REGION`, `RECORDING_S3_ACCESS_KEY`, `RECORDING_S3_SECRET_KEY`, `RECORDING_S3_ENDPOINT` | Supabase Storage'ın **S3-uyumlu** bağlantı bilgileri (Project Settings → Storage → S3 Connection → "New access key" — `SUPABASE_SERVICE_ROLE_KEY`'den farklı bir anahtar çiftidir). `RECORDING_S3_BUCKET`, `SUPABASE_RECORDINGS_BUCKET` ile aynı olmalı. Boş bırakılırsa ses kaydı devre dışı kalır, sadece transkript kaydedilir. |
| `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `OPENAI_API_VERSION` | Azure OpenAI erişimi |
| `STT_DEPLOYMENT_NAME`, `LLM_DEPLOYMENT_NAME`, `TTS_DEPLOYMENT_NAME` | Azure'daki model deployment adları |
| `TAVILY_API_KEY` | `web_search` aracı için |
| `NEXT_PUBLIC_API_URL` | Frontend'in backend'i bulacağı adres, varsayılan `http://localhost:5000` |
| `CORS_ORIGINS` | Backend'in kabul edeceği origin(ler), varsayılan `http://localhost:3000` |
| `BACKEND_API_URL` | `agent.py`'nin backend'i bulacağı adres, varsayılan `http://localhost:5000` |

### 3. Supabase: tablo ve bucket

SQL Editor'de:

```sql
create table conversations (
  id text primary key,
  status text not null default 'active',
  started_at timestamptz not null,
  ended_at timestamptz,
  transcript jsonb,
  has_recording boolean not null default false,
  error_message text
);
```

Storage → New bucket → adı `.env`'deki `SUPABASE_RECORDINGS_BUCKET` ile aynı (varsayılan
`recordings`) → **Public bucket** açık.

## Çalıştırma

Üç süreci ayrı terminallerde başlatın (proje kökünden):

```bash
uv run python agent.py dev                                    # sesli asistan
uv run uvicorn app:app --reload --port 5000 --app-dir backend # API
npm run dev --prefix frontend                                 # arayüz (http://localhost:3000)
```

## Proje yapısı

```
agent.py              LiveKit Agents giriş noktası
voice_agent/
  config.py            .env okuma
  models.py             STT/LLM/TTS tanımları
  recording.py           egress + backend senkronizasyonu
  tools.py                function_tool'lar (matematik, web araması)
system_prompt.txt      asistanın talimatları (panelden düzenlenebilir)

backend/
  app.py                FastAPI route'ları ve hata yönetimi
  config.py              .env okuma
  db.py                    Supabase (DB + Storage) erişimi

frontend/
  src/app/                sayfalar (sistem promptu, konuşmalar, yeni konuşma)
  src/components/          paylaşılan bileşenler (Nav, VoiceCall, ErrorPanel, ...)
  src/lib/                  API istemcisi, tipler, useAsync hook'u
```
