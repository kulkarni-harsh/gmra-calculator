def get_google_places_keywords(specialty_lookup: dict, specialty_name: str) -> list[str]:
    """
    Return the list of Google Places search keywords for a given specialty name.
    Falls back to [specialty_name] if the specialty isn't found in the lookup or has
    no keywords, so callers always get at least one keyword to search.
    """
    needle = specialty_name.strip().lower()
    for entry in specialty_lookup.values():
        if entry.get("description", "").strip().lower() == needle:
            keywords = entry.get("google_places_keywords", [])
            return keywords if keywords else [specialty_name]
    return [specialty_name]
