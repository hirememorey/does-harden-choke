"""Trigger Sensitivity, Null Model, Bayesian Classification, and Bootstrap CIs.

Phase A validation: kill the taxonomy or prove it's real.

A1: Threshold sensitivity — parameterize classify_trigger(), run across
    threshold grid, identify swing players, build heatmap.
A2: Null model — permute is_floor_primary within each player's playoff
    games, run full Screen F pipeline, compare structure to real data.
A3: Bayesian classification — Beta posteriors on tercile floor rates,
    probabilistic trigger labels.
A5: Bootstrap tercile CIs — resample games within each tercile,
    report 95% CIs, flag players whose tercile CIs overlap.

Output:
  data/processed/trigger_sensitivity.csv     — A1: classification per threshold combo
  data/processed/trigger_null_model.csv      — A2: null model results
  data/processed/trigger_bayesian.csv        — A3: posterior probabilities
  data/processed/trigger_bootstrap_cis.csv    — A5: bootstrap CIs
  output/figures/trigger_sensitivity_heatmap.png  — A1 heatmap
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config

from screen_f import compute_trigger_profile, _def_col

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

RNG = np.random.default_rng(42)


# ---------------------------------------------------------------------------
# A1: Parameterized classify_trigger
# ---------------------------------------------------------------------------

THRESHOLD_DEFAULTS = {
    "gradient_scheme": -0.15,
    "gradient_disengage": 0.15,
    "gradient_disengage_soft": 0.10,
    "weak_elevated_over_po": 0.05,
    "weak_elevated_floor": 0.20,
    "strong_present": 0.10,
    "bimodal_elevation": 0.05,
    "disengage_strong_ratio": 0.5,
    "disengage_weak_strong_gap": 0.15,
    "disengage_soft_gap": 0.05,
}


def classify_trigger_param(profile: dict, t: dict | None = None) -> str:
    if profile is None:
        return "unknown"

    if t is None:
        t = THRESHOLD_DEFAULTS

    gradient = profile.get("gradient", np.nan)
    def_coef = profile.get("def_coef", np.nan)
    def_pval = profile.get("def_pval", 1.0)
    is_bimodal = profile.get("is_bimodal", False)
    weak_floor = profile.get("weak_floor", np.nan)
    strong_floor = profile.get("strong_floor", np.nan)
    avg_floor = profile.get("avg_floor", np.nan)
    po_floor = profile.get("po_floor_rate", np.nan)

    if np.isnan(gradient):
        return "unknown"

    grad_scheme = t["gradient_scheme"]
    grad_dis = t["gradient_disengage"]
    grad_dis_soft = t["gradient_disengage_soft"]

    if gradient <= grad_scheme and (def_pval < 0.10 or (not np.isnan(def_coef) and def_coef > 0.01)):
        return "scheme-dependent"

    if gradient >= grad_dis:
        if not np.isnan(strong_floor) and not np.isnan(po_floor) and strong_floor < po_floor * t["disengage_strong_ratio"]:
            return "disengagement"
        if not np.isnan(weak_floor) and not np.isnan(strong_floor) and weak_floor - strong_floor > t["disengage_weak_strong_gap"]:
            return "disengagement"

    if not np.isnan(weak_floor) and not np.isnan(strong_floor):
        weak_elevated = weak_floor > max(po_floor + t["weak_elevated_over_po"], t["weak_elevated_floor"]) if not np.isnan(po_floor) else False
        strong_present = strong_floor > t["strong_present"]
        if weak_elevated and strong_present:
            return "opponent-independent"

    if is_bimodal and not np.isnan(avg_floor) and not np.isnan(weak_floor) and not np.isnan(strong_floor):
        if weak_floor > avg_floor + t["bimodal_elevation"] and strong_floor > avg_floor + t["bimodal_elevation"]:
            return "bimodal"

    if gradient > grad_dis_soft and not np.isnan(weak_floor) and not np.isnan(strong_floor) and weak_floor > strong_floor + t["disengage_soft_gap"]:
        return "disengagement"

    return "standard"


def run_sensitivity(df: pd.DataFrame) -> pd.DataFrame:
    col = _def_col(df)
    po = df[df["is_playoff"] & df[col].notna()].copy()

    players = sorted(po["player_name"].unique())
    profiles = {}
    for player in players:
        po_sub = po[po["player_name"] == player]
        rs_sub = df[(df["player_name"] == player) & ~df["is_playoff"]]
        profiles[player] = compute_trigger_profile(po_sub, rs_sub, col)

    gradient_grid = [0.10, 0.12, 0.15, 0.18, 0.20]
    bimodal_grid = [0.03, 0.05, 0.08]
    weak_floor_grid = [0.15, 0.20, 0.25]

    rows = []
    for g_grad in gradient_grid:
        for b_elev in bimodal_grid:
            for w_floor in weak_floor_grid:
                t = dict(THRESHOLD_DEFAULTS)
                t["gradient_disengage"] = g_grad
                t["gradient_scheme"] = -g_grad
                t["gradient_disengage_soft"] = g_grad - 0.05
                t["bimodal_elevation"] = b_elev
                t["weak_elevated_floor"] = w_floor

                for player in players:
                    p = profiles[player]
                    if p is None:
                        continue
                    trig = classify_trigger_param(p, t)
                    rows.append({
                        "player": player,
                        "gradient_threshold": g_grad,
                        "bimodal_elevation": b_elev,
                        "weak_floor_threshold": w_floor,
                        "trigger": trig,
                        "baseline_trigger": classify_trigger_param(p),
                    })

    results = pd.DataFrame(rows)
    results.to_csv(config.PROCESSED_DIR / "trigger_sensitivity.csv", index=False)

    n_players = len(players)
    for g_grad in gradient_grid:
        for b_elev in bimodal_grid:
            for w_floor in weak_floor_grid:
                subset = results[
                    (results["gradient_threshold"] == g_grad)
                    & (results["bimodal_elevation"] == b_elev)
                    & (results["weak_floor_threshold"] == w_floor)
                ]
                changed = (subset["trigger"] != subset["baseline_trigger"]).sum()
                if changed > 0:
                    pct = changed / n_players * 100
                    swing_players = subset[subset["trigger"] != subset["baseline_trigger"]]["player"].tolist()

    return results


def print_sensitivity_report(results: pd.DataFrame) -> None:
    baseline = results[results["gradient_threshold"] == 0.15][
        results["bimodal_elevation"] == 0.05
    ][results["weak_floor_threshold"] == 0.20]

    print("\n" + "=" * 100)
    print("A1: THRESHOLD SENSITIVITY ANALYSIS")
    print("=" * 100)
    print()

    gradient_grid = sorted(results["gradient_threshold"].unique())
    bimodal_grid = sorted(results["bimodal_elevation"].unique())
    weak_grid = sorted(results["weak_floor_threshold"].unique())
    players = sorted(results["player"].unique())
    n_players = len(players)
    trigger_types = ["opponent-independent", "scheme-dependent", "disengagement", "bimodal", "standard", "unknown"]

    for g_grad in gradient_grid:
        subset = results[results["gradient_threshold"] == g_grad]
        base_subset = subset[subset["bimodal_elevation"] == 0.05][subset["weak_floor_threshold"] == 0.20]
        changed = (base_subset["trigger"] != base_subset["baseline_trigger"]).sum()
        print(f"  gradient={g_grad:.2f}: {changed}/{n_players} players change classification ({changed/n_players*100:.0f}%)")
        if changed > 0:
            for _, row in base_subset[base_subset["trigger"] != base_subset["baseline_trigger"]].iterrows():
                print(f"    {row['player']}: {row['baseline_trigger']} -> {row['trigger']}")

    print()
    print("  Swing players (change under +/-0.03 gradient perturbation):")
    base_15 = results[results["gradient_threshold"] == 0.15][results["bimodal_elevation"] == 0.05][results["weak_floor_threshold"] == 0.20]
    base_12 = results[results["gradient_threshold"] == 0.12][results["bimodal_elevation"] == 0.05][results["weak_floor_threshold"] == 0.20]
    base_18 = results[results["gradient_threshold"] == 0.18][results["bimodal_elevation"] == 0.05][results["weak_floor_threshold"] == 0.20]

    swing = []
    for player in players:
        t_base = base_15[base_15["player"] == player]["trigger"].values
        t_low = base_12[base_12["player"] == player]["trigger"].values
        t_high = base_18[base_18["player"] == player]["trigger"].values
        if len(t_base) == 0:
            continue
        labels = [t_base[0]]
        if len(t_low) > 0 and t_low[0] != t_base[0]:
            labels.append(t_low[0])
        if len(t_high) > 0 and t_high[0] != t_base[0]:
            labels.append(t_high[0])
        if len(labels) > 1:
            swing.append(player)
            print(f"    {player}: {labels[0]} (0.15) -> swings to {set(labels[1:])} under perturbation")

    robust = n_players - len(swing)
    print(f"\n  Robust: {robust}/{n_players} ({robust/n_players*100:.0f}%)")
    print(f"  Swing:  {len(swing)}/{n_players} ({len(swing)/n_players*100:.0f}%)")

    print("\n  Full heatmap (player x gradient, bimodal=0.05, weak_floor=0.20):")
    header = f"  {'Player':<28}"
    for g in gradient_grid:
        header += f" {g:.2f}"
    print(header)
    print(f"  {'-'*28}" + " " * 6 * len(gradient_grid))
    for player in players:
        line = f"  {player:<28}"
        for g in gradient_grid:
            t = results[
                (results["player"] == player)
                & (results["gradient_threshold"] == g)
                & (results["bimodal_elevation"] == 0.05)
                & (results["weak_floor_threshold"] == 0.20)
            ]["trigger"].values
            if len(t) > 0:
                abbr = {"opponent-independent": "OI", "scheme-dependent": "SD", "disengagement": "DI", "bimodal": "BM", "standard": "ST", "unknown": "UK"}
                line += f" {abbr.get(t[0], '??'):>4}"
            else:
                line += "    -"
        print(line)


# ---------------------------------------------------------------------------
# A2: Null model
# ---------------------------------------------------------------------------

def run_null_model(df: pd.DataFrame, n_perm: int = 1000) -> pd.DataFrame:
    col = _def_col(df)
    po = df[df["is_playoff"] & df[col].notna()].copy()

    players = sorted(po["player_name"].unique())

    real_results = []
    for player in players:
        po_sub = po[po["player_name"] == player]
        rs_sub = df[(df["player_name"] == player) & ~df["is_playoff"]]
        p = compute_trigger_profile(po_sub, rs_sub, col)
        if p is not None:
            p["player"] = player
            p["trigger"] = classify_trigger_param(p)
            real_results.append(p)

    real_df = pd.DataFrame(real_results)
    real_dist = real_df["trigger"].value_counts().to_dict()

    null_dists = {trigger: [] for trigger in ["opponent-independent", "scheme-dependent", "disengagement", "bimodal", "standard"]}
    null_max_bimodal = []
    null_max_gradient_15 = []

    for i in range(n_perm):
        if i % 100 == 0:
            logger.info("Null model permutation %d/%d", i, n_perm)

        po_perm = po.copy()
        perm_results = []

        for player in players:
            player_idx = po_perm[po_perm["player_name"] == player].index
            if len(player_idx) == 0:
                continue
            floor_vals = po_perm.loc[player_idx, "is_floor_primary"].values.copy()
            RNG.shuffle(floor_vals)
            po_perm.loc[player_idx, "is_floor_primary"] = floor_vals

            po_sub = po_perm[po_perm["player_name"] == player]
            rs_sub = df[(df["player_name"] == player) & ~df["is_playoff"]]
            p = compute_trigger_profile(po_sub, rs_sub, col)
            if p is not None:
                p["player"] = player
                p["trigger"] = classify_trigger_param(p)
                perm_results.append(p)

        perm_df = pd.DataFrame(perm_results)
        perm_dist = perm_df["trigger"].value_counts().to_dict()
        for trigger in null_dists:
            null_dists[trigger].append(perm_dist.get(trigger, 0))

        null_max_bimodal.append(perm_dist.get("bimodal", 0))
        n_grad_15 = 0
        if "gradient" in perm_df.columns:
            n_grad_15 = (perm_df["gradient"].dropna().abs() >= 0.15).sum()
        null_max_gradient_15.append(n_grad_15)

    rows = []
    for trigger in ["opponent-independent", "scheme-dependent", "disengagement", "bimodal", "standard"]:
        real_count = real_dist.get(trigger, 0)
        null_counts = null_dists[trigger]
        p_val = np.mean([c >= real_count for c in null_counts])
        rows.append({
            "trigger_type": trigger,
            "real_count": real_count,
            "null_mean": np.mean(null_counts),
            "null_std": np.std(null_counts),
            "null_p95": np.percentile(null_counts, 95),
            "p_value": p_val,
        })

    real_bimodal = real_dist.get("bimodal", 0)
    real_grad_15 = 0
    if "gradient" in real_df.columns:
        real_grad_15 = (real_df["gradient"].dropna().abs() >= 0.15).sum()

    rows.append({
        "trigger_type": "any_bimodal",
        "real_count": real_bimodal,
        "null_mean": np.mean(null_max_bimodal),
        "null_std": np.std(null_max_bimodal),
        "null_p95": np.percentile(null_max_bimodal, 95),
        "p_value": np.mean([c >= real_bimodal for c in null_max_bimodal]),
    })
    rows.append({
        "trigger_type": "any_gradient_ge_015",
        "real_count": real_grad_15,
        "null_mean": np.mean(null_max_gradient_15),
        "null_std": np.std(null_max_gradient_15),
        "null_p95": np.percentile(null_max_gradient_15, 95),
        "p_value": np.mean([c >= real_grad_15 for c in null_max_gradient_15]),
    })

    results = pd.DataFrame(rows)
    results.to_csv(config.PROCESSED_DIR / "trigger_null_model.csv", index=False)
    return results


def print_null_report(results: pd.DataFrame) -> None:
    print("\n" + "=" * 100)
    print("A2: NULL MODEL (PERMUTATION TEST)")
    print("=" * 100)
    print()
    print("  If is_floor_primary is randomly assigned within each player's playoff games,")
    print("  how much trigger structure emerges by chance?")
    print()
    print(f"  {'Trigger type':<25} {'Real':>5} {'Null mean':>10} {'Null p95':>10} {'p-value':>8}")
    print(f"  {'-'*25} {'----':>5} {'---------':>10} {'--------':>10} {'--------':>8}")
    for _, r in results.iterrows():
        sig = " ***" if r["p_value"] < 0.01 else " **" if r["p_value"] < 0.05 else " *" if r["p_value"] < 0.10 else ""
        print(f"  {r['trigger_type']:<25} {int(r['real_count']):>5} {r['null_mean']:>10.1f} {r['null_p95']:>10.1f} {r['p_value']:>8.3f}{sig}")


# ---------------------------------------------------------------------------
# A3: Bayesian classification
# ---------------------------------------------------------------------------

def run_bayesian(df: pd.DataFrame, n_samples: int = 10000) -> pd.DataFrame:
    col = _def_col(df)
    po = df[df["is_playoff"] & df[col].notna()].copy()

    players = sorted(po["player_name"].unique())
    rows = []

    for player in players:
        po_sub = po[po["player_name"] == player]
        rs_sub = df[(df["player_name"] == player) & ~df["is_playoff"]]
        p = compute_trigger_profile(po_sub, rs_sub, col)
        if p is None:
            continue

        weak_floor = p.get("weak_floor", np.nan)
        avg_floor = p.get("avg_floor", np.nan)
        strong_floor = p.get("strong_floor", np.nan)
        gradient = p.get("gradient", np.nan)
        po_floor = p.get("po_floor_rate", np.nan)

        if np.isnan(weak_floor) or np.isnan(strong_floor):
            continue

        weak_n = p.get("weak_n", 0)
        strong_n = p.get("strong_n", 0)
        weak_games = po_sub[po_sub[col] <= po_sub[col].quantile(0.33)]
        strong_games = po_sub[po_sub[col] > po_sub[col].quantile(0.67)]

        weak_k = int(weak_games["is_floor_primary"].sum()) if len(weak_games) > 0 else 0
        weak_n_total = len(weak_games)
        strong_k = int(strong_games["is_floor_primary"].sum()) if len(strong_games) > 0 else 0
        strong_n_total = len(strong_games)

        prior_alpha = 1.0
        prior_beta = 5.0

        weak_samples = RNG.beta(prior_alpha + weak_k, prior_beta + weak_n_total - weak_k, size=n_samples)
        strong_samples = RNG.beta(prior_alpha + strong_k, prior_beta + strong_n_total - strong_k, size=n_samples)
        gradient_samples = weak_samples - strong_samples

        p_oi = np.mean(
            (weak_samples > 0.20)
            & (strong_samples > 0.10)
        )

        p_sd = np.mean(gradient_samples <= -0.15)

        p_di = np.mean(
            (gradient_samples >= 0.15)
            & (strong_samples < 0.5 * po_floor if not np.isnan(po_floor) else 0)
        ) if not np.isnan(po_floor) else np.mean(gradient_samples >= 0.15)

        p_bm = np.mean(
            (weak_samples > avg_floor + 0.05 if not np.isnan(avg_floor) else np.zeros(n_samples, dtype=bool))
            & (strong_samples > avg_floor + 0.05 if not np.isnan(avg_floor) else np.zeros(n_samples, dtype=bool))
        ) if not np.isnan(avg_floor) else 0.0

        p_st = 1.0 - p_oi - p_sd - p_di - p_bm
        p_st = max(p_st, 0.0)

        probs = {
            "opponent-independent": p_oi,
            "scheme-dependent": p_sd,
            "disengagement": p_di,
            "bimodal": p_bm,
            "standard": p_st,
        }
        best = max(probs, key=probs.get)
        best_prob = probs[best]
        uncertain = best_prob < 0.70

        row = {
            "player": player,
            "hard_trigger": classify_trigger_param(p),
            "bayesian_best": best,
            "bayesian_best_prob": best_prob,
            "uncertain": uncertain,
        }
        for t, prob in probs.items():
            row[f"prob_{t}"] = prob

        rows.append(row)

    results = pd.DataFrame(rows)
    results.to_csv(config.PROCESSED_DIR / "trigger_bayesian.csv", index=False)
    return results


def print_bayesian_report(results: pd.DataFrame) -> None:
    print("\n" + "=" * 100)
    print("A3: BAYESIAN TRIGGER CLASSIFICATION")
    print("=" * 100)
    print()
    print(f"  {'Player':<28} {'Hard':>10} {'Bayes':>10} {'Best p':>7} {'Unc':>5} {'p_OI':>6} {'p_SD':>6} {'p_DI':>6} {'p_BM':>6} {'p_ST':>6}")
    print(f"  {'-'*28} {'----':>10} {'-----':>10} {'------':>7} {'---':>5} {'----':>6} {'----':>6} {'----':>6} {'----':>6} {'----':>6}")

    n_uncertain = 0
    n_concordant = 0
    n_total = len(results)

    for _, r in results.iterrows():
        concord = "Y" if r["hard_trigger"] == r["bayesian_best"] else "N"
        if r["hard_trigger"] != r["bayesian_best"]:
            n_concordant += 0
        else:
            n_concordant += 1
        if r["uncertain"]:
            n_uncertain += 1
        unc = "Y" if r["uncertain"] else " "
        print(f"  {r['player']:<28} {r['hard_trigger']:>10} {r['bayesian_best']:>10} {r['bayesian_best_prob']:>7.2f} {unc:>5} "
              f"{r['prob_opponent-independent']:>6.2f} {r['prob_scheme-dependent']:>6.2f} "
              f"{r['prob_disengagement']:>6.2f} {r['prob_bimodal']:>6.2f} {r['prob_standard']:>6.2f}")

    print()
    print(f"  Concordance (hard == bayesian best): {n_concordant}/{n_total} ({n_concordant/n_total*100:.0f}%)")
    print(f"  Uncertain (best posterior < 0.70):  {n_uncertain}/{n_total} ({n_uncertain/n_total*100:.0f}%)")

    if n_uncertain > n_total * 0.5:
        print("\n  WARNING: Majority of players are uncertain. Hard classification is premature.")
    elif n_uncertain > n_total * 0.3:
        print("\n  CAUTION: Significant minority uncertain. Probabilistic labels recommended for swing players.")
    else:
        print("\n  PASS: Most players have confident posterior classifications.")


# ---------------------------------------------------------------------------
# A5: Bootstrap tercile CIs
# ---------------------------------------------------------------------------

def run_bootstrap_cis(df: pd.DataFrame, n_boot: int = 1000) -> pd.DataFrame:
    col = _def_col(df)
    po = df[df["is_playoff"] & df[col].notna()].copy()

    players = sorted(po["player_name"].unique())
    rows = []

    for player in players:
        po_sub = po[po["player_name"] == player]
        rs_sub = df[(df["player_name"] == player) & ~df["is_playoff"]]
        p = compute_trigger_profile(po_sub, rs_sub, col)
        if p is None:
            continue

        q33 = po_sub[col].quantile(0.33)
        q67 = po_sub[col].quantile(0.67)
        weak_idx = po_sub[col] <= q33
        avg_idx = (po_sub[col] > q33) & (po_sub[col] <= q67)
        strong_idx = po_sub[col] > q67

        weak_games = po_sub[weak_idx]
        avg_games = po_sub[avg_idx]
        strong_games = po_sub[strong_idx]

        def bootstrap_ci(games: pd.DataFrame, n_boot: int) -> tuple:
            if len(games) < 3:
                return np.nan, np.nan, np.nan, np.nan
            rates = []
            for _ in range(n_boot):
                sample = games.sample(n=len(games), replace=True, random_state=RNG)
                rates.append(sample["is_floor_primary"].mean())
            return np.percentile(rates, 2.5), np.percentile(rates, 50), np.percentile(rates, 97.5), len(games)

        w_lo, w_med, w_hi, w_n = bootstrap_ci(weak_games, n_boot)
        a_lo, a_med, a_hi, a_n = bootstrap_ci(avg_games, n_boot)
        s_lo, s_med, s_hi, s_n = bootstrap_ci(strong_games, n_boot)

        ws_overlap = False
        if not np.isnan(w_lo) and not np.isnan(s_hi):
            ws_overlap = w_lo < s_hi

        wa_overlap = False
        if not np.isnan(w_lo) and not np.isnan(a_hi):
            wa_overlap = w_lo < a_hi

        rows.append({
            "player": player,
            "trigger": classify_trigger_param(p),
            "weak_floor": p.get("weak_floor", np.nan),
            "weak_ci_lo": w_lo,
            "weak_ci_med": w_med,
            "weak_ci_hi": w_hi,
            "weak_n": w_n,
            "avg_floor": p.get("avg_floor", np.nan),
            "avg_ci_lo": a_lo,
            "avg_ci_med": a_med,
            "avg_ci_hi": a_hi,
            "avg_n": a_n,
            "strong_floor": p.get("strong_floor", np.nan),
            "strong_ci_lo": s_lo,
            "strong_ci_med": s_med,
            "strong_ci_hi": s_hi,
            "strong_n": s_n,
            "gradient": p.get("gradient", np.nan),
            "ws_overlap": ws_overlap,
            "wa_overlap": wa_overlap,
        })

    results = pd.DataFrame(rows)
    results.to_csv(config.PROCESSED_DIR / "trigger_bootstrap_cis.csv", index=False)
    return results


def print_bootstrap_report(results: pd.DataFrame) -> None:
    print("\n" + "=" * 100)
    print("A5: BOOTSTRAP TERCILE CONFIDENCE INTERVALS (95%)")
    print("=" * 100)
    print()
    print(f"  {'Player':<28} {'Trigger':>18} {'Weak (CI)':>24} {'Avg (CI)':>24} {'Strong (CI)':>24} {'W-S overlap':>12}")
    print(f"  {'-'*28} {'-'*18} {'-'*24} {'-'*24} {'-'*24} {'-'*12}")

    n_overlap = 0
    n_total = 0
    for _, r in results.iterrows():
        n_total += 1
        if r["ws_overlap"]:
            n_overlap += 1

        def fmt(val, lo, hi):
            if np.isnan(val):
                return "         -          "
            return f"{val:>5.0%} [{lo:>4.0%}-{hi:>4.0%}]"

        weak_s = fmt(r["weak_floor"], r["weak_ci_lo"], r["weak_ci_hi"])
        avg_s = fmt(r["avg_floor"], r["avg_ci_lo"], r["avg_ci_hi"])
        strong_s = fmt(r["strong_floor"], r["strong_ci_lo"], r["strong_ci_hi"])
        overlap = "YES" if r["ws_overlap"] else "no"

        print(f"  {r['player']:<28} {r['trigger']:>18} {weak_s:>24} {avg_s:>24} {strong_s:>24} {overlap:>12}")

    print()
    print(f"  Players with weak-strong CI overlap: {n_overlap}/{n_total} ({n_overlap/n_total*100:.0f}%)")
    print("  (Overlap means the tercile floor rates are not statistically distinguishable)")

    if n_overlap > n_total * 0.5:
        print("\n  WARNING: Majority of players have overlapping weak-strong CIs.")
        print("  Trigger classifications may not be statistically supported at the tercile level.")
    elif n_overlap > n_total * 0.3:
        print("\n  CAUTION: Significant minority have overlapping CIs.")
        print("  Some trigger labels are not statistically distinguishable from each other.")
    else:
        print("\n  PASS: Most players have distinguishable tercile floor rates.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    path = config.PROCESSED_DIR / "analysis_table.csv"
    if not path.exists():
        raise FileNotFoundError(f"Run features first: {path}")

    df = pd.read_csv(path, low_memory=False)
    df["is_playoff"] = df["is_playoff"].astype(bool)
    df["is_floor_primary"] = df["is_floor_primary"].astype(bool)

    config.FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    # A1: Sensitivity
    logger.info("A1: Running threshold sensitivity analysis...")
    sens = run_sensitivity(df)
    print_sensitivity_report(sens)

    # A2: Null model
    logger.info("A2: Running null model (1000 permutations)...")
    null = run_null_model(df, n_perm=1000)
    print_null_report(null)

    # A3: Bayesian
    logger.info("A3: Running Bayesian classification...")
    bayes = run_bayesian(df)
    print_bayesian_report(bayes)

    # A5: Bootstrap CIs
    logger.info("A5: Running bootstrap tercile CIs...")
    boot = run_bootstrap_cis(df)
    print_bootstrap_report(boot)

    # Summary
    print("\n" + "=" * 100)
    print("PHASE A SUMMARY: KILL THE TAXONOMY OR PROVE IT'S REAL")
    print("=" * 100)

    n_players = len(sens["player"].unique())
    base = sens[
        (sens["gradient_threshold"] == 0.15)
        & (sens["bimodal_elevation"] == 0.05)
        & (sens["weak_floor_threshold"] == 0.20)
    ]
    base_12 = sens[
        (sens["gradient_threshold"] == 0.12)
        & (sens["bimodal_elevation"] == 0.05)
        & (sens["weak_floor_threshold"] == 0.20)
    ]
    base_18 = sens[
        (sens["gradient_threshold"] == 0.18)
        & (sens["bimodal_elevation"] == 0.05)
        & (sens["weak_floor_threshold"] == 0.20)
    ]
    n_swing = 0
    for player in sens["player"].unique():
        t15 = base[base["player"] == player]["trigger"].values
        t12 = base_12[base_12["player"] == player]["trigger"].values
        t18 = base_18[base_18["player"] == player]["trigger"].values
        if len(t15) > 0 and ((len(t12) > 0 and t12[0] != t15[0]) or (len(t18) > 0 and t18[0] != t15[0])):
            n_swing += 1

    swing_pct = n_swing / n_players * 100 if n_players > 0 else 0

    null_bimodal_row = null[null["trigger_type"] == "bimodal"]
    null_bimodal_p = null_bimodal_row["p_value"].values[0] if len(null_bimodal_row) > 0 else 1.0

    n_uncertain = bayes["uncertain"].sum()
    uncertain_pct = n_uncertain / len(bayes) * 100 if len(bayes) > 0 else 100

    n_overlap = boot["ws_overlap"].sum()
    overlap_pct = n_overlap / len(boot) * 100 if len(boot) > 0 else 100

    print()
    print(f"  A1 (Sensitivity): {n_swing}/{n_players} swing players ({swing_pct:.0f}%) under +/-0.03 gradient perturbation")
    print(f"  A2 (Null model):   Bimodal category p = {null_bimodal_p:.3f} {'(PASS)' if null_bimodal_p < 0.05 else '(FAIL - similar to chance)'}")
    print(f"  A3 (Bayesian):    {n_uncertain}/{len(bayes)} uncertain ({uncertain_pct:.0f}%)")
    print(f"  A5 (Bootstrap):   {n_overlap}/{len(boot)} weak-strong CI overlap ({overlap_pct:.0f}%)")
    print()

    a1_pass = swing_pct < 30
    a2_pass = null_bimodal_p < 0.05
    a3_pass = uncertain_pct < 50
    a5_pass = overlap_pct < 50

    if a1_pass and a2_pass and a3_pass:
        print("  VERDICT: TAXONOMY SURVIVES Phase A. Proceed to A4 (split-sample).")
    elif a1_pass and a3_pass and not a2_pass:
        print("  VERDICT: MIXED. Taxonomy survives sensitivity but null model shows")
        print("  comparable structure from noise. Investigate before A4.")
    elif not a1_pass:
        print("  VERDICT: TAXONOMY FAILS sensitivity test. Stop.")
        print("  Publishable contribution: opponent-adjustment + trait stability.")
    elif not a3_pass:
        print("  VERDICT: TAXONOMY FAILS Bayesian confidence. Hard labels are premature.")
        print("  Consider probabilistic classifications instead.")
    else:
        print("  VERDICT: INCONCLUSIVE. Some checks pass, some fail. Investigate before A4.")

    logger.info("Phase A complete")


if __name__ == "__main__":
    main()
