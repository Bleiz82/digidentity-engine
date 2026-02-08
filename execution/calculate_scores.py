"""
DigIdentity Engine - Score Calculator
Calcola score 0-100 per ogni area di analisi + score totale.
"""

from typing import Dict, Any, Optional


def calculate_scores(
    pagespeed_data: Optional[Dict[str, Any]],
    serp_data: Optional[Dict[str, Any]],
    gmb_data: Optional[Dict[str, Any]],
    social_data: Optional[Dict[str, Any]],
    competitors_data: Optional[Dict[str, Any]]
) -> Dict[str, int]:
    print(f"Score calculation...")

    # Normalizza None in dict vuoti
    pagespeed_data = pagespeed_data or {}
    serp_data = serp_data or {}
    gmb_data = gmb_data or {}
    social_data = social_data or {}
    competitors_data = competitors_data or {}

    scores = {
        "score_sito_web": calculate_website_score(pagespeed_data),
        "score_seo": calculate_seo_score(serp_data, pagespeed_data),
        "score_gmb": calculate_gmb_score(gmb_data),
        "score_social": calculate_social_score(social_data),
        "score_competitivo": calculate_competitive_score(competitors_data, gmb_data)
    }

    weights = {
        "score_sito_web": 0.25,
        "score_seo": 0.25,
        "score_gmb": 0.20,
        "score_social": 0.15,
        "score_competitivo": 0.15
    }

    scores["score_totale"] = int(sum(
        scores[key] * weights[key] for key in weights.keys()
    ))

    print(f"Score calcolati:")
    for key, value in scores.items():
        print(f"   {key}: {value}/100")

    return scores


def calculate_website_score(pagespeed_data: Dict[str, Any]) -> int:
    if not pagespeed_data or not pagespeed_data.get("success"):
        return 0

    desktop = pagespeed_data.get("desktop", {}) or {}
    mobile = pagespeed_data.get("mobile", {}) or {}

    desktop_avg = (
        desktop.get("performance", 0) +
        desktop.get("accessibility", 0) +
        desktop.get("best_practices", 0) +
        desktop.get("seo", 0)
    ) / 4

    mobile_avg = (
        mobile.get("performance", 0) +
        mobile.get("accessibility", 0) +
        mobile.get("best_practices", 0) +
        mobile.get("seo", 0)
    ) / 4

    final_score = int(mobile_avg * 0.6 + desktop_avg * 0.4)
    return max(0, min(100, final_score))


def calculate_seo_score(serp_data: Dict[str, Any], pagespeed_data: Dict[str, Any]) -> int:
    if not serp_data or not serp_data.get("success"):
        return 0

    pagespeed_data = pagespeed_data or {}
    score = 0

    brand_query = serp_data.get("brand_query", {}) or {}
    if brand_query.get("found"):
        position = brand_query.get("position", 11)
        if position == 1:
            score += 40
        elif position <= 3:
            score += 30
        elif position <= 5:
            score += 20
        elif position <= 10:
            score += 10

    sector_query = serp_data.get("sector_query", {}) or {}
    if sector_query.get("found"):
        position = sector_query.get("position", 11)
        if position <= 3:
            score += 30
        elif position <= 5:
            score += 20
        elif position <= 10:
            score += 10

    if pagespeed_data.get("success"):
        mobile = pagespeed_data.get("mobile", {}) or {}
        desktop = pagespeed_data.get("desktop", {}) or {}
        mobile_seo = mobile.get("seo", 0)
        desktop_seo = desktop.get("seo", 0)
        avg_seo = (mobile_seo + desktop_seo) / 2
        score += int(avg_seo * 0.3)

    return max(0, min(100, score))


def calculate_gmb_score(gmb_data: Dict[str, Any]) -> int:
    if not gmb_data or not gmb_data.get("found"):
        return 0

    data = gmb_data.get("data", {}) or {}
    score = 0

    score += 20

    completeness = data.get("completeness", 0) or 0
    score += int(completeness * 0.3)

    rating = data.get("rating", 0) or 0
    if rating >= 4.5:
        score += 25
    elif rating >= 4.0:
        score += 20
    elif rating >= 3.5:
        score += 15
    elif rating >= 3.0:
        score += 10
    elif rating > 0:
        score += 5

    reviews = data.get("reviews_count", 0) or 0
    if reviews >= 100:
        score += 25
    elif reviews >= 50:
        score += 20
    elif reviews >= 20:
        score += 15
    elif reviews >= 10:
        score += 10
    elif reviews >= 5:
        score += 5

    return max(0, min(100, score))


def calculate_social_score(social_data: Dict[str, Any]) -> int:
    if not social_data or not social_data.get("success"):
        return 0

    platforms_declared = social_data.get("platforms_declared", []) or []
    analysis = social_data.get("analysis", {}) or {}

    if not platforms_declared:
        return 0

    score = 0

    num_platforms = min(len(platforms_declared), 4)
    score += num_platforms * 10

    verified_count = sum(1 for p in analysis.values() if isinstance(p, dict) and p.get("verified"))
    if verified_count > 0:
        verification_rate = verified_count / len(platforms_declared)
        score += int(verification_rate * 60)

    return max(0, min(100, score))


def calculate_competitive_score(
    competitors_data: Dict[str, Any],
    gmb_data: Dict[str, Any]
) -> int:
    if not competitors_data or not gmb_data:
        return 50

    if not competitors_data.get("success") or not gmb_data.get("found"):
        return 50

    position = competitors_data.get("competitive_position", "average")

    position_scores = {
        "leader": 90,
        "strong": 75,
        "average": 50,
        "weak": 30,
        "new": 10
    }

    base_score = position_scores.get(position, 50)

    benchmarks = competitors_data.get("benchmarks", {}) or {}
    rating_gap = benchmarks.get("rating_gap")
    reviews_gap = benchmarks.get("reviews_gap")

    if rating_gap is not None:
        base_score += int(rating_gap * 10)

    if reviews_gap is not None:
        avg_reviews = benchmarks.get("avg_competitor_reviews", 1) or 1
        if avg_reviews > 0:
            reviews_ratio = reviews_gap / avg_reviews
            base_score += int(reviews_ratio * 5)

    return max(0, min(100, base_score))
