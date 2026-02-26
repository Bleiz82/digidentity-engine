#!/usr/bin/env python3
import re, time, logging, requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)
REQUEST_TIMEOUT = 15
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

AI_CRAWLERS = {
    "GPTBot":           {"owner": "OpenAI / ChatGPT",        "impact": "critico"},
    "ChatGPT-User":     {"owner": "OpenAI / ChatGPT",        "impact": "critico"},
    "OAI-SearchBot":    {"owner": "OpenAI Search",           "impact": "critico"},
    "Google-Extended":  {"owner": "Google AI / Gemini",      "impact": "critico"},
    "Googlebot":        {"owner": "Google",                  "impact": "critico"},
    "PerplexityBot":    {"owner": "Perplexity AI",           "impact": "alto"},
    "anthropic-ai":     {"owner": "Anthropic / Claude",      "impact": "alto"},
    "ClaudeBot":        {"owner": "Anthropic / Claude",      "impact": "alto"},
    "Bingbot":          {"owner": "Microsoft / Bing Copilot","impact": "alto"},
    "msnbot":           {"owner": "Microsoft",               "impact": "medio"},
    "Applebot":         {"owner": "Apple / Siri",            "impact": "medio"},
    "Applebot-Extended":{"owner": "Apple AI",                "impact": "medio"},
    "YouBot":           {"owner": "You.com",                 "impact": "medio"},
    "cohere-ai":        {"owner": "Cohere",                  "impact": "basso"},
    "Diffbot":          {"owner": "Diffbot",                 "impact": "basso"},
}

DEFINITION_PATTERNS_IT = [
    r"\b\w[\w\s]{2,30}\s+è\s+(?:un|una|il|la|lo|gli|le|dei|delle|degli)\b",
    r"\b\w[\w\s]{2,30}\s+si\s+riferisce?\s+a\b",
    r"\b\w[\w\s]{2,30}\s+significa?\b",
    r"\bin\s+(?:parole|termini)\s+(?:semplici|altri|pratici)\s*[,:]",
    r"\becco\s+(?:come|perché|cosa|quando)\b",
]

AUTHORITY_PATTERNS_IT = [
    r"(?:secondo|per|stando\s+a)\s+[A-Z]",
    r"(?:la\s+ricerca|lo\s+studio|i\s+dati|l\x27analisi)\s+(?:mostra|indica|suggerisce|evidenzia)",
    r"(?:Politecnico|Università|ISTAT|Confcommercio|CGIA|Osservatorio|Unioncamere)",
    r"\b\d{1,3}(?:[.,]\d+)?%\s+(?:dei|delle|degli|di)\b",
    r"\b(?:nel|nel\s+corso\s+del)\s+20[0-9]{2}\b",
]

DIRECT_ANSWER_PATTERNS_IT = [
    r"^(?:sì|no|certamente|assolutamente|mai|sempre|dipende)[,\s:.]",
    r"^(?:per|in)\s+(?:breve|sintesi|riassunto|conclusione)[,:]",
    r"^\d+\.\s+",
    r"^[-•]\s+",
]

LIST_PATTERNS_IT = [
    r"(?:ecco|questi\s+sono|di\s+seguito)[:\s]+",
    r"\d+\s+(?:modi|consigli|passi|step|motivi|vantaggi|errori|esempi)",
    r"(?:primo|secondo|terzo|quarto|quinto)[,:]",
    r"(?:in\s+primo\s+luogo|in\s+secondo\s+luogo|infine|inoltre)",
]


def analyze_robots_txt(base_url):
    result = {
        "found": False, "url": "", "content": "",
        "crawlers": {}, "critical_blocked": [], "all_blocked": [],
        "sitemap_declared": False, "sitemap_url": "",
        "score": 0, "summary": "",
    }
    robots_url = urljoin(base_url, "/robots.txt")
    result["url"] = robots_url
    try:
        resp = requests.get(robots_url, headers=HEADERS, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        if resp.status_code != 200:
            result["summary"] = f"robots.txt non trovato (HTTP {resp.status_code})"
            result["score"] = 70
            return result
        result["found"] = True
        content = resp.text
        result["content"] = content[:3000]
        for line in content.splitlines():
            if line.strip().lower().startswith("sitemap:"):
                result["sitemap_declared"] = True
                result["sitemap_url"] = line.split(":", 1)[1].strip()
                break
        current_agents = []
        rules = {}
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or ":" not in line:
                continue
            key, _, value = line.partition(":")
            key = key.strip().lower()
            value = value.strip()
            if key == "user-agent":
                current_agents = [value]
                for agent in current_agents:
                    if agent not in rules:
                        rules[agent] = {"disallow": [], "allow": []}
            elif key == "disallow" and current_agents:
                for agent in current_agents:
                    if agent not in rules:
                        rules[agent] = {"disallow": [], "allow": []}
                    rules[agent]["disallow"].append(value)
            elif key == "allow" and current_agents:
                for agent in current_agents:
                    if agent not in rules:
                        rules[agent] = {"disallow": [], "allow": []}
                    rules[agent]["allow"].append(value)
        for crawler_name, crawler_info in AI_CRAWLERS.items():
            matched_key = next((k for k in rules if k.lower() == crawler_name.lower()), None)
            wildcard = rules.get("*", {"disallow": [], "allow": []})
            agent_rules = rules[matched_key] if matched_key else wildcard
            disallowed = agent_rules.get("disallow", [])
            allowed = agent_rules.get("allow", [])
            is_blocked = ("/" in disallowed or "*" in disallowed) and "/" not in allowed
            is_allowed = "/" in allowed or "*" in allowed
            status = "bloccato" if is_blocked else ("consentito" if (is_allowed or matched_key) else "non_menzionato")
            result["crawlers"][crawler_name] = {
                "owner": crawler_info["owner"], "impact": crawler_info["impact"],
                "status": status, "is_blocked": is_blocked, "is_explicitly_allowed": is_allowed,
            }
            if is_blocked:
                result["all_blocked"].append(crawler_name)
                if crawler_info["impact"] == "critico":
                    result["critical_blocked"].append(crawler_name)
        bc = len(result["critical_blocked"])
        bt = len(result["all_blocked"])
        result["score"] = max(0, 40 - bc*15) if bc > 0 else (55 if bt > 3 else (70 if bt > 0 else (100 if result["sitemap_declared"] else 85)))
        if result["critical_blocked"]:
            result["summary"] = f"CRITICO: {bc} crawler AI critici bloccati ({', '.join(result['critical_blocked'])})."
        elif result["all_blocked"]:
            result["summary"] = f"ATTENZIONE: {bt} crawler AI bloccati: {', '.join(result['all_blocked'])}."
        else:
            result["summary"] = "OK: Nessun crawler AI bloccato."
        logger.info(f"[GEO] robots.txt: {bc} critici bloccati, score={result['score']}")
    except Exception as e:
        result["summary"] = f"Errore robots.txt: {e}"
        result["score"] = 50
        logger.warning(f"[GEO] Errore robots.txt: {e}")
    return result


def analyze_llms_txt(base_url):
    result = {
        "found": False, "url": "", "content": "",
        "has_description": False, "has_sections": False,
        "has_links": False, "has_optional": False,
        "sections_found": [], "links_count": 0,
        "score": 0, "grade": "F", "summary": "", "template": "",
    }
    llms_url = urljoin(base_url, "/llms.txt")
    result["url"] = llms_url
    try:
        resp = requests.get(llms_url, headers=HEADERS, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        if resp.status_code == 200:
            result["found"] = True
            content = resp.text
            result["content"] = content[:5000]
            lines = content.splitlines()
            result["has_description"] = any(
                l.strip() and not l.startswith("#") and not l.startswith(">")
                and not l.startswith("-") and len(l) > 30 for l in lines[:10]
            )
            result["has_sections"] = sum(1 for l in lines if l.startswith("## ")) >= 1
            result["has_links"] = "http" in content
            result["has_optional"] = "## Optional" in content or "## Opzionale" in content
            result["links_count"] = len(re.findall(r"https?://\S+", content))
            result["sections_found"] = [l[3:].strip() for l in lines if l.startswith("## ")]
            score = 40
            if result["has_description"]: score += 20
            if result["has_sections"]:    score += 20
            if result["has_links"]:       score += 15
            if result["has_optional"]:    score += 5
            result["score"] = min(100, score)
            result["grade"] = next((g for s, g in [(90,"A"),(75,"B"),(60,"C"),(40,"D")] if result["score"] >= s), "F")
            result["summary"] = f"llms.txt trovato — Score: {result['score']}/100 (Grade {result['grade']}). Sezioni: {len(result['sections_found'])}."
        else:
            result["summary"] = f"llms.txt non trovato (HTTP {resp.status_code})."
    except Exception as e:
        result["summary"] = f"llms.txt non raggiungibile: {e}"
        logger.warning(f"[GEO] Errore llms.txt: {e}")
    domain = urlparse(base_url).netloc
    result["template"] = (
        "# [Nome Attivita]\n\n"
        "> [Descrizione: cosa fai, dove sei, per chi.]\n\n"
        "## Servizi\n"
        f"- [Servizio 1]: {base_url}/servizi\n"
        f"- [Servizio 2]: {base_url}/servizi\n\n"
        "## Informazioni\n"
        f"- Chi siamo: {base_url}/chi-siamo\n"
        f"- Contatti: {base_url}/contatti\n\n"
        "## Optional\n"
        f"- Blog: {base_url}/blog\n"
        f"- FAQ: {base_url}/faq\n"
    )
    return result


def analyze_citability(url, html_content=None):
    result = {
        "score": 0, "grade": "F", "passages_analyzed": 0,
        "high_quality_passages": 0, "avg_word_count": 0,
        "optimal_passages": [], "issues": [], "strengths": [],
        "definition_score": 0, "authority_score": 0,
        "structure_score": 0, "readability_score": 0, "summary": "",
    }
    try:
        if not html_content:
            resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT, allow_redirects=True)
            html_content = resp.text
        soup = BeautifulSoup(html_content, "lxml")
        for tag in soup(["script","style","nav","header","footer","iframe","aside"]):
            tag.decompose()
        text_blocks = [
            tag.get_text(separator=" ", strip=True)
            for tag in soup.find_all(["p","h1","h2","h3","li","blockquote","section"])
            if len(tag.get_text(separator=" ", strip=True).split()) >= 10
        ]
        if not text_blocks:
            result["summary"] = "Nessun blocco di testo significativo trovato"
            return result
        result["passages_analyzed"] = len(text_blocks)
        def_hits = auth_hits = dir_hits = list_hits = hq = 0
        word_counts = []
        for block in text_blocks:
            wc = len(block.split())
            word_counts.append(wc)
            bs = 0
            for p in DEFINITION_PATTERNS_IT:
                if re.search(p, block, re.IGNORECASE): def_hits += 1; bs += 25; break
            for p in AUTHORITY_PATTERNS_IT:
                if re.search(p, block, re.IGNORECASE): auth_hits += 1; bs += 20; break
            for p in DIRECT_ANSWER_PATTERNS_IT:
                if re.search(p, block, re.IGNORECASE | re.MULTILINE): dir_hits += 1; bs += 20; break
            for p in LIST_PATTERNS_IT:
                if re.search(p, block, re.IGNORECASE): list_hits += 1; bs += 15; break
            if 134 <= wc <= 167:
                bs += 20
                result["optimal_passages"].append(block[:200] + "...")
            if wc < 30: bs -= 10
            elif wc > 500: bs -= 5
            if bs >= 40: hq += 1
        result["high_quality_passages"] = hq
        result["avg_word_count"] = round(sum(word_counts)/len(word_counts)) if word_counts else 0
        n = max(len(text_blocks), 1)
        result["definition_score"]  = min(100, round((def_hits/n)*300))
        result["authority_score"]   = min(100, round((auth_hits/n)*400))
        result["structure_score"]   = min(100, round((list_hits/n)*300))
        result["readability_score"] = min(100, round((dir_hits/n)*300))
        result["score"] = round(
            result["definition_score"]*0.30 + result["authority_score"]*0.25 +
            result["structure_score"]*0.25  + result["readability_score"]*0.20
        )
        result["grade"] = next((g for s,g in [(80,"A"),(65,"B"),(50,"C"),(35,"D")] if result["score"] >= s), "F")
        if result["definition_score"] >= 60:
            result["strengths"].append("Definizioni chiare — ottimo per risposte AI")
        else:
            result["issues"].append("Mancano definizioni esplicite (es. X e...)")
        if result["authority_score"] >= 50:
            result["strengths"].append("Presenza dati/statistiche/fonti autorevoli")
        else:
            result["issues"].append("Nessun dato numerico o fonte citata")
        if result["avg_word_count"] < 80:
            result["issues"].append("Testi troppo brevi — AI fatica a citarli")
        elif result["avg_word_count"] > 400:
            result["issues"].append("Testi troppo lunghi — spezza in paragrafi da 130-170 parole")
        else:
            result["strengths"].append(f"Lunghezza media ottimale: {result['avg_word_count']} parole")
        result["summary"] = f"Score citabilita: {result['score']}/100 (Grade {result['grade']}). {len(text_blocks)} blocchi, {hq} alta qualita."
        logger.info(f"[GEO] Citabilita: score={result['score']}, grade={result['grade']}")
    except Exception as e:
        result["summary"] = f"Errore citabilita: {e}"
        logger.warning(f"[GEO] Errore citabilita: {e}")
    return result


def analyze_schema_markup(url, html_content=None):
    result = {
        "found": False, "types_found": [],
        "has_local_business": False, "has_organization": False,
        "has_faq": False, "has_review": False,
        "has_breadcrumb": False, "has_website": False, "has_person": False,
        "missing_critical": [], "score": 0, "raw_schemas": [], "summary": "",
    }
    try:
        if not html_content:
            resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT, allow_redirects=True)
            html_content = resp.text
        soup = BeautifulSoup(html_content, "lxml")
        json_ld_tags = soup.find_all("script", type="application/ld+json")
        if not json_ld_tags:
            result["missing_critical"] = ["LocalBusiness","FAQPage","BreadcrumbList"]
            result["summary"] = "Nessun schema markup trovato."
            return result
        import json as jl
        result["found"] = True
        for tag in json_ld_tags:
            try:
                schema = jl.loads(tag.string or "{}")
                schemas = schema if isinstance(schema, list) else schema.get("@graph", [schema]) if isinstance(schema, dict) else [schema]
                for s in schemas:
                    st = s.get("@type", "")
                    if isinstance(st, list): st = st[0]
                    if not st: continue
                    result["types_found"].append(st)
                    result["raw_schemas"].append({"type": st, "fields": list(s.keys())[:15]})
                    stl = st.lower()
                    if any(t in stl for t in ["localbusiness","restaurant","store","professionalservice","dentist","lawyer","accountant"]):
                        result["has_local_business"] = True
                    elif "organization" in stl: result["has_organization"] = True
                    if "faqpage" in stl or "faq" in stl: result["has_faq"] = True
                    if "review" in stl or "aggregaterating" in stl: result["has_review"] = True
                    if "breadcrumb" in stl: result["has_breadcrumb"] = True
                    if "website" in stl: result["has_website"] = True
                    if "person" in stl: result["has_person"] = True
            except Exception:
                continue
        score = 20
        if result["has_local_business"]: score += 35
        if result["has_organization"]:   score += 15
        if result["has_faq"]:            score += 20
        if result["has_review"]:         score += 10
        if result["has_breadcrumb"]:     score += 10
        if result["has_website"]:        score += 10
        result["score"] = min(100, score)
        if not result["has_local_business"] and not result["has_organization"]:
            result["missing_critical"].append("LocalBusiness / Organization")
        if not result["has_faq"]:    result["missing_critical"].append("FAQPage")
        if not result["has_review"]: result["missing_critical"].append("AggregateRating")
        result["summary"] = (
            f"Schema trovati: {', '.join(result['types_found'][:5]) or 'nessuno'}. "
            f"Score: {result['score']}/100. "
            f"Mancanti: {', '.join(result['missing_critical']) or 'nessuno'}."
        )
        logger.info(f"[GEO] Schema: types={result['types_found']}, score={result['score']}")
    except Exception as e:
        result["summary"] = f"Errore schema: {e}"
        logger.warning(f"[GEO] Errore schema: {e}")
    return result


def calculate_platform_scores(robots_r, citability_r, schema_r, llms_r):
    crawlers = robots_r.get("crawlers", {})
    def ok(name): return not crawlers.get(name, {}).get("is_blocked", False)
    cit = citability_r.get("score", 50)
    sch = schema_r.get("score", 50)
    llm = llms_r.get("score", 0)
    return {k: min(100, v) for k, v in {
        "Google AI Overviews": round((int(ok("Googlebot"))*30)+(int(ok("Google-Extended"))*20)+(cit*0.25)+(sch*0.25)),
        "ChatGPT / OpenAI":    round((int(ok("GPTBot") and ok("ChatGPT-User"))*40)+(cit*0.30)+(llm*0.15)+(sch*0.15)),
        "Perplexity AI":       round((int(ok("PerplexityBot"))*35)+(cit*0.35)+(llm*0.15)+(sch*0.15)),
        "Gemini":              round((int(ok("Googlebot"))*25)+(int(ok("Google-Extended"))*25)+(cit*0.25)+(sch*0.25)),
        "Bing Copilot":        round((int(ok("Bingbot"))*40)+(cit*0.30)+(sch*0.20)+(llm*0.10)),
    }.items()}


def calculate_geo_score(citability, robots, llms, schema, platform_avg):
    score = min(100, max(0, round(citability*0.30 + robots*0.25 + schema*0.20 + platform_avg*0.15 + llms*0.10)))
    levels = [
        (80,"Eccellente","verde","Alta probabilita di essere citato dai motori AI."),
        (65,"Buono","verde","Buona visibilita AI con margini di miglioramento."),
        (45,"Discreto","giallo","Visibilita AI parziale. Interventi consigliati."),
        (25,"Insufficiente","arancio","Il sito fatica ad essere citato dai motori AI."),
        (0, "Critico","rosso","Il sito e praticamente invisibile ai motori AI."),
    ]
    lv, co, de = next((lv,co,de) for th,lv,co,de in levels if score >= th)
    return {
        "score": score, "level": lv, "color": co, "description": de,
        "components": {"citabilita": citability, "crawler_access": robots, "schema_markup": schema, "platform_readiness": platform_avg, "llms_txt": llms},
    }


def _generate_quick_wins(geo_data):
    wins = []
    if not geo_data["llms"].get("found"):
        wins.append({"titolo": "Crea il file llms.txt", "descrizione": "Aggiungi /llms.txt alla root con descrizione, servizi e link principali.", "impatto": "Alto", "sforzo": "30 min", "piattaforme": ["ChatGPT","Perplexity","Claude"], "template": geo_data["llms"].get("template","")})
    cb = geo_data["robots"].get("critical_blocked", [])
    if cb:
        wins.append({"titolo": "Sblocca i crawler AI nel robots.txt", "descrizione": f"Rimuovi Disallow per: {', '.join(cb)}.", "impatto": "Critico", "sforzo": "15 min", "piattaforme": cb})
    if not geo_data["schema"].get("found"):
        wins.append({"titolo": "Aggiungi schema LocalBusiness", "descrizione": "Inserisci JSON-LD LocalBusiness nella homepage con nome, indirizzo, telefono, orari.", "impatto": "Alto", "sforzo": "2 ore", "piattaforme": ["Google AI Overviews","Google Maps","ChatGPT"]})
    elif "FAQPage" in geo_data["schema"].get("missing_critical", []):
        wins.append({"titolo": "Aggiungi schema FAQPage", "descrizione": "Crea sezione FAQ con schema FAQPage — formato piu citato dai modelli AI.", "impatto": "Alto", "sforzo": "3 ore", "piattaforme": ["Google AI Overviews","ChatGPT","Perplexity"]})
    if geo_data["citability"].get("score", 0) < 40:
        wins.append({"titolo": "Ottimizza i testi per la citabilita AI", "descrizione": "Riscrivi i paragrafi con definizioni esplicite e dati numerici. Range ottimale: 130-170 parole/blocco.", "impatto": "Alto", "sforzo": "4 ore", "piattaforme": ["ChatGPT","Perplexity","Gemini"]})
    if geo_data["robots"].get("found") and not geo_data["robots"].get("sitemap_declared"):
        wins.append({"titolo": "Dichiara la sitemap nel robots.txt", "descrizione": "Aggiungi: Sitemap: https://tuodominio.it/sitemap.xml", "impatto": "Medio", "sforzo": "10 min", "piattaforme": ["Google","Bing","tutti i crawler AI"]})
    return wins[:5]


def _generate_critical_issues(geo_data):
    issues = []
    score = geo_data["geo_score"].get("score", 0)
    if score < 30:
        issues.append({"titolo": f"GEO Score critico: {score}/100", "descrizione": "L attivita e praticamente invisibile ai motori AI.", "urgenza": "critica"})
    if geo_data["robots"].get("critical_blocked"):
        issues.append({"titolo": f"Crawler AI bloccati: {', '.join(geo_data['robots']['critical_blocked'])}", "descrizione": "Il robots.txt impedisce ai principali motori AI di leggere il sito.", "urgenza": "critica"})
    if not geo_data["schema"].get("found"):
        issues.append({"titolo": "Schema markup assente", "descrizione": "I motori AI non riescono a identificare settore, posizione e contatti.", "urgenza": "alta"})
    if not geo_data["llms"].get("found"):
        issues.append({"titolo": "llms.txt assente", "descrizione": "Solo il 4% dei siti italiani ha un llms.txt. Crearlo ora e un vantaggio competitivo.", "urgenza": "media"})
    return issues


def scrape_geo(website_url, company_name, html_content=None):
    result = {
        "analyzed": False, "website_url": website_url, "company_name": company_name,
        "geo_score": {}, "robots": {}, "llms": {}, "citability": {},
        "schema": {}, "platform_scores": {}, "quick_wins": [], "critical_issues": [],
        "summary": "", "error": None,
    }
    if not website_url:
        result["error"] = "URL non fornito"
        result["summary"] = "Nessun sito web — attivita non visibile ai motori AI tramite sito."
        result["geo_score"] = calculate_geo_score(0, 0, 0, 0, 0)
        return result
    logger.info(f"[GEO] Avvio analisi per: {website_url}")
    start = time.time()
    try:
        result["robots"]     = analyze_robots_txt(website_url);     time.sleep(0.3)
        result["llms"]       = analyze_llms_txt(website_url);       time.sleep(0.3)
        result["citability"] = analyze_citability(website_url, html_content); time.sleep(0.3)
        result["schema"]     = analyze_schema_markup(website_url, html_content)
        result["platform_scores"] = calculate_platform_scores(result["robots"], result["citability"], result["schema"], result["llms"])
        platform_avg = round(sum(result["platform_scores"].values()) / len(result["platform_scores"])) if result["platform_scores"] else 0
        result["geo_score"] = calculate_geo_score(
            citability=result["citability"].get("score", 0),
            robots=result["robots"].get("score", 0),
            llms=result["llms"].get("score", 0),
            schema=result["schema"].get("score", 0),
            platform_avg=platform_avg,
        )
        result["quick_wins"]      = _generate_quick_wins(result)
        result["critical_issues"] = _generate_critical_issues(result)
        result["analyzed"] = True
        elapsed = round(time.time() - start, 1)
        result["summary"] = (
            f"GEO Score: {result['geo_score']['score']}/100 ({result['geo_score']['level']}). "
            f"Crawler bloccati: {len(result['robots'].get('critical_blocked', []))}. "
            f"llms.txt: {'trovato' if result['llms']['found'] else 'assente'}. "
            f"Schema: {'trovato' if result['schema']['found'] else 'assente'}. "
            f"Completato in {elapsed}s."
        )
        logger.info(f"[GEO] Score finale: {result['geo_score']['score']}/100 in {elapsed}s")
    except Exception as e:
        result["error"] = str(e)
        result["summary"] = f"Errore analisi GEO: {e}"
        logger.error(f"[GEO] Errore: {e}", exc_info=True)
    return result
