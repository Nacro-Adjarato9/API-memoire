import json
import re
import unicodedata

import requests
from requests.exceptions import RequestException
from django.conf import settings

from biens.models import Bien


ALTERNATIVE_ZONES = {
    "cocody riviera golf": ["Riviera Palmeraie", "Angré", "Bingerville"],
    "cocody": ["Angré", "Riviera Palmeraie", "Bingerville"],
    "marcory": ["Zone 4", "Biétry", "Treichville"],
    "plateau": ["Treichville", "Adjamé", "Koumassi"],
    "yopougon": ["Niangon", "Azito", "Gesco"],
    "abobo": ["Anyama", "N'dotré", "Adjamé"],
    "angre": ["Cocody", "Riviera Palmeraie", "Bingerville"],
    "bingerville": ["Cocody", "Riviera", "Angré"],
    "treichville": ["Marcory", "Plateau", "Koumassi"],
}

CITY_SUGGESTIONS = [
    "Bouaké",
    "Yamoussoukro",
    "Daloa",
    "Korhogo",
    "San Pedro",
    "Man",
    "Gagnoa",
    "Abengourou",
    "Aboisso",
]


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
        return None, f"HTTP {response.status_code}: {response.text or response.reason}"

    try:
        payload = response.json()
        return payload["choices"][0]["message"]["content"], None
    except (ValueError, KeyError, TypeError) as exc:
        return None, f"Invalid AI response format: {exc}"


def extract_budget(text):
    if not text:
        return None
    numbers = [int(match.replace(" ", "")) for match in re.findall(r"\b\d[\d ]*\b", text)]
    return numbers[-1] if numbers else None


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

    alternative_villes = ALTERNATIVE_ZONES.get(ville_norm, [])
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
    return "Voici les meilleures alternatives disponibles selon vos critères."


def search_biens_intelligente(data):
    criteria = extract_search_criteria(data)
    resultats = [serialize_bien(bien) for bien in build_bien_queryset(criteria)[:10]]

    if resultats:
        budget_note = (
            f" avec un budget max de {criteria['budget_max']} FCFA"
            if criteria.get("budget_max")
            else ""
        )
        ai_message = (
            f"Voici des logements correspondant à votre recherche{budget_note}."
        )
        prompt = (
            "Tu es un assistant immobilier en Côte d'Ivoire. Résume brièvement les résultats de recherche "
            f"suivants en français simple : {json.dumps(resultats[:5], ensure_ascii=False)}"
        )
        ai_text, _ = call_ai(
            [
                {"role": "system", "content": "Tu aides à rechercher des logements immobiliers en Côte d'Ivoire."},
                {"role": "user", "content": prompt},
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
            "suggestions": [],
        }

    suggestions = build_alternatives(criteria, limit=5)
    message = explain_alternatives(criteria, suggestions)
    prompt = (
        "Tu es un assistant immobilier en Côte d'Ivoire. Explique pourquoi ces alternatives sont pertinentes, "
        f"puis propose brièvement la meilleure option : {json.dumps(suggestions[:5], ensure_ascii=False)}"
    )
    ai_text, _ = call_ai(
        [
            {"role": "system", "content": "Tu aides à proposer des alternatives immobilières utiles et réalistes."},
            {"role": "user", "content": prompt},
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
        "suggestions": suggestions,
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


def verify_document(document_type, document_url):
    prompt = (
        "Tu es un expert en immobilier en Côte d'Ivoire. Vérifie la cohérence d'un document soumis pour une transaction immobilière. "
        f"Type de document: {document_type}. URL: {document_url}. "
        "Retourne un JSON avec verdict, confiance, message, details."
    )
    ai_text, ai_error = call_ai(
        [
            {"role": "system", "content": "Tu es un assistant de vérification de documents immobiliers."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=250,
        temperature=0.2,
    )

    def fallback():
        verdict = "Document suspect"
        confidence = 60
        message = "Le document semble incohérent ou incomplet. Une vérification manuelle est recommandée."
        details = {
            "type_detecte": document_type,
            "qualite": "Non évaluée",
            "authentique": False,
            "recommandations": "Vérification manuelle conseillée.",
        }
        if any(keyword in normalize_text(document_url) for keyword in ["cni", "passeport", "rccm", "propriete"]):
            verdict = "Document valide"
            confidence = 70
            message = "Le document semble cohérent, mais une vérification complémentaire est recommandée."
            details["authentique"] = True
            details["qualite"] = "Potentiellement valide"
        return verdict, confidence, message, details

    if ai_text:
        try:
            parsed = json.loads(ai_text)
            if isinstance(parsed, dict):
                verdict = parsed.get("verdict", "Document suspect")
                confidence = int(parsed.get("confidence", parsed.get("confiance", 60)))
                message = parsed.get("message", "Vérification réalisée, mais des doutes subsistent.")
                details = parsed.get("details", {
                    "type_detecte": document_type,
                    "qualite": "Non évaluée",
                    "authentique": False,
                    "recommandations": "Vérification manuelle conseillée.",
                })
                return {
                    "verdict": verdict,
                    "confidence": confidence,
                    "message": message,
                    "details": details,
                    "ai_analysis": ai_text,
                }
        except (ValueError, TypeError):
            pass

    verdict, confidence, message, details = fallback()
    return {
        "verdict": verdict,
        "confidence": confidence,
        "message": message,
        "details": details,
        "ai_analysis": ai_text or f"AI unavailable: {ai_error}" if ai_error else "Aucune analyse IA disponible.",
    }
