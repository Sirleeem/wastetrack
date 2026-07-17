"""Lightweight route optimization: priority + Haversine nearest-neighbour."""

from __future__ import annotations

import math
from typing import Iterable, List, Sequence, Tuple

URGENCY_WEIGHT = {"high": 0, "medium": 1, "low": 2}


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two points in kilometres."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def nearest_neighbour_order(
    points: Sequence[Tuple[int, float, float, str]],
    start: Tuple[float, float] | None = None,
) -> Tuple[List[int], float]:
    """
    Order report points using urgency-first clusters then nearest neighbour.

    points: sequence of (report_id, lat, lon, urgency)
    Returns ordered report ids and total estimated path distance (km).
    """
    if not points:
        return [], 0.0

    remaining = list(points)
    # Sort by urgency so high-priority points are preferred as seed when equidistant
    remaining.sort(key=lambda p: URGENCY_WEIGHT.get((p[3] or "medium").lower(), 1))

    if start is None:
        # Start from highest urgency (already first after sort)
        current_lat, current_lon = remaining[0][1], remaining[0][2]
        ordered = [remaining.pop(0)]
    else:
        current_lat, current_lon = start
        ordered = []

    total = 0.0
    while remaining:
        # Prefer nearby high-urgency points: score = distance + urgency penalty
        best_idx = 0
        best_score = float("inf")
        best_dist = 0.0
        for i, (rid, lat, lon, urg) in enumerate(remaining):
            dist = haversine_km(current_lat, current_lon, lat, lon)
            penalty = URGENCY_WEIGHT.get((urg or "medium").lower(), 1) * 0.15
            score = dist + penalty
            if score < best_score:
                best_score = score
                best_idx = i
                best_dist = dist
        chosen = remaining.pop(best_idx)
        total += best_dist
        ordered.append(chosen)
        current_lat, current_lon = chosen[1], chosen[2]

    return [p[0] for p in ordered], round(total, 3)


def order_reports(reports: Iterable, depot: Tuple[float, float] | None = None) -> Tuple[List, float]:
    """
    Take ORM Report objects, return (ordered_reports, distance_km).
    """
    reports = list(reports)
    if not reports:
        return [], 0.0

    points = [(r.id, r.latitude, r.longitude, r.urgency or "medium") for r in reports]
    ordered_ids, distance = nearest_neighbour_order(points, start=depot)
    by_id = {r.id: r for r in reports}
    return [by_id[i] for i in ordered_ids], distance


def manual_path_distance(reports: Sequence) -> float:
    """Sum sequential distances for a given report order (manual baseline)."""
    if len(reports) < 2:
        return 0.0
    total = 0.0
    for a, b in zip(reports, reports[1:]):
        total += haversine_km(a.latitude, a.longitude, b.latitude, b.longitude)
    return round(total, 3)
