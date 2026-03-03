def get_population_severity_scoring(
    current_avg_provider_per_100k: float, target_avg_provider_per_100k: float
) -> tuple[str, str]:
    """Determine severity scoring based on provider ratios and provide rationale"""
    if current_avg_provider_per_100k < 0.5 * target_avg_provider_per_100k:
        return (
            "Underserved - High Priority",
            "Current provider ratio is < 50% of the target, indicating a significant shortage.",
        )
    elif current_avg_provider_per_100k < 0.8 * target_avg_provider_per_100k:
        return (
            "Moderate Gap",
            "Current provider ratio is between 50% and 80% of the target, indicating a moderate gap.",
        )
    else:
        return (
            "Saturated",
            "Current provider ratio is >= 80% of the target, indicating saturation.",
        )


def get_anchor_cpt_severity_scoring(
    target_anchor_visits_count: int,
    actual_anchor_visits_count: int,
) -> tuple[int, str, str]:
    """Determine severity scoring based on anchor CPT counts and provide rationale"""
    visits_diff = int(actual_anchor_visits_count - target_anchor_visits_count)
    # If actual visits are less than target visits, then it means that current providers are enough to handle the demand
    # If actual visits are more than target visits, then it means that there is a gap in the market
    capacity_percent = round((actual_anchor_visits_count / target_anchor_visits_count) * 100, 1)
    print(
        f"CPT Stats: Target={target_anchor_visits_count}, "
        f"Actual={actual_anchor_visits_count} visits_diff={visits_diff} "
        f"capacity_percent={capacity_percent}%"
    )
    print(f"Anchor CPT visits capacity percent: {capacity_percent}%")
    if visits_diff < 0:
        return (
            visits_diff,
            "Low Potential / High Risk",
            f"""Competition at {capacity_percent}% capacity with {abs(visits_diff):,}"""
            + """ "empty chair" visits available. """
            + "Existing surplus creates high risk for a new entrant.",
        )
    elif visits_diff == 0:
        return (
            visits_diff,
            "Balanced Market",
            "Market is balanced with no surplus or deficit in anchor CPT visits.",
        )
    else:
        return (
            visits_diff,
            "High Potential",
            f"""Market at {capacity_percent}% capacity with {visits_diff:,} visits exceeding benchmarks. """
            + "This overflow creates a clear entry point for a new office.",
        )
