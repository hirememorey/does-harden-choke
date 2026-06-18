"""Causal chain Step 3 — Regression models for mechanism → team outcomes.

Primary: continuous fga_retention predicting team ORtg in floor games.
Secondary: FTA retention, win probability, cross-player mechanism, gradient axis.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

OUTPUT_PATH = config.PROCESSED_DIR / "mechanism_model_results.csv"
ROBUSTNESS_PATH = config.PROCESSED_DIR / "mechanism_model_robustness.csv"

BASE_CONTROLS = "game_score + opponent_defrtg + is_playoff + minutes + C(player_name) + C(season)"
CLUSTER_KWDS = {"cov_type": "cluster", "cov_kwds": {"groups": None}}


def load_floor_games(min_floor_games: int = 5) -> pd.DataFrame:
    path = config.PROCESSED_DIR / "causal_analysis_table.csv"
    df = pd.read_csv(path)
    floor = df[df["is_floor_primary"] == True].copy()
    floor["is_playoff"] = floor["is_playoff"].astype(int)

    counts = floor.groupby("player_name").size()
    keep_players = counts[counts >= min_floor_games].index
    dropped = sorted(set(floor["player_name"]) - set(keep_players))
    if dropped:
        logger.info(
            "Dropping %d players with <%d floor games: %s",
            len(dropped),
            min_floor_games,
            ", ".join(dropped),
        )
    floor = floor[floor["player_name"].isin(keep_players)].copy()

    floor["mechanism_shrinker"] = (floor["mechanism"] == "shrinker").astype(int)
    return floor.dropna(subset=["team_off_rating", "game_score", "fga_retention", "opponent_defrtg"])


def fit_ols(formula: str, data: pd.DataFrame, label: str) -> tuple[object, pd.Series]:
    model = smf.ols(formula, data=data).fit()
    try:
        model = model.get_robustcov_results(cov_type="cluster", groups=data["player_name"])
    except (ValueError, np.linalg.LinAlgError):
        logger.warning("%s: cluster SE failed — using HC1", label)
        model = model.get_robustcov_results(cov_type="HC1")
    return model, summarize_key_coefs(model, label)


def fit_logit(formula: str, data: pd.DataFrame, label: str) -> tuple[object, pd.Series]:
    try:
        model = smf.logit(formula, data=data).fit(
            disp=0,
            cov_type="cluster",
            cov_kwds={"groups": data["player_name"]},
        )
    except (ValueError, np.linalg.LinAlgError):
        logger.warning("%s: cluster SE failed — using default SE", label)
        model = smf.logit(formula, data=data).fit(disp=0)
    return model, summarize_key_coefs(model, label)


def _coef_series(model) -> pd.Series:
    params = model.params
    if isinstance(params, pd.Series):
        return params
    names = list(getattr(model.model, "exog_names", []))
    if len(names) != len(params):
        names = [f"x{i}" for i in range(len(params))]
    return pd.Series(params, index=names)


def _pvalue_series(model) -> pd.Series:
    pvalues = model.pvalues
    if isinstance(pvalues, pd.Series):
        return pvalues
    names = list(getattr(model.model, "exog_names", []))
    if len(names) != len(pvalues):
        names = [f"x{i}" for i in range(len(pvalues))]
    return pd.Series(pvalues, index=names)


def _bse_series(model) -> pd.Series:
    bse = model.bse
    if isinstance(bse, pd.Series):
        return bse
    names = list(getattr(model.model, "exog_names", []))
    if len(names) != len(bse):
        names = [f"x{i}" for i in range(len(bse))]
    return pd.Series(bse, index=names)


def summarize_key_coefs(model, label: str) -> pd.Series:
    """Extract the focal coefficient(s) for the results table."""
    params = _coef_series(model)
    pvalues = _pvalue_series(model)
    bse = _bse_series(model)

    focal_terms = [
        "fga_retention", "fta_retention", "player_gradient",
        "mechanism_shrinker", "rim_abandonment_index",
    ]
    term = next((t for t in focal_terms if t in params.index), None)
    if term is None:
        return pd.Series({
            "model": label,
            "term": None,
            "coef": np.nan,
            "se": np.nan,
            "pvalue": np.nan,
            "n_obs": int(model.nobs),
            "r_squared": getattr(model, "rsquared", np.nan),
        })

    return pd.Series({
        "model": label,
        "term": term,
        "coef": float(params[term]),
        "se": float(bse[term]),
        "pvalue": float(pvalues[term]),
        "n_obs": int(model.nobs),
        "r_squared": getattr(model, "rsquared", np.nan),
    })


def interpret_fga(coef: float, pvalue: float) -> str:
    if pvalue >= 0.05:
        return "H3 — mechanism does not predict team ORtg (null)"
    if coef > 0:
        return "H1 — higher retention (forcing) predicts better team ORtg (contraction worse)"
    return "H2 — higher retention (forcing) predicts worse team ORtg (forcing worse)"


def run_primary_models(floor: pd.DataFrame) -> list[pd.Series]:
    results = []

    print("=" * 70)
    print("CAUSAL CHAIN STEP 3 — REGRESSION MODELS")
    print("=" * 70)
    print(f"\nFloor games in sample: {len(floor)} ({floor['player_name'].nunique()} players)\n")

    # Model 1: Primary — FGA retention
    formula1 = f"team_off_rating ~ fga_retention + {BASE_CONTROLS}"
    m1, r1 = fit_ols(formula1, floor, "M1_primary_fga_retention")
    results.append(r1)
    print("=== Model 1: team_off_rating ~ fga_retention + controls + player/season FE ===")
    print(f"  fga_retention: β={r1['coef']:.3f}, SE={r1['se']:.3f}, p={r1['pvalue']:.4f}")
    print(f"  R²={r1['r_squared']:.3f}, n={r1['n_obs']}")
    print(f"  → {interpret_fga(r1['coef'], r1['pvalue'])}\n")

    # Model 2: Win probability
    formula2 = f"team_win ~ fga_retention + {BASE_CONTROLS}"
    m2, r2 = fit_logit(formula2, floor, "M2_win_probability")
    results.append(r2)
    print("=== Model 2: team_win ~ fga_retention + controls (logit) ===")
    print(f"  fga_retention: β={r2['coef']:.3f}, SE={r2['se']:.3f}, p={r2['pvalue']:.4f}")
    print(f"  n={r2['n_obs']}\n")

    # Model 3: FTA retention
    fta_floor = floor.dropna(subset=["fta_retention"])
    formula3 = f"team_off_rating ~ fta_retention + {BASE_CONTROLS}"
    m3, r3 = fit_ols(formula3, fta_floor, "M3_fta_retention")
    results.append(r3)
    print("=== Model 3: team_off_rating ~ fta_retention + controls ===")
    print(f"  fta_retention: β={r3['coef']:.3f}, SE={r3['se']:.3f}, p={r3['pvalue']:.4f}")
    print(f"  R²={r3['r_squared']:.3f}, n={r3['n_obs']}\n")

    # Model 4: Cross-player mechanism (descriptive, no player FE)
    formula4 = (
        "team_off_rating ~ mechanism_shrinker + game_score + opponent_defrtg "
        "+ is_playoff + minutes + C(season)"
    )
    m4 = smf.ols(formula4, data=floor).fit(cov_type="HC1")
    r4 = summarize_key_coefs(m4, "M4_cross_player_shrinker")
    results.append(r4)
    print("=== Model 4: Cross-player shrinker indicator (descriptive, no player FE) ===")
    print(f"  mechanism_shrinker: β={r4['coef']:.3f}, SE={r4['se']:.3f}, p={r4['pvalue']:.4f}")
    print(f"  R²={r4['r_squared']:.3f}, n={r4['n_obs']}")
    print("  (Confounded by team/system/era — illustrative only)\n")

    # Model 5: Gradient axis (Swiss cheese)
    grad_floor = floor.dropna(subset=["player_gradient"])
    formula5 = f"team_off_rating ~ player_gradient + fga_retention + {BASE_CONTROLS}"
    m5, r5 = fit_ols(formula5, grad_floor, "M5_gradient_axis")
    results.append(r5)
    print("=== Model 5: team_off_rating ~ player_gradient + fga_retention + controls ===")
    print(f"  player_gradient: β={r5['coef']:.3f}, SE={r5['se']:.3f}, p={r5['pvalue']:.4f}")
    if "fga_retention" in _coef_series(m5).index:
        print(
            f"  fga_retention:   β={_coef_series(m5)['fga_retention']:.3f}, "
            f"p={_pvalue_series(m5)['fga_retention']:.4f}"
        )
    print(f"  R²={r5['r_squared']:.3f}, n={r5['n_obs']}\n")

    # Model 6: Rim abandonment index
    rim_floor = floor.dropna(subset=["rim_abandonment_index"])
    formula6 = f"team_off_rating ~ rim_abandonment_index + {BASE_CONTROLS}"
    m6, r6 = fit_ols(formula6, rim_floor, "M6_rim_abandonment")
    results.append(r6)
    print("=== Model 6: team_off_rating ~ rim_abandonment_index + controls ===")
    print(f"  rim_abandonment: β={r6['coef']:.3f}, SE={r6['se']:.3f}, p={r6['pvalue']:.4f}")
    print(f"  R²={r6['r_squared']:.3f}, n={r6['n_obs']}\n")

    return results


def run_robustness(floor: pd.DataFrame) -> list[pd.Series]:
    """Robustness checks on the primary FGA retention specification."""
    formula = f"team_off_rating ~ fga_retention + {BASE_CONTROLS}"
    checks = [
        ("R1_close_games", floor[floor["team_plus_minus"].abs() <= 15]),
        ("R2_minutes_25plus", floor[floor["minutes"] >= 25]),
        ("R3_playoff_only", floor[floor["is_playoff"] == 1]),
        ("R4_no_injury_flag", floor[floor["is_injury_flagged"] == False]),
    ]

    results = []
    print("=== Robustness Checks (primary specification) ===")
    for label, subset in checks:
        if len(subset) < 50:
            logger.warning("%s: only %d obs — skipping", label, len(subset))
            continue
        _, row = fit_ols(formula, subset, label)
        results.append(row)
        print(
            f"  {label}: β={row['coef']:.3f}, p={row['pvalue']:.4f}, n={row['n_obs']}"
        )

    harden = floor[floor["player_name"] == "James Harden"]
    if len(harden) >= 15:
        m = smf.ols(
            "team_off_rating ~ fga_retention + game_score + opponent_defrtg + is_playoff + minutes + C(season)",
            data=harden,
        ).fit()
        row = summarize_key_coefs(m, "R5_harden_only")
        results.append(row)
        print(
            f"  R5_harden_only: β={row['coef']:.3f}, p={row['pvalue']:.4f}, n={row['n_obs']}"
        )
    print()
    return results


def main() -> None:
    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    floor = load_floor_games()
    primary_results = run_primary_models(floor)
    robustness_results = run_robustness(floor)

    primary_df = pd.DataFrame(primary_results)
    robustness_df = pd.DataFrame(robustness_results)

    primary_df.to_csv(OUTPUT_PATH, index=False)
    robustness_df.to_csv(ROBUSTNESS_PATH, index=False)
    logger.info("Wrote %s (%d models)", OUTPUT_PATH, len(primary_df))
    logger.info("Wrote %s (%d checks)", ROBUSTNESS_PATH, len(robustness_df))

    print("=== Kill Decision Summary ===")
    m1 = primary_df[primary_df["model"] == "M1_primary_fga_retention"].iloc[0]
    m5 = primary_df[primary_df["model"] == "M5_gradient_axis"].iloc[0]
    fga_sig = m1["pvalue"] < 0.05
    grad_sig = m5["pvalue"] < 0.05
    if not fga_sig and not grad_sig:
        print("  Both fga_retention and player_gradient null → descriptive-only contribution")
        print("  Pivot to paper on trait stability + opponent adjustment + honest negatives")
    elif fga_sig:
        print(f"  fga_retention significant (p={m1['pvalue']:.4f}) → mechanism matters for team outcomes")
        print("  Proceed to architecture-prediction model with causal motivation")
    elif grad_sig:
        print(f"  player_gradient significant (p={m5['pvalue']:.4f}) → opponent-sensitivity axis matters")
        print("  Swiss cheese framing survives as continuous spectrum")


if __name__ == "__main__":
    main()
