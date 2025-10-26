import os
from typing import Any, Dict, List, Optional
import httpx
from urllib.parse import quote

GOOGLE_PLACES_TEXTSEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
GOOGLE_PLACES_DETAILS_URL = "https://places.googleapis.com/v1/places/{place_id}"


def _get_api_key() -> str:
    key = os.getenv("EXPO_PUBLIC_GOOGLE_MAPS_API_KEY") or os.getenv("GOOGLE_MAPS_API_KEY")
    if not key:
        raise RuntimeError("Falta EXPO_PUBLIC_GOOGLE_MAPS_API_KEY en el entorno del MCP.")
    return key


def _headers(api_key: str, field_mask: Optional[str] = None) -> Dict[str, str]:
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
    }
    if field_mask:
        headers["X-Goog-FieldMask"] = field_mask
    return headers


def _fetch_details(api_key: str, place_id: str) -> Dict[str, Any]:
    mask = ",".join([
        "id",
        "displayName",
        "formattedAddress",
        "location",
        "googleMapsUri",
        "websiteUri",
        "internationalPhoneNumber",
        "nationalPhoneNumber",
    ])
    url = GOOGLE_PLACES_DETAILS_URL.format(place_id=place_id)
    with httpx.Client(timeout=20.0) as client:
        r = client.get(url, headers=_headers(api_key, mask))
        r.raise_for_status()
        return r.json()


def search_places(query: str, lat: Optional[float] = None, lng: Optional[float] = None, radius_m: int = 5000, limit: int = 5) -> Dict[str, Any]:
    api_key = _get_api_key()
    mask = ",".join([
        "places.id",
        "places.displayName",
        "places.formattedAddress",
        "places.location",
        "places.googleMapsUri",
    ])

    payload: Dict[str, Any] = {"textQuery": query}
    if lat is not None and lng is not None:
        payload["locationBias"] = {
            "circle": {
                "center": {"latitude": float(lat), "longitude": float(lng)},
                "radius": float(radius_m),
            }
        }

    with httpx.Client(timeout=20.0) as client:
        r = client.post(GOOGLE_PLACES_TEXTSEARCH_URL, json=payload, headers=_headers(api_key, mask))
        r.raise_for_status()
        data = r.json()

    places = data.get("places", [])[:limit]
    results: List[Dict[str, Any]] = []

    for p in places:
        pid = p.get("id")
        name = None
        dn = p.get("displayName")
        if isinstance(dn, dict):
            name = dn.get("text")
        else:
            name = dn
        address = p.get("formattedAddress")
        loc = p.get("location") or {}
        latlng = (loc.get("latitude"), loc.get("longitude"))
        maps_url = p.get("googleMapsUri")

        phone = None
        try:
            if pid:
                details = _fetch_details(api_key, pid)
                phone = details.get("nationalPhoneNumber") or details.get("internationalPhoneNumber")
                maps_url = details.get("googleMapsUri") or maps_url
                if details.get("location"):
                    latlng = (
                        details["location"].get("latitude", latlng[0]),
                        details["location"].get("longitude", latlng[1]),
                    )
        except Exception:
            # No fallamos si details falla
            pass

        # Construir deep link para la app
        def q(v: Optional[Any]) -> str:
            if v is None:
                return ""
            return quote(str(v), safe="")

        deep_link = f"fiscai://place?name={q(name)}&address={q(address)}&lat={q(latlng[0])}&lng={q(latlng[1])}&placeId={q(pid)}&phone={q(phone)}"

        results.append({
            "name": name,
            "address": address,
            "lat": latlng[0],
            "lng": latlng[1],
            "placeId": pid,
            "phone": phone,
            "mapsUrl": maps_url,
            "deepLink": deep_link,
        })

    return {"query": query, "results": results}
