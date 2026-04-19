# 📻 Daily Briefing — Podcast Pessoal Automático

Gera um episódio de ~5 minutos todo dia com notícias de **tech** e do **mundo**,
narrado em português pelo Claude, e publica como podcast RSS que abre direto no
Pocket Casts ou qualquer app de podcast.

## Como funciona

```
Fontes RSS (HN, TechCrunch, BBC, G1)
        ↓
   Claude API (roteiro em PT-BR)
        ↓
   gTTS (texto → MP3)
        ↓
   GitHub Releases (host do áudio)
        ↓
   GitHub Pages (feed.xml público)
        ↓
   Pocket Casts / Overcast 🎧
```

## Setup (10 minutos)

### 1. Fork / clone este repositório

```bash
git clone https://github.com/SEU_USUARIO/daily-briefing.git
cd daily-briefing
```

### 2. Ative o GitHub Pages

- Vá em **Settings → Pages**
- Source: `Deploy from a branch`
- Branch: `main`, pasta: `/docs`
- Salve — em alguns minutos o feed estará em:
  `https://SEU_USUARIO.github.io/daily-briefing/feed.xml`

### 3. Adicione o secret da API

- Vá em **Settings → Secrets and variables → Actions → New repository secret**
- Nome: `GROQ_API_KEY`
- Valor: sua chave da API da Anthropic (https://console.anthropic.com)

### 4. Rode manualmente pela primeira vez

- Vá em **Actions → 📻 Daily Briefing → Run workflow**
- Aguarde ~2 minutos — o primeiro episódio será gerado!

### 5. Assine no app de podcast

**Pocket Casts:**
Descobrir → Busca → ícone de URL → cole a URL do feed

**Overcast:**
Add Podcast → Add URL → cole a URL do feed

**AntennaPod (Android):**
Adicionar podcast → URL do podcast → cole a URL

---

## Personalização

Edite `main.py` para ajustar:

```python
# Fontes de notícias
NEWS_SOURCES = {
    "tech": [
        ("Hacker News",  "https://hnrss.org/frontpage?count=15"),
        ("TechCrunch",   "https://techcrunch.com/feed/"),
        # Adicione mais aqui...
    ],
    "mundo": [
        ("BBC Brasil",   "https://www.bbc.com/portuguese/topicos/brasil/index.xml"),
        # Adicione mais aqui...
    ],
}
```

Edite `.github/workflows/daily.yml` para mudar o horário:

```yaml
# Horário atual: 06h30 BRT (09h30 UTC), segunda a sexta
- cron: "30 9 * * 1-5"
```

## Custo estimado

| Serviço | Custo |
|---|---|
| Groq API (Llama 3.3 70B) | Gratuito |
| gTTS (Google TTS) | Gratuito |
| GitHub Pages + Releases | Gratuito |
| **Total/mês (22 dias úteis)** | **R$ 0,00** |

## Dependências

```
groq (via requests) — Llama 3.3 70B
feedparser  — leitura de RSS
gtts        — text-to-speech gratuito
requests    — upload para GitHub API
```
