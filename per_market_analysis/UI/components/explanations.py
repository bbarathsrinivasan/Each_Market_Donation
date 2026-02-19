"""Explanations and descriptions for each plot type."""

BASIC_DONATION_EXPLANATION = {
    "what": "Shows cumulative donation ratio (Dem/(Dem+Rep)) over time, with Polymarket prices overlaid on the same 0-1 axis.",
    "calculation": (
        "For each period (day/week/month), sum all DEM and REP donations from the start through that period (cumulative). "
        "Dem_Ratio = Cumulative_DEM / (Cumulative_DEM + Cumulative_REP). "
        "Polymarket prices are aggregated to the same periods by taking the last price in each period."
    ),
    "data_source": (
        "- Donation data: `{slug}/output/{freq}_cumulative_aggregations.csv` (Segment=All)\n"
        "- Polymarket prices: `{slug}/polymarket_prices.csv`"
    ),
    "interpretation": (
        "Each point shows: 'Of all donations made from the start through this period, what fraction went to Democrats?' "
        "The Polymarket price line shows the market's implied probability for the Democrat outcome at the end of each period."
    ),
}

CUMULATIVE_SEGMENTS_EXPLANATION = {
    "what": "Cumulative donation ratios broken down by donor segment (Small/Medium/Large based on cumulative donation amounts).",
    "calculation": (
        "Donors are segmented by 33.3rd and 66.6th percentiles of cumulative donation amounts:\n"
        "- Small = bottom 33.3% of donors\n"
        "- Medium = 33.3-66.6% of donors\n"
        "- Large = top 33.3% of donors\n\n"
        "Each segment's Dem_Ratio is calculated separately using cumulative donations from that segment only. "
        "For each period, sum DEM and REP donations from the start through that period for each segment."
    ),
    "data_source": "`{slug}/output/{freq}_cumulative_aggregations.csv` (all segments: All, Small, Medium, Large)",
    "interpretation": (
        "Shows how donation sentiment differs across donor segments over time. "
        "All segments use cumulative calculations (running totals from the start)."
    ),
}

NON_CUMULATIVE_SEGMENTS_EXPLANATION = {
    "what": "Period-specific donation ratios (no carry-forward) broken down by donor segment.",
    "calculation": (
        "For each period (day/week/month), sum DEM and REP donations in that period only (no cumulative sum). "
        "Dem_Ratio = Period_DEM / (Period_DEM + Period_REP). "
        "Calculated separately per segment (Small/Medium/Large)."
    ),
    "data_source": "`{slug}/non_cumulative_donations/output/{freq}_non_cumulative_aggregations.csv` (all segments)",
    "interpretation": (
        "Shows donation sentiment per period, not running totals. "
        "Useful for identifying periods with high/low Democratic support without the cumulative effect. "
        "More volatile than cumulative ratios but shows period-specific trends."
    ),
    "difference": "Unlike cumulative ratios, this shows donation sentiment per period only, with no carry-forward from previous periods.",
}

SUMMARY_ANALYSIS_EXPLANATION = {
    "what": (
        "Combined view of all four signals: donation-based (cumulative and non-cumulative) "
        "and prediction-market-based (cumulative from trades, non-cumulative from Polymarket prices)."
    ),
    "lines": {
        "donation_cumulative": {
            "description": "Cumulative Dem_Ratio from start through each period",
            "calculation": "Sum DEM and REP donations from start through period. Dem_Ratio = Cumulative_DEM / (Cumulative_DEM + Cumulative_REP).",
            "data_source": "`{slug}/output/{freq}_cumulative_aggregations.csv` (Segment=All)",
        },
        "prediction_cumulative": {
            "description": "Investment-weighted odds from blockchain trades, aggregated across all users, cumulative positions",
            "calculation": (
                "For each user and day: cumulative positions (running sum of net tokens), individual YES/NO exposure derived. "
                "Aggregated across all users: agg_yes / (agg_yes + agg_no). "
                "Forward-filled when missing periods."
            ),
            "data_source": "`trades_Plot/{slug}/{market_id}_all_users_segment.csv`",
        },
        "donation_non_cumulative": {
            "description": "Period-specific Dem_Ratio (no carry-forward)",
            "calculation": "Sum DEM and REP donations in that period only. Dem_Ratio = Period_DEM / (Period_DEM + Period_REP).",
            "data_source": "`{slug}/non_cumulative_donations/output/{freq}_non_cumulative_aggregations.csv` (Segment=All)",
        },
        "prediction_non_cumulative": {
            "description": "Polymarket price for Democrat outcome at end of period",
            "calculation": "Last Polymarket price for Democrat outcome in each period (no cumulation).",
            "data_source": "`{slug}/polymarket_prices.csv` (aggregated by period, Democrat outcome selected)",
        },
    },
    "interpretation": (
        "Compare donation-based signals (blue/green) with prediction-market signals (red/purple). "
        "Cumulative lines show running totals; non-cumulative lines show period-specific values."
    ),
}

USER_ANALYSIS_EXPLANATION = {
    "what": (
        "Investment-weighted prediction odds from blockchain trades, compared to Polymarket price-based odds. "
        "Shows how different user segments (by cumulative donation amount) predict outcomes."
    ),
    "calculation": (
        "For each user and day (by day_offset relative to market close):\n"
        "1. Net tokens (buys - sells) per user per outcome (YES/NO) are summed by day\n"
        "2. Cumulative position = running sum of net tokens over time (carried forward on no-trade days)\n"
        "3. Individual exposure to YES and NO is derived from cumulative positions\n"
        "4. Aggregated across users in segment: agg_yes / (agg_yes + agg_no)\n\n"
        "Users are segmented by their cumulative donation amounts (same percentiles as donation segments)."
    ),
    "x_axis": "Day offset: 0 = closing day, negative = days before closing",
    "data_source": (
        "- Trade odds: `trades_Plot/{slug}/{market_id}_{segment}_segment.csv`\n"
        "- Price odds: `{slug}/polymarket_prices.csv` (aggregated by day_offset)"
    ),
    "interpretation": (
        "Compare investment-weighted odds from actual trades (colored lines) with Polymarket price-based odds (blue). "
        "Shows whether different donor segments have different prediction accuracy or timing."
    ),
}
