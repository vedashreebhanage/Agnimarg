"""INTAKE — source validation on inbound hotspot data.

Answers the original security audit's Tier-1 finding #5 ("No source
validation on inbound data ... a single spoofed or faulty weather/hotspot
feed can trigger a false threat cone unchecked") with real clustering logic,
not just a description.

Mirrors the clustering approach in the master blueprint (Section 8: DBSCAN,
eps=1000m, min_samples=2) without adding scikit-learn as a dependency — this
is single-linkage distance clustering, which is the same idea DBSCAN reduces
to for this scale of data (a few dozen points, not millions).

A cluster of 2+ corroborating hotspot points becomes a "confirmed" event that
SENTINEL is allowed to act on. A lone, uncorroborated point is flagged rather
than silently trusted — exactly the gap the audit called out.
"""
import math

EARTH_RADIUS_KM = 6371.0


def _haversine_km(a: dict, b: dict) -> float:
    lat1, lon1, lat2, lon2 = map(math.radians, [a["lat"], a["lon"], b["lat"], b["lon"]])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(h))


def cluster_hotspots(hotspots: list, eps_km: float = 1.0) -> list:
    """Single-linkage distance clustering: two points are in the same cluster
    if within eps_km of each other, transitively. Returns a list of clusters
    (each a list of hotspot dicts), in the input order of each cluster's first
    member."""
    n = len(hotspots)
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i, j):
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[ri] = rj

    for i in range(n):
        for j in range(i + 1, n):
            if _haversine_km(hotspots[i], hotspots[j]) <= eps_km:
                union(i, j)

    clusters_by_root: dict[int, list] = {}
    for i, h in enumerate(hotspots):
        clusters_by_root.setdefault(find(i), []).append(h)
    return list(clusters_by_root.values())


def corroborate(hotspots: list, eps_km: float = 1.0, min_samples: int = 2) -> dict:
    """Splits hotspots into confirmed (corroborated by >= min_samples nearby
    points) vs. unconfirmed (isolated single reports). Only confirmed points
    should feed SENTINEL's threat-cone generation."""
    clusters = cluster_hotspots(hotspots, eps_km=eps_km)
    confirmed, unconfirmed = [], []
    for cluster in clusters:
        target = confirmed if len(cluster) >= min_samples else unconfirmed
        target.extend(cluster)
    return {"confirmed": confirmed, "unconfirmed": unconfirmed, "cluster_count": len(clusters)}
