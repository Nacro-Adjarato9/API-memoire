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
Agis comme un agent humain, chaleureux et expert. Adapte ton ton à ce que l'utilisateur vient
d'écrire, ne suis jamais un script fixe qui se répète peu importe le message.
Langues : Français, Anglais, Dioula.
RÈGLES :
1. Si 'context.recherche_demandee' est false (l'utilisateur n'a pas exprimé de critère de
   recherche : simple salutation, question générale, remerciement, etc.) : réponds
   naturellement à ce qu'il a dit, ne mentionne AUCUN bien, AUCUN prix, AUCUNE alternative,
   et pose une question ouverte pour comprendre ce qu'il cherche (ville, budget, type de logement).
2. Si 'context.recherche_demandee' est true : utilise UNIQUEMENT les données du 'context'
   pour présenter les biens ou alternatives trouvés. Ne jamais inventer de prix ou de biens.
3. Si recherche demandée mais aucun bien trouvé : propose les alternatives du 'context' avec pédagogie.
4. Ne suggère de regarder la carte interactive que si des biens sont réellement présentés.
5. Termine par une question, adaptée au contexte de la conversation."""

# Critères qui indiquent une vraie intention de recherche (par opposition à un message de
# conversation générale comme "Bonjour" ou "Merci"). Si aucun n'est présent, on ne déclenche
# ni recherche en base ni mention de biens dans la réponse.
CRITERES_INTENTION_RECHERCHE = (
    "ville", "quartier", "commune", "type_bien", "budget_min", "budget_max",
    "nombre_chambres", "proximite",
)


def has_search_intent(criteria):
    return any(criteria.get(champ) for champ in CRITERES_INTENTION_RECHERCHE)

def get_adjacent_zones(zone):
    """Zones voisines connues pour une commune donnée (module 5 réutilise ceci)."""
    return ABIDJAN_ZONES.get(normalize_text(zone), [])


def search_with_fallback(criteria, limit=10):
    """Recherche avec repli en cascade : budget -> zone -> commune voisine -> global.

    Retourne (liste_de_Bien, info) où info decrit si/comment la recherche a ete elargie,
    pour que l'appelant (API ou chat) puisse l'expliquer a l'utilisateur.
    """
    qs = build_bien_queryset(criteria)
    if qs.exists():
        return list(qs[:limit]), {"fallback": False, "relaxed": []}

    relaxed = []

    if criteria.get("budget_max"):
        criteria_budget = criteria.copy()
        criteria_budget["budget_max"] = int(criteria["budget_max"]) * 1.2
        qs = build_bien_queryset(criteria_budget)
        if qs.exists():
            relaxed.append("budget")
            return list(qs[:limit]), {"fallback": True, "relaxed": relaxed}

    criteria_zone = criteria.copy()
    criteria_zone["quartier"] = None
    criteria_zone["commune"] = None
    qs = build_bien_queryset(criteria_zone)
    if qs.exists():
        relaxed.append("zone")
        return list(qs[:limit]), {"fallback": True, "relaxed": relaxed}

    ville = criteria.get("ville") or ""
    zones_voisines = get_adjacent_zones(ville)
    if zones_voisines:
        qs = Bien.objects.filter(statut="disponible", ville__in=zones_voisines)
        if criteria.get("budget_max"):
            qs = qs.filter(prix__lte=criteria["budget_max"])
        if criteria.get("type_bien"):
            qs = qs.filter(type__icontains=criteria["type_bien"])
        qs = qs.order_by("prix")
        if qs.exists():
            relaxed.append("ville_voisine")
            return list(qs[:limit]), {
                "fallback": True,
                "relaxed": relaxed,
                "villes_suggerees": zones_voisines,
            }

    qs = Bien.objects.filter(statut="disponible")
    if criteria.get("budget_max"):
        qs = qs.filter(prix__lte=criteria["budget_max"])
    relaxed.append("global")
    return list(qs.order_by("prix")[:limit]), {"fallback": True, "relaxed": relaxed}


TREND_CACHE_TTL = 60 * 60 * 25  # 25h : le cron quotidien rafraîchit avant expiration
TREND_INDEX_KEY = "logeciv:trend:index"


def _trend_cache_key(ville, type_bien):
    return f"logeciv:trend:{normalize_text(ville)}:{normalize_text(type_bien)}"


def compute_trends():
    """Module 6 : agrège prix moyen/min/max par (ville, type) et met en cache Redis.

    Pas de nouvelle table : les résultats sont recalculés (via ce batch, exécuté par un
    planificateur externe type cron) et stockés dans le cache déjà configuré (django-redis),
    avec une variation semaine/semaine calculée par rapport à la dernière valeur en cache.
    """
    from django.db.models import Avg, Count, Max, Min

    groupes = (
        Bien.objects.filter(statut="disponible")
        .values("ville", "type")
        .annotate(nb_biens=Count("id"), prix_moyen=Avg("prix"), prix_min=Min("prix"), prix_max=Max("prix"))
    )

    index = []
    for groupe in groupes:
        ville, type_bien = groupe["ville"], groupe["type"]
        key = _trend_cache_key(ville, type_bien)
        precedent = cache.get(key)
        prix_moyen = float(groupe["prix_moyen"])

        variation_pct = None
        if precedent and precedent.get("prix_moyen"):
            variation_pct = round((prix_moyen - precedent["prix_moyen"]) / precedent["prix_moyen"] * 100, 1)

        snapshot = {
            "ville": ville,
            "type": type_bien,
            "nb_biens": groupe["nb_biens"],
            "prix_moyen": prix_moyen,
            "prix_min": float(groupe["prix_min"]),
            "prix_max": float(groupe["prix_max"]),
            "variation_pct_semaine": variation_pct,
        }
        cache.set(key, snapshot, TREND_CACHE_TTL)
        index.append(key)

    cache.set(TREND_INDEX_KEY, index, TREND_CACHE_TTL)
    return index


def get_trends():
    """Lit uniquement le cache (pas de recalcul à la volée) pour un dashboard rapide."""
    index = cache.get(TREND_INDEX_KEY) or []
    trends = [cache.get(key) for key in index]
    return [t for t in trends if t is not None]


MOTS_CLES_SUSPECTS = [
    "paiement avant visite",
    "payer avant de visiter",
    "sans visite",
    "pas de visite possible",
    "virement immediat",
    "virement immédiat",
    "urgent",
    "depart precipite",
    "départ précipité",
    "argent d'abord",
]

SEUIL_SUSPICION = 5


def evaluate_bien_fraud(bien):
    """Module 4 : score de suspicion basé uniquement sur des règles (pas d'appel IA).

    Trois règles indépendantes qui accumulent des points :
    1) prix hors norme comparé à la moyenne ville+type,
    2) mots-clés suspects dans la description,
    3) fréquence de publication suspecte du même propriétaire + signalements existants.
    """
    from datetime import timedelta

    from django.db.models import Avg
    from django.utils import timezone

    score = 0.0
    raisons = []

    # Règle 1 : prix hors norme (moyenne ville+type, hors ce bien)
    stats = (
        Bien.objects.filter(ville=bien.ville, type=bien.type)
        .exclude(id=bien.id)
        .aggregate(prix_moyen=Avg("prix"))
    )
    prix_moyen = stats["prix_moyen"]
    if prix_moyen:
        prix_moyen = float(prix_moyen)
        prix = float(bien.prix)
        if prix < prix_moyen * 0.3:
            score += 4
            raisons.append(f"Prix très inférieur à la moyenne du marché ({prix} vs ~{prix_moyen:.0f} FCFA)")
        elif prix > prix_moyen * 3:
            score += 2
            raisons.append(f"Prix très supérieur à la moyenne du marché ({prix} vs ~{prix_moyen:.0f} FCFA)")

    # Règle 2 : mots-clés suspects dans la description
    description_norm = normalize_text(bien.description)
    mots_trouves = [mot for mot in MOTS_CLES_SUSPECTS if normalize_text(mot) in description_norm]
    if mots_trouves:
        score += 2 * len(mots_trouves)
        raisons.append(f"Termes suspects dans la description: {', '.join(mots_trouves)}")

    # Règle 3 : fréquence de publication + signalements existants
    if bien.proprietaire_id:
        recent_count = Bien.objects.filter(
            proprietaire_id=bien.proprietaire_id,
            created_at__gte=timezone.now() - timedelta(hours=24),
        ).count()
        if recent_count >= 5:
            score += 3
            raisons.append(f"{recent_count} annonces publiées par le même propriétaire en 24h")

    nb_signalements = bien.signalements.count() if hasattr(bien, "signalements") else 0
    if nb_signalements:
        score += min(nb_signalements, 3) * 2
        raisons.append(f"{nb_signalements} signalement(s) utilisateur existant(s)")

    return {
        "score_suspicion": score,
        "est_suspect": score >= SEUIL_SUSPICION,
        "raisons": raisons,
    }


def check_new_matches_and_price_drops():
    """Module 7 : détecte les nouveaux biens correspondant aux recherches sauvegardées
    et les baisses de prix sur les favoris, puis notifie (anti-spam via notify_once)."""
    from django.utils import timezone

    from favoris.models import Favori
    from notifications.services import notify_once
    from utilisateurs.models import HistoriqueRecherche

    nb_notifs = 0

    # 1) Recherches sauvegardées : nouveaux biens depuis le dernier passage
    utilisateur_ids = HistoriqueRecherche.objects.values_list("utilisateur_id", flat=True).distinct()
    for user_id in utilisateur_ids:
        derniere_recherche = HistoriqueRecherche.objects.filter(utilisateur_id=user_id).order_by("-date").first()
        if not derniere_recherche:
            continue

        criteria = extract_search_criteria({"texte": derniere_recherche.critere_recherche})
        cache_key = f"logeciv:notif:last_check:{user_id}"
        derniere_verif = cache.get(cache_key)
        maintenant = timezone.now()

        qs = build_bien_queryset(criteria)
        if derniere_verif:
            qs = qs.filter(created_at__gt=derniere_verif)
        nouveaux = list(qs[:5])

        if nouveaux:
            noms = ", ".join(b.titre for b in nouveaux[:3])
            message = f"{len(nouveaux)} nouveau(x) bien(s) correspondent à votre recherche : {noms}."
            dedup_key = "saved_search:" + "-".join(str(b.id) for b in nouveaux)
            notification = notify_once(
                derniere_recherche.utilisateur, "saved_search", dedup_key, message, bien=nouveaux[0]
            )
            if notification:
                nb_notifs += 1

        cache.set(cache_key, maintenant, 60 * 60 * 24 * 7)

    # 2) Favoris : baisse de prix depuis le dernier passage
    for favori in Favori.objects.select_related("bien", "utilisateur"):
        cache_key = f"logeciv:notif:last_price:{favori.id}"
        prix_connu = cache.get(cache_key)
        prix_actuel = float(favori.bien.prix)

        if prix_connu is not None and prix_actuel < prix_connu:
            message = (
                f"Le prix de '{favori.bien.titre}' a baissé : "
                f"{prix_connu:.0f} FCFA -> {prix_actuel:.0f} FCFA."
            )
            dedup_key = f"price_drop:{favori.id}:{prix_actuel}"
            notification = notify_once(favori.utilisateur, "price_drop", dedup_key, message, bien=favori.bien)
            if notification:
                nb_notifs += 1

        cache.set(cache_key, prix_actuel, 60 * 60 * 24 * 30)

    return nb_notifs


def recommend_for_user(user, limit=10):
    """Module 2 : recommandations personnalisées à partir de l'historique de recherche
    et des favoris de l'utilisateur — règles pondérées, pas de ML (échelle du projet)."""
    from collections import Counter

    from favoris.models import Favori
    from utilisateurs.models import HistoriqueRecherche

    historiques = HistoriqueRecherche.objects.filter(utilisateur=user).order_by("-date")[:20]
    favoris = Favori.objects.filter(utilisateur=user).select_related("bien")

    villes = Counter()
    types = Counter()
    prix_connus = []

    for h in historiques:
        criteria = extract_search_criteria({"texte": h.critere_recherche})
        if criteria.get("ville"):
            villes[normalize_text(criteria["ville"])] += 1
        if criteria.get("type_bien"):
            types[criteria["type_bien"]] += 1
        if criteria.get("budget_max"):
            prix_connus.append(criteria["budget_max"])

    biens_favoris_ids = set()
    for fav in favoris:
        biens_favoris_ids.add(fav.bien_id)
        villes[normalize_text(fav.bien.ville)] += 2  # un favori pèse plus qu'une simple recherche
        types[fav.bien.type] += 2
        prix_connus.append(float(fav.bien.prix))

    if not villes and not types and not prix_connus:
        # Pas assez de signal : pas de personnalisation possible, laisser l'appelant
        # retomber sur une liste générique (ex: biens les plus récents).
        return []

    ville_preferee = villes.most_common(1)[0][0] if villes else None
    type_prefere = types.most_common(1)[0][0] if types else None
    prix_moyen = sum(prix_connus) / len(prix_connus) if prix_connus else None
    fourchette = (prix_moyen * 0.7, prix_moyen * 1.3) if prix_moyen else None

    candidats = Bien.objects.filter(statut="disponible").exclude(id__in=biens_favoris_ids)

    scores = []
    for bien in candidats:
        score = 0
        if ville_preferee and normalize_text(bien.ville) == ville_preferee:
            score += 3
        if type_prefere and bien.type == type_prefere:
            score += 2
        if fourchette and fourchette[0] <= float(bien.prix) <= fourchette[1]:
            score += 2
        if score > 0:
            scores.append((score, bien))

    scores.sort(key=lambda pair: pair[0], reverse=True)
    return [serialize_bien(bien) for _, bien in scores[:limit]]


def suggerer_zones(ville, budget_max=None, type_bien=None, limit=5):
    """Module 5 : propose des zones voisines pertinentes quand une commune est trop chère/vide.

    Réutilise get_adjacent_zones (module 1) au lieu de dupliquer la liste de voisinage,
    puis classe les voisins par nombre de résultats disponibles (le plus d'offres en premier).
    """
    zones_voisines = get_adjacent_zones(ville)
    if not zones_voisines:
        return []

    suggestions = []
    for zone in zones_voisines:
        qs = Bien.objects.filter(statut="disponible", ville__icontains=zone)
        if budget_max:
            qs = qs.filter(prix__lte=budget_max)
        if type_bien:
            qs = qs.filter(type__icontains=type_bien)
        nb_resultats = qs.count()
        if nb_resultats == 0:
            continue
        prix_moyen = qs.order_by("prix")[nb_resultats // 2].prix if nb_resultats else None
        suggestions.append(
            {
                "ville": zone,
                "nb_resultats": nb_resultats,
                "prix_moyen": str(prix_moyen) if prix_moyen is not None else None,
                "raison": f"Zone proche de {ville}, prix comparable",
            }
        )

    suggestions.sort(key=lambda s: s["nb_resultats"], reverse=True)
    return suggestions[:limit]


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
def build_base_reply(criteria, logements, en_fallback):
    """Réponse de secours utilisée quand l'appel a Groq échoue (jamais de réponse vide)."""
    budget_max = criteria.get("budget_max")
    ville = criteria.get("ville")

    if budget_max and budget_max <= 100000 and not ville:
        base_reply = "Avec ce budget, je vous recommande Bouaké, Yamoussoukro, Daloa ou Korhogo."
    elif budget_max and budget_max <= 150000:
        base_reply = "Avec ce budget, ciblez des quartiers abordables ou des villes secondaires."
    else:
        base_reply = "Je peux vous aider à trouver un bien adapté à votre budget et à votre zone préférée."

    if ville:
        base_reply = f"J'ai compris que vous cherchez autour de {ville}. {base_reply}"

    if logements and not en_fallback:
        base_reply = f"{base_reply} J'ai trouvé {len(logements)} logement(s) correspondant à votre demande."
    elif logements and en_fallback:
        base_reply = (
            f"{base_reply} Je n'ai pas de correspondance exacte, "
            f"voici {len(logements)} alternative(s) intéressante(s)."
        )

    return base_reply


def chat_immobilier(message, history=None, lat=None, lng=None):
    """Assistant IA unique (fusion des anciennes v1/v2/v3).

    La recherche de biens (et donc toute mention de biens/prix dans la réponse) ne se
    déclenche que si le message contient une vraie intention de recherche (ville, budget,
    type de logement...). Un simple "Bonjour" reçoit une réponse conversationnelle, jamais
    une liste de biens - y compris d'éventuelles données de test présentes en base.

    Toujours une réponse utile même si l'appel Groq échoue : `reponse` retombe
    sur `base_reply`, construit à partir de vrais biens (search fallback).
    """
    history = history or []
    criteria = extract_search_criteria({"texte": message})
    recherche_demandee = has_search_intent(criteria)

    if recherche_demandee:
        logements, en_fallback, niveau = filtrer_biens_intelligemment(criteria)
        if lat and lng:
            logements = filter_points_by_radius(logements, float(lat), float(lng), 5)
        base_reply = build_base_reply(criteria, logements, en_fallback)
    else:
        logements, en_fallback = [], False
        base_reply = (
            "Bonjour ! Je suis LOGI, votre assistant immobilier LogeCiv. "
            "Que recherchez-vous : un studio, un appartement, une villa ? "
            "Dans quelle ville ou quel quartier, et avec quel budget ?"
        )

    context = {
        "recherche_demandee": recherche_demandee,
        "logements": logements[:8],
        "nb_resultats": len(logements),
        "en_fallback": en_fallback,
    }
    messages = [{"role": "system", "content": LOGI_SYSTEM_PROMPT}]
    for h in history[-10:]:
        messages.append(h)
    messages.append({"role": "user", "content": f"Context: {json.dumps(context, ensure_ascii=False)}\nMsg: {message}"})

    ai_text, _ = call_ai(messages)
    reply = ai_text or base_reply

    return {
        "message": message,
        "reply": reply,
        "reponse": reply,
        "logements": logements,
        "resultats": logements,
        "en_fallback": en_fallback,
        "recherche_demandee": recherche_demandee,
        "criteres": criteria,
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


search_biens_intelligente = search_biens_intelligente_v2


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
