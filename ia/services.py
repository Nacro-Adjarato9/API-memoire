import json
import re
import unicodedata

import requests
from requests.exceptions import RequestException
from django.conf import settings
from django.core.cache import cache

from biens.models import Bien

ABIDJAN_ZONES = {
    "cocody riviera golf": ["Riviera Palmeraie", "Angré", "Bingerville"],
    "cocody": ["Angré", "Riviera Palmeraie", "Bingerville"],
    "marcory": ["Zone 4", "Biétry", "Treichville"],
    "plateau": ["Treichville", "Adjamé", "Koumassi"],
    "yopougon": ["Niangon", "Azito", "Gesco"],
    "abobo": ["Anyama", "N'dotré", "Adjamé"],
    "angre": ["Cocody", "Riviera Palmeraie", "Bingerville"],
    "bingerville": ["Cocody", "Riviera", "Angré"],
    "treichville": ["Marcory", "Plateau", "Koumassi"],
    "riviera": ["Cocody", "Angré", "Riviera Palmeraie"],
    "riviera palmeraie": ["Riviera", "Cocody", "Angré"],
}

SECONDARY_CITIES = {
    "bouake": {"price_range": (50000, 200000), "description": "2e ville de Côte d'Ivoire, prix abordables"},
    "yamoussoukro": {"price_range": (50000, 180000), "description": "Capitale politique, cadre calme"},
    "daloa": {"price_range": (40000, 150000), "description": "Zone agricole, très abordable"},
    "korhogo": {"price_range": (35000, 120000), "description": "Nord ivoirien, budget minimal"},
    "san pedro": {"price_range": (60000, 200000), "description": "Port, économie dynamique"},
    "man": {"price_range": (40000, 130000), "description": "Ouest ivoirien, cadre naturel"},
    "gagnoa": {"price_range": (40000, 140000), "description": "Centre-Ouest, prix abordables"},
    "abengourou": {"price_range": (45000, 160000), "description": "Est ivoirien, croissance urbaine"},
    "aboisso": {"price_range": (50000, 170000), "description": "Sud-Est, cadre tranquille"},
}

LOGI_SYSTEM_PROMPT = """Tu es LOGI, l'assistant immobilier intelligent de LogeCiv en Côte d'Ivoire.
Agis comme un agent humain, chaleureux et expert.
Langues : Français, Anglais, Dioula.
RÈGLES :
1. Utilise UNIQUEMENT les données du 'context'.
2. Ne jamais inventer de prix ou de biens.
3. Si aucun bien : propose des alternatives (fallback) avec pédagogie.
4. Suggère toujours de regarder la carte interactive.
5. Termine par une question."""

def filtrer_biens_intelligemment(params):
    """Version améliorée avec fallback progressif."""
    qs = build_bien_queryset(params)
    logements = [serialize_bien(b) for b in qs[:10]]
    
    if len(logements) > 0:
        return logements, False, 0 # Match parfait

    # Fallback 1: Élargir le budget de 20%
    if params.get("budget_max"):
        params_copy = params.copy()
        params_copy["budget_max"] = int(params["budget_max"]) * 1.2
        qs = build_bien_queryset(params_copy)
        logements = [serialize_bien(b) for b in qs[:10]]
        if len(logements) > 0:
            for l in logements: l["_fallback"] = "budget"
            return logements, True, 1

    # Fallback 2: Ville entière sans quartier
    params_copy = params.copy()
    params_copy["quartier"] = None
    params_copy["commune"] = None
    qs = build_bien_queryset(params_copy)
    logements = [serialize_bien(b) for b in qs[:10]]
    if len(logements) > 0:
        for l in logements: l["_fallback"] = "zone"
        return logements, True, 2

    return build_alternatives(params), True, 3


def normalize_text(value):
    if not value:
        return ""
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(char for char in text if not unicodedata.combining(char))
    return text.lower().strip()


def serialize_bien(bien):
    return {
        "id": bien.id,
        "titre": bien.titre,
        "prix": str(bien.prix),
        "ville": bien.ville,
        "localisation": bien.localisation,
        "type": bien.type,
        "transaction_type": bien.transaction_type,
        "statut": bien.statut,
        "meuble": bien.meuble,
        "piscine": bien.piscine,
        "securite": bien.securite,
        "proximite": bien.proximite,
        "nombre_chambres": bien.nombre_chambres,
        "nombre_salons": bien.nombre_salons,
        "nombre_salles_bain": bien.nombre_salles_bain,
        "superficie": str(bien.superficie) if bien.superficie is not None else None,
        "etage": bien.etage,
        "parking": bien.parking,
        "description": bien.description,
    }


def haversine(lat1, lng1, lat2, lng2):
    """Distance en km entre deux points GPS."""
    from math import radians, cos, sin, asin, sqrt

    radius_km = 6371
    lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlng / 2) ** 2
    return radius_km * 2 * asin(sqrt(a))


def geocode_address(address, ville="Abidjan"):
    """Geocode une adresse avec Nominatim et met en cache le résultat."""
    query = ", ".join(part for part in [address, ville, "Cote d'Ivoire"] if part)
    if not query.strip():
        return None

    import hashlib

    cache_key = "logeciv:geocode:" + hashlib.sha1(normalize_text(query).encode("utf-8")).hexdigest()
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": query,
        "format": "jsonv2",
        "limit": 1,
    }
    headers = {"User-Agent": "LogeCiv/1.0 (https://logeciv.ci)"}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=5)
        response.raise_for_status()
        results = response.json()
        if not results:
            cache.set(cache_key, None, 60 * 60)
            return None

        point = {
            "latitude": float(results[0]["lat"]),
            "longitude": float(results[0]["lon"]),
            "display_name": results[0].get("display_name", ""),
            "source": "nominatim",
        }
        cache.set(cache_key, point, 60 * 60 * 24 * 7)
        return point
    except RequestException:
        return None
    except (TypeError, ValueError, KeyError):
        return None


def serialize_bien_for_map(bien_obj):
    """Transforme un objet Bien en point pour Leaflet."""
    if isinstance(bien_obj, dict):
        data = bien_obj
    else:
        data = serialize_bien(bien_obj)
    
    # Utiliser les coordonnées réelles si présentes, sinon geocoder
    lat = getattr(bien_obj, 'latitude', None) if not isinstance(bien_obj, dict) else bien_obj.get('latitude')
    lng = getattr(bien_obj, 'longitude', None) if not isinstance(bien_obj, dict) else bien_obj.get('longitude')

    if lat and lng:
        data.update({"latitude": float(lat), "longitude": float(lng), "carte_disponible": True})
    else:
        coords = geocode_address(data.get("localisation") or data.get("ville"), data.get("ville"))
        if coords:
            data.update(coords)
            data["carte_disponible"] = True
        else:
            data["carte_disponible"] = False
    return data


def serialize_biens_for_map(biens_qs, limit=20):
    return [serialize_bien_for_map(b) for b in biens_qs[:limit]]


def filter_points_by_radius(points, lat, lng, rayon_km=5):
    filtered = []
    for point in points:
        point_lat = point.get("latitude")
        point_lng = point.get("longitude")
        if point_lat is None or point_lng is None:
            continue
        if haversine(lat, lng, point_lat, point_lng) <= rayon_km:
            filtered.append(point)
    return filtered


def call_ai(messages, max_tokens=800, temperature=0.4):
    api_key = (
        getattr(settings, "IA_CHAT_API_KEY", "")
        or getattr(settings, "GROK_API_KEY", "")
        or getattr(settings, "GROQ_API_KEY", "")
        or getattr(settings, "OPENAI_API_KEY", "")
    )
    api_url = (
        getattr(settings, "IA_CHAT_API_URL", "")
        or getattr(settings, "GROK_API_URL", "")
        or getattr(settings, "GROQ_API_URL", "")
        or getattr(settings, "OPENAI_API_URL", "")
        or "https://api.x.ai/v1/chat/completions"
    )
    model = (
        getattr(settings, "IA_CHAT_MODEL", "")
        or getattr(settings, "GROK_MODEL", "")
        or "gpt-4o-mini"
    )

    if not api_key:
        return None, "IA key missing"

    try:
        response = requests.post(
            api_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            timeout=30,
        )
    except RequestException as exc:
        return None, str(exc)

    if response.status_code != 200:
        return None, f"Erreur IA"

    try:
        payload = response.json()
        return payload["choices"][0]["message"]["content"], None
    except:
        return None, "Format IA invalide"


def extract_budget(text):
    if not text:
        return None
    numbers = [int(match.replace(" ", "")) for match in re.findall(r"\b\d[\d ]*\b", text)]
    return numbers[-1] if numbers else None


def generate_smart_prompt(criteria, resultats, suggestions):
    ville = criteria.get("ville") or "Côte d'Ivoire"
    type_bien = criteria.get("type_bien") or "logement"
    budget_max = criteria.get("budget_max")
    localisation = criteria.get("quartier") or criteria.get("commune") or criteria.get("proximite") or ""

    resultats_text = json.dumps(resultats[:5], ensure_ascii=False)
    suggestions_text = json.dumps(suggestions[:5], ensure_ascii=False)

    budget_text = f"budget maximal de {budget_max} FCFA" if budget_max else "budget non précisé"
    localisation_text = f"localisation: {localisation}" if localisation else "localisation non précisée"

    return (
        f"Tu es un assistant immobilier expert en Côte d'Ivoire. "
        f"Critères: ville={ville}, type={type_bien}, {budget_text}, {localisation_text}. "
        f"Résultats trouvés: {resultats_text}. "
        f"Suggestions alternatives: {suggestions_text}. "
        "Propose une réponse claire, précise et utile en français, en indiquant si les biens correspondent à la recherche "
        "ou si des alternatives sont nécessaires."
    )


def recommande_villes_par_budget(budget):
    try:
        budget = int(budget)
    except (TypeError, ValueError):
        return []

    recommendations = []
    for ville, info in SECONDARY_CITIES.items():
        min_price, max_price = info["price_range"]
        if budget >= min_price:
            recommendations.append(
                {
                    "ville": ville.title(),
                    "prix_range": f"{min_price:,} - {max_price:,} FCFA",
                    "description": info["description"],
                }
            )

    if not recommendations:
        recommendations = [
            {
                "ville": "Abidjan",
                "prix_range": "100000 - 500000 FCFA",
                "description": "Ville principale avec de nombreuses options immobilières.",
            }
        ]

    return recommendations[:5]


def extract_search_criteria(data):
    texte = data.get("texte", "")
    ville = data.get("ville") or None
    quartier = data.get("quartier") or None
    commune = data.get("commune") or None
    type_bien = data.get("type_bien") or None
    budget_min = data.get("budget_min") or None
    budget_max = data.get("budget_max") or None
    nombre_chambres = data.get("nombre_chambres") or data.get("nombre_chambres_min") or None
    nombre_salles_bain = data.get("nombre_salles_bain") or None
    superficie_min = data.get("superficie_min") or None
    superficie_max = data.get("superficie_max") or None
    meuble = data.get("meuble")
    parking = data.get("parking")
    piscine = data.get("piscine")
    securite = data.get("securite")
    proximite = data.get("proximite") or None
    statut = data.get("statut") or None

    text_norm = normalize_text(texte)
    if not ville and text_norm:
        villes = list(Bien.objects.values_list("ville", flat=True).distinct())
        ville = next((item for item in villes if normalize_text(item) in text_norm), None)

    if not type_bien and text_norm:
        types = ["appartement", "maison", "terrain", "bureau", "commerce", "studio", "villa"]
        type_bien = next((item for item in types if item in text_norm), None)

    budget_from_text = extract_budget(texte)
    if not budget_max and budget_from_text:
        budget_max = budget_from_text

    if isinstance(nombre_chambres, str) and nombre_chambres.isdigit():
        nombre_chambres = int(nombre_chambres)

    return {
        "texte": texte,
        "ville": ville,
        "quartier": quartier,
        "commune": commune,
        "type_bien": type_bien,
        "budget_min": budget_min,
        "budget_max": budget_max,
        "nombre_chambres": nombre_chambres,
        "nombre_salles_bain": nombre_salles_bain,
        "superficie_min": superficie_min,
        "superficie_max": superficie_max,
        "meuble": meuble,
        "parking": parking,
        "piscine": piscine,
        "securite": securite,
        "proximite": proximite,
        "statut": statut,
    }


def build_bien_queryset(criteria):
    biens = Bien.objects.filter(statut="disponible")

    if criteria.get("ville"):
        biens = biens.filter(ville__icontains=criteria["ville"])
    if criteria.get("quartier"):
        biens = biens.filter(localisation__icontains=criteria["quartier"])
    if criteria.get("commune"):
        biens = biens.filter(localisation__icontains=criteria["commune"])
    if criteria.get("type_bien"):
        biens = biens.filter(type__icontains=criteria["type_bien"])
    if criteria.get("budget_min") is not None:
        biens = biens.filter(prix__gte=criteria["budget_min"])
    if criteria.get("budget_max") is not None:
        biens = biens.filter(prix__lte=criteria["budget_max"])
    if criteria.get("nombre_chambres") is not None:
        biens = biens.filter(nombre_chambres__gte=criteria["nombre_chambres"])
    if criteria.get("nombre_salles_bain") is not None:
        biens = biens.filter(nombre_salles_bain__gte=criteria["nombre_salles_bain"])
    if criteria.get("superficie_min") is not None:
        biens = biens.filter(superficie__gte=criteria["superficie_min"])
    if criteria.get("superficie_max") is not None:
        biens = biens.filter(superficie__lte=criteria["superficie_max"])
    if criteria.get("meuble") is True:
        biens = biens.filter(meuble=True)
    if criteria.get("meuble") is False:
        biens = biens.filter(meuble=False)
    if criteria.get("parking") is True:
        biens = biens.filter(parking=True)
    if criteria.get("parking") is False:
        biens = biens.filter(parking=False)
    if criteria.get("piscine") is True:
        biens = biens.filter(piscine=True)
    if criteria.get("piscine") is False:
        biens = biens.filter(piscine=False)
    if criteria.get("securite") is True:
        biens = biens.filter(securite=True)
    if criteria.get("securite") is False:
        biens = biens.filter(securite=False)
    if criteria.get("proximite"):
        biens = biens.filter(proximite__icontains=criteria["proximite"]) | biens.filter(localisation__icontains=criteria["proximite"])
    if criteria.get("statut"):
        statut = criteria["statut"].lower()
        if statut in ["location", "vente", "location_vente"]:
            biens = biens.filter(transaction_type__iexact=statut)

    return biens.order_by("prix", "-created_at")


def build_alternatives(criteria, limit=5):
    budget_max = criteria.get("budget_max") or 0
    type_bien = criteria.get("type_bien")
    ville = criteria.get("ville") or ""
    ville_norm = normalize_text(ville)

    alternative_query = Bien.objects.filter(statut="disponible")
    if budget_max:
        alternative_query = alternative_query.filter(prix__lte=budget_max)
    if type_bien:
        alternative_query = alternative_query.filter(type__icontains=type_bien)
    if ville:
        alternative_query = alternative_query.exclude(ville__icontains=ville)

    results = [serialize_bien(bien) for bien in alternative_query.order_by("prix")[:limit]]
    if results:
        return results

    alternative_villes = ABIDJAN_ZONES.get(ville_norm, [])
    if alternative_villes:
        alt_biens = Bien.objects.filter(statut="disponible")
        if budget_max:
            alt_biens = alt_biens.filter(prix__lte=budget_max)
        if type_bien:
            alt_biens = alt_biens.filter(type__icontains=type_bien)
        alt_biens = alt_biens.filter(ville__in=alternative_villes)
        results = [serialize_bien(bien) for bien in alt_biens.order_by("prix")[:limit]]

    if results:
        return results

    if budget_max:
        fallback = Bien.objects.filter(statut="disponible", prix__lte=budget_max).order_by("prix")[:limit]
        results = [serialize_bien(bien) for bien in fallback]

    if results:
        return results

    fallback = Bien.objects.filter(statut="disponible").order_by("prix")[:limit]
    return [serialize_bien(bien) for bien in fallback]


def explain_alternatives(criteria, suggestions):
    ville = criteria.get("ville")
    budget_max = criteria.get("budget_max")
    if ville and budget_max and suggestions:
        return (
            f"Je n'ai pas trouvé une correspondance parfaite à {ville} avec {budget_max} FCFA. "
            "Voici des alternatives adaptées à votre budget."
        )
    if ville and suggestions:
        return f"Je n'ai pas trouvé une correspondance exacte à {ville}. Voici des logements alternatifs."
    if suggestions:
        return "Voici des logements similaires disponibles."
def chat_immobilier_v3(message, history=[], lat=None, lng=None):
    criteria = extract_search_criteria({"texte": message})
    logements, en_fallback, niveau = filtrer_biens_intelligemment(criteria)
    if lat and lng:
        logements = filter_points_by_radius(logements, float(lat), float(lng), 5)
    context = {"logements": logements[:8], "nb_resultats": len(logements), "en_fallback": en_fallback}
    messages = [{"role": "system", "content": LOGI_SYSTEM_PROMPT}]
    for h in history[-10:]: messages.append(h)
    messages.append({"role": "user", "content": f"Context: {json.dumps(context)}\nMsg: {message}"})
    reply, _ = call_ai(messages)
    return {
        "reply": reply,
        "reponse": reply,
        "logements": logements,
        "en_fallback": en_fallback,
        "criteres": criteria,
    }


def chat_immobilier(message):
    criteria = extract_search_criteria({"texte": message})
    suggestions = build_alternatives(criteria, limit=5)
    resultats = [serialize_bien(bien) for bien in build_bien_queryset(criteria)[:5]]

    if criteria.get("budget_max") and criteria.get("budget_max") <= 100000 and not criteria.get("ville"):
        base_reply = (
            "Avec ce budget, je vous recommande Bouaké, Yamoussoukro, Daloa ou Korhogo."
        )
    elif criteria.get("budget_max") and criteria.get("budget_max") <= 150000:
        base_reply = "Avec ce budget, ciblez des quartiers abordables ou des villes secondaires."
    else:
        base_reply = "Je peux vous aider à trouver un bien adapté à votre budget et à votre zone préférée."

    if criteria.get("ville"):
        base_reply = (
            f"J'ai compris que vous cherchez autour de {criteria['ville']}."
            + (" " + base_reply if base_reply else "")
        )

    if resultats:
        base_reply = (
            f"{base_reply} J'ai trouvé {len(resultats)} logement(s) correspondant à votre demande."
        )
    elif suggestions:
        base_reply = (
            f"{base_reply} Je vous propose ces alternatives intéressantes."
        )

    prompt = (
        "Tu es un assistant immobilier amical et concret pour la Côte d'Ivoire. "
        "Réponds en français, en 3 phrases maximum, avec un ton utile et orienté action. "
        f"Message utilisateur: {message}. "
        f"Critères extraits: {json.dumps(criteria, ensure_ascii=False)}. "
        f"Biens trouvés: {json.dumps(resultats[:5], ensure_ascii=False)}. "
        f"Suggestions: {json.dumps(suggestions[:5], ensure_ascii=False)}."
    )
    ai_text, _ = call_ai(
        [
            {"role": "system", "content": "Tu es un assistant immobilier conversationnel."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=220,
        temperature=0.5,
    )

    return {
        "message": message,
        "criteres": criteria,
        "reponse": ai_text or base_reply,
        "resultats": resultats,
        "suggestions": suggestions,
    }


def search_biens_intelligente_v2(data):
    criteria = extract_search_criteria(data)
    biens_queryset = list(build_bien_queryset(criteria)[:10])
    resultats = [serialize_bien(bien) for bien in biens_queryset]
    map_points = serialize_biens_for_map(biens_queryset, limit=10)

    if resultats:
        budget_note = (
            f" avec un budget max de {criteria['budget_max']} FCFA"
            if criteria.get("budget_max")
            else ""
        )
        ai_message = f"Voici des logements correspondant a votre recherche{budget_note}."
        prompt = generate_smart_prompt(criteria, resultats, [])
        ai_text, _ = call_ai(
            [
                {"role": "system", "content": LOGI_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": prompt + f"\n\nBiens trouves: {json.dumps(resultats[:5], ensure_ascii=False)}"
                    + f"\n\nCarte: {json.dumps(map_points[:5], ensure_ascii=False)}",
                },
            ],
            max_tokens=250,
            temperature=0.3,
        )
        return {
            "type": "resultats",
            "message": ai_message,
            "analyse_ia": ai_text or ai_message,
            "criteres": criteria,
            "resultats": resultats,
            "map_points": map_points,
            "suggestions": [],
        }

    suggestions = build_alternatives(criteria, limit=5)
    message = explain_alternatives(criteria, suggestions)
    prompt = generate_smart_prompt(criteria, [], suggestions)
    ai_text, _ = call_ai(
        [
            {"role": "system", "content": LOGI_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": prompt + f"\n\nAlternatives: {json.dumps(suggestions[:5], ensure_ascii=False)}",
            },
        ],
        max_tokens=250,
        temperature=0.4,
    )

    return {
        "type": "suggestions",
        "message": message,
        "analyse_ia": ai_text or message,
        "criteres": criteria,
        "resultats": [],
        "map_points": [],
        "suggestions": suggestions,
    }


def chat_immobilier_v2(message):
    criteria = extract_search_criteria({"texte": message})
    suggestions = build_alternatives(criteria, limit=5)
    biens_queryset = list(build_bien_queryset(criteria)[:5])
    resultats = [serialize_bien(bien) for bien in biens_queryset]
    map_points = serialize_biens_for_map(biens_queryset, limit=5)

    if criteria.get("budget_max") and criteria.get("budget_max") <= 100000 and not criteria.get("ville"):
        base_reply = "Avec ce budget, je vous recommande Bouaké, Yamoussoukro, Daloa ou Korhogo."
    elif criteria.get("budget_max") and criteria.get("budget_max") <= 150000:
        base_reply = "Avec ce budget, ciblez des quartiers abordables ou des villes secondaires."
    else:
        base_reply = "Je peux vous aider à trouver un bien adapté à votre budget et à votre zone préférée."

    if criteria.get("ville"):
        base_reply = (
            f"J'ai compris que vous cherchez autour de {criteria['ville']}."
            + (" " + base_reply if base_reply else "")
        )

    if resultats:
        base_reply = f"{base_reply} J'ai trouvé {len(resultats)} logement(s) correspondant à votre demande."
        if map_points:
            base_reply = f"{base_reply} Certains biens sont aussi visibles sur la carte."
    elif suggestions:
        base_reply = f"{base_reply} Je vous propose ces alternatives intéressantes."

    prompt = (
        "Tu es un assistant immobilier amical et concret pour la Côte d'Ivoire. "
        "Réponds en français, en 3 phrases maximum, avec un ton utile et orienté action. "
        f"Message utilisateur: {message}. "
        f"Critères extraits: {json.dumps(criteria, ensure_ascii=False)}. "
        f"Biens trouvés: {json.dumps(resultats[:5], ensure_ascii=False)}. "
        f"Carte: {json.dumps(map_points[:5], ensure_ascii=False)}. "
        f"Suggestions: {json.dumps(suggestions[:5], ensure_ascii=False)}."
    )
    ai_text, _ = call_ai(
        [
            {"role": "system", "content": LOGI_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        max_tokens=220,
        temperature=0.5,
    )

    return {
        "message": message,
        "criteres": criteria,
        "reponse": ai_text or base_reply,
        "resultats": resultats,
        "map_points": map_points,
        "suggestions": suggestions,
    }


search_biens_intelligente = search_biens_intelligente_v2
chat_immobilier = chat_immobilier_v2


def validate_document_locally(document_type, document_data=None):
    doc_type_norm = normalize_text(document_type)

    valid_types = {
        "cni": {"name": "Carte Nationale d'Identité", "required_fields": ["numero", "date_expiration"]},
        "passeport": {"name": "Passeport", "required_fields": ["numero", "date_expiration"]},
        "rccm": {"name": "Registre de Commerce", "required_fields": ["numero_rccm", "raison_sociale"]},
        "acte_propriete": {"name": "Acte de Propriété", "required_fields": ["numero_acte", "proprio"]},
        "justif_propriete": {"name": "Justificatif de Propriété", "required_fields": []},
    }

    for key, info in valid_types.items():
        if key in doc_type_norm or info["name"].lower() in doc_type_norm:
            return True, info["name"]

    return False, "Type de document non reconnu"


def verify_document(document_type, document_url, document_data=None):
    is_valid_type, type_name = validate_document_locally(document_type)

    prompt = (
        "Tu es un expert en vérification de documents immobiliers en Côte d'Ivoire avec 15 ans d'expérience. "
        f"Analyse ce document de type '{document_type}' ({type_name if is_valid_type else 'type inconnu'}). "
        "Tu dois vérifier : "
        "1. Cohérence du format et du contenu "
        "2. Signes de fraude ou d'altération "
        "3. Données complètes et valides "
        "Réponds en JSON avec ces champs exactement: "
        "{'verdict': 'Valide'|'Suspect'|'Incomplet', "
        "'confiance': 0-100, "
        "'message': 'explication claire', "
        "'details': {'type_document': '...', 'qualite': '...', 'completes': true/false, 'risques': [...], 'recommandations': [...]}}"
    )

    ai_text, ai_error = call_ai(
        [
            {"role": "system", "content": "Tu es un assistant expert en vérification de documents immobiliers. Réponds toujours en JSON valide."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=350,
        temperature=0.2,
    )

    def fallback_validation():
        if not is_valid_type:
            return {
                "verdict": "Document incomplet",
                "confidence": 30,
                "message": "Type de document non reconnu ou fourni. Vérification manuelle obligatoire.",
                "details": {
                    "type_document": document_type,
                    "qualite": "Type invalide",
                    "authentique": False,
                    "risques": ["Type de document non valide"],
                    "recommandations": ["Soumettre un type de document valide", "Vérification manuelle requise"],
                },
            }

        if "cni" in normalize_text(document_type) or "passeport" in normalize_text(document_type):
            return {
                "verdict": "Document valide",
                "confidence": 75,
                "message": "Pièce d'identité valide. Une vérification officielle est recommandée pour les transactions importantes.",
                "details": {
                    "type_document": type_name,
                    "qualite": "Acceptable",
                    "authentique": True,
                    "risques": ["Risque de falsification possible"],
                    "recommandations": ["Vérifier auprès des autorités officielles", "Vérifier l'authenticité du numéro"],
                },
            }

        if "rccm" in normalize_text(document_type):
            return {
                "verdict": "Document valide",
                "confidence": 80,
                "message": "RCCM validé. Confirmez la numérotation avec le registre national.",
                "details": {
                    "type_document": type_name,
                    "qualite": "Bon",
                    "authentique": True,
                    "risques": [],
                    "recommandations": ["Vérifier le statut juridique actuel", "Confirmer l'activité légale"],
                },
            }

        return {
            "verdict": "Document suspect",
            "confidence": 50,
            "message": "Le document nécessite une vérification manuelle plus approfondie.",
            "details": {
                "type_document": type_name or document_type,
                "qualite": "À évaluer",
                "authentique": False,
                "risques": ["Vérification insuffisante", "Données manquantes"],
                "recommandations": ["Verification manuelle recommandée", "Consulter un expert légal"],
            },
        }

    if ai_text:
        try:
            parsed = json.loads(ai_text)
            if isinstance(parsed, dict):
                verdict = parsed.get("verdict", "Document suspect")
                confidence = min(100, max(0, int(parsed.get("confiance", parsed.get("confidence", 50)))))
                message = parsed.get("message", "Vérification réalisée.")
                details = parsed.get("details", {})

                return {
                    "verdict": verdict,
                    "confidence": confidence,
                    "message": message,
                    "details": details,
                    "ai_analysis": ai_text,
                }
        except (ValueError, TypeError, json.JSONDecodeError):
            pass

    result = fallback_validation()
    result["ai_analysis"] = ai_text or f"AI indisponible: {ai_error}" if ai_error else "Analyse IA utilisée par défaut"
    return result
def verify_document_v2(document_type, document_url, document_data=None):
    is_valid_type, type_name = validate_document_locally(document_type)

    prompt = (
        "Tu es un expert en vérification de documents immobiliers en Côte d'Ivoire. "
        f"Analyse ce document de type '{document_type}' ({type_name if is_valid_type else 'type inconnu'}). "
        "Réponds en JSON valide avec les champs: "
        "{'verdict': 'Valide'|'Suspect'|'Incomplet', 'confiance': 0-100, 'message': '...', 'details': {...}}"
    )

    ai_text, ai_error = call_ai(
        [
            {"role": "system", "content": "Tu es un assistant expert en verification de documents immobiliers. Reponds toujours en JSON valide."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=350,
        temperature=0.2,
    )

    def fallback_validation():
        if not is_valid_type:
            return {
                "verdict": "Incomplet",
                "valide": False,
                "confidence": 30,
                "message": "Type de document non reconnu ou fourni. Vérification manuelle obligatoire.",
                "details": {
                    "type_document": document_type,
                    "qualite": "Type invalide",
                    "authentique": False,
                    "risques": ["Type de document non valide"],
                    "recommandations": ["Soumettre un type de document valide", "Vérification manuelle requise"],
                },
            }

        return {
            "verdict": "Suspect",
            "valide": False,
            "confidence": 50,
            "message": "Le document nécessite une vérification manuelle plus approfondie. Vérification manuelle recommandée.",
            "details": {
                "type_document": type_name or document_type,
                "qualite": "À évaluer",
                "authentique": False,
                "risques": ["Vérification insuffisante", "Données manquantes"],
                "recommandations": ["Vérification manuelle recommandée", "Consulter un expert légal"],
            },
        }

    if ai_text:
        try:
            parsed = json.loads(ai_text)
            if isinstance(parsed, dict):
                verdict = parsed.get("verdict", "Suspect")
                confidence = min(100, max(0, int(parsed.get("confiance", parsed.get("confidence", 50)))))
                message = parsed.get("message", "Vérification réalisée.")
                details = parsed.get("details", {})
                if "type_detecte" not in details:
                    details["type_detecte"] = document_type.upper() if document_type else "INCONNU"
                return {
                    "verdict": verdict,
                    "valide": str(verdict).strip().lower() in {"valide", "document valide", "valid"},
                    "confidence": confidence,
                    "message": message,
                    "details": details,
                    "ai_analysis": ai_text,
                }
        except (ValueError, TypeError, json.JSONDecodeError):
            pass

    result = fallback_validation()
    result["ai_analysis"] = ai_text or (f"AI indisponible: {ai_error}" if ai_error else "Analyse IA utilisée par défaut")
    if "type_detecte" not in result["details"]:
        result["details"]["type_detecte"] = document_type.upper() if document_type else "INCONNU"
    return result


verify_document = verify_document_v2
