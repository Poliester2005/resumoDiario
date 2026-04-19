#!/usr/bin/env python3
"""
Daily Briefing Generator — 100% gratuito
Groq (Llama 3.3 70B) + Edge TTS + GitHub Pages
"""

import os, re, json, requests, feedparser
from datetime import datetime
from pathlib import Path

PODCAST_TITLE       = "Meu Briefing Diário"
PODCAST_DESCRIPTION = "Resumo personalizado de tech e notícias do mundo, gerado com IA."
PODCAST_AUTHOR      = "Automatizado com Groq + Llama"

NEWS_SOURCES = {
    "tech": [
        ("Hacker News", "https://hnrss.org/frontpage?count=15"),
        ("TechCrunch",  "https://techcrunch.com/feed/"),
        ("The Verge",   "https://www.theverge.com/rss/index.xml"),
    ],
    "mundo": [
        ("BBC Brasil",  "https://www.bbc.com/portuguese/topicos/brasil/index.xml"),
        ("G1 Brasil",   "https://g1.globo.com/rss/g1/"),
        ("BBC World",   "http://feeds.bbci.co.uk/news/world/rss.xml"),
    ],
}

MAX_ARTICLES_PER_SOURCE = 6
MAX_EPISODES_IN_FEED    = 30

GROQ_API_KEY = os.environ["GROQ_API_KEY"]
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
REPO         = os.environ.get("REPO", "")

GROQ_URL   = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"
WEEKDAYS   = ["segunda-feira","terça-feira","quarta-feira","quinta-feira","sexta-feira","sábado","domingo"]


def strip_html(text):
    return re.sub(r"<[^>]+>", "", text or "").strip()


def fetch_articles():
    articles = []
    for category, sources in NEWS_SOURCES.items():
        for name, url in sources:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries[:MAX_ARTICLES_PER_SOURCE]:
                    summary = strip_html(entry.get("summary") or entry.get("description") or "")[:400]
                    articles.append({"title": entry.get("title","").strip(), "summary": summary,
                                     "category": category, "source": name})
            except Exception as e:
                print(f"  ⚠️  {name}: {e}")
    return articles


def summarize_with_groq(articles):
    today    = WEEKDAYS[datetime.now().weekday()]
    date_fmt = datetime.now().strftime("%d/%m/%Y")
    body     = "\n\n".join(
        f"[{a['category'].upper()} | {a['source']}]\nTítulo: {a['title']}\n{a['summary']}"
        for a in articles
    )
    prompt = (
        f"Você é um apresentador de podcast brasileiro descontraído e inteligente.\n"
        f"Hoje é {today}, {date_fmt}.\n\n"
        "Crie um briefing em áudio de 4-5 minutos.\n"
        "REGRAS: escreva em português do Brasil natural; saudação animada com o dia; "
        "bloco Tech (4-5 notícias) depois Mundo (3-4 notícias); "
        "transições naturais; frase motivadora no final; "
        "APENAS texto corrido sem markdown, listas ou símbolos.\n\n"
        f"Notícias:\n{body}"
    )
    r = requests.post(GROQ_URL,
        headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
        json={"model": GROQ_MODEL, "max_tokens": 2000,
              "messages": [{"role": "user", "content": prompt}], "temperature": 0.7},
        timeout=60)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


# Voz disponíveis em pt-BR (escolha a sua favorita):
#   pt-BR-FranciscaNeural  — feminina, natural e calorosa     ← padrão
#   pt-BR-AntonioNeural    — masculina, séria e clara
#   pt-BR-ThalitaNeural    — feminina, jovem e descontraída
TTS_VOICE = "pt-BR-FranciscaNeural"

def text_to_speech(text, output_path):
    import asyncio
    import edge_tts

    async def _synthesize():
        communicate = edge_tts.Communicate(text, TTS_VOICE)
        await communicate.save(str(output_path))

    asyncio.run(_synthesize())


def create_github_release(date_str, audio_path):
    h = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    r = requests.post(f"https://api.github.com/repos/{REPO}/releases", headers=h,
        json={"tag_name": f"ep-{date_str}", "name": f"Episodio {date_str}",
              "body": f"Briefing {date_str}", "draft": False, "prerelease": False})
    r.raise_for_status()
    upload_url = r.json()["upload_url"].replace("{?name,label}", "")
    with open(audio_path, "rb") as f:
        data = f.read()
    r = requests.post(f"{upload_url}?name={audio_path.name}",
        headers={**h, "Content-Type": "audio/mpeg"}, data=data)
    r.raise_for_status()
    return r.json()["browser_download_url"]


def update_rss_feed(date_str, audio_url, script, audio_path):
    docs = Path("docs")
    docs.mkdir(exist_ok=True)
    eps_file = docs / "episodes.json"
    episodes = json.loads(eps_file.read_text()) if eps_file.exists() else []
    episodes.insert(0, {"date": date_str, "title": f"Briefing {date_str}",
        "description": script[:300].replace("\n"," ") + "…",
        "url": audio_url, "size": audio_path.stat().st_size, "duration": "00:05:00"})
    episodes = episodes[:MAX_EPISODES_IN_FEED]
    eps_file.write_text(json.dumps(episodes, ensure_ascii=False, indent=2))

    user, repo_name = REPO.split("/")
    pages_url = f"https://{user}.github.io/{repo_name}"
    items = "\n".join(
        f'    <item>\n      <title><![CDATA[{e["title"]}]]></title>\n'
        f'      <description><![CDATA[{e["description"]}]]></description>\n'
        f'      <enclosure url="{e["url"]}" length="{e["size"]}" type="audio/mpeg"/>\n'
        f'      <guid isPermaLink="false">{e["url"]}</guid>\n'
        f'      <pubDate>{e["date"]}</pubDate>\n'
        f'      <itunes:duration>{e["duration"]}</itunes:duration>\n    </item>'
        for e in episodes)
    rss = (f'<?xml version="1.0" encoding="UTF-8"?>\n'
           f'<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">\n'
           f'  <channel>\n    <title>{PODCAST_TITLE}</title>\n'
           f'    <description>{PODCAST_DESCRIPTION}</description>\n'
           f'    <link>{pages_url}</link>\n    <language>pt-BR</language>\n'
           f'    <itunes:author>{PODCAST_AUTHOR}</itunes:author>\n'
           f'    <itunes:category text="Technology"/>\n    <itunes:explicit>false</itunes:explicit>\n'
           f'{items}\n  </channel>\n</rss>')
    (docs / "feed.xml").write_text(rss, encoding="utf-8")
    print(f"   → Feed atualizado com {len(episodes)} episódio(s)")


def main():
    date_str   = datetime.now().strftime("%Y-%m-%d")
    audio_path = Path(f"episode-{date_str}.mp3")

    print("📰 Buscando notícias...")
    articles = fetch_articles()
    print(f"   → {len(articles)} artigos")

    print("🦙 Gerando roteiro com Groq (Llama 3.3 70B — gratuito)...")
    script = summarize_with_groq(articles)
    print(f"   → {len(script)} caracteres")

    print("🎙️  Convertendo para áudio com Edge TTS (Microsoft Neural)...")
    text_to_speech(script, audio_path)
    print(f"   → {audio_path.name} ({audio_path.stat().st_size/1024:.0f} KB)")

    if GITHUB_TOKEN and REPO:
        print("📤 Fazendo upload para GitHub Releases...")
        audio_url = create_github_release(date_str, audio_path)
        print(f"   → {audio_url}")
        print("📡 Atualizando feed RSS...")
        update_rss_feed(date_str, audio_url, script, audio_path)
    else:
        print("⚠️  GITHUB_TOKEN/REPO não definidos — pulando publicação")

    print("✅ Pronto!")

if __name__ == "__main__":
    main()
