"""Run gravity model validation, compute R²/timing, and generate bar charts."""
import pandas as pd
import numpy as np
import geopandas as gpd
from shapely import wkt
from shapely.geometry import Point
from scipy.stats import linregress, pearsonr, spearmanr
import os, json, time, sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

print("=" * 60)
print("  GRAVITY MODEL VALIDATION — FULL ANALYSIS")
print("=" * 60)

start = time.time()

# Ensure output dir
os.makedirs("images", exist_ok=True)

# 1. Load real Pamplona zones
p_zones_df = pd.read_csv("pamplona_zones.csv")
p_zones_gdf = gpd.GeoDataFrame(
    p_zones_df,
    geometry=gpd.points_from_xy(p_zones_df["lon"], p_zones_df["lat"]),
    crs="EPSG:4326"
)

# 2. Load grid2demand zones
print("\nLoading grid2demand output...")
g2d_zones = pd.read_csv("grid2demand_output/zone.csv")
g2d_zones["geometry"] = g2d_zones["geometry"].apply(wkt.loads)
g2d_zones_gdf = gpd.GeoDataFrame(g2d_zones, geometry="geometry", crs="EPSG:4326")

# 3. Spatial join
t0 = time.time()
joined = gpd.sjoin(p_zones_gdf, g2d_zones_gdf, how="inner", predicate="within")
zone_map = dict(zip(joined["id"].astype(str), joined["zone_id"].astype(int)))
t_sjoin = time.time() - t0
print(f"  Spatial join: {len(joined)} zone mappings in {t_sjoin:.2f}s")
print(f"  Mapped {len(zone_map)} of {len(p_zones_df)} zones to grid cells")

# 4. Load real flows and map to grid
t0 = time.time()
p_flows = pd.read_csv("pamplona_real_flows.csv")
p_flows["o_g2d"] = p_flows["origin"].astype(str).map(zone_map)
p_flows["d_g2d"] = p_flows["dest"].astype(str).map(zone_map)
p_flows = p_flows.dropna(subset=["o_g2d", "d_g2d"])
p_flows["o_g2d"] = p_flows["o_g2d"].astype(int)
p_flows["d_g2d"] = p_flows["d_g2d"].astype(int)

# 5. Aggregate real flows to grid cells
real_grid_flows = p_flows.groupby(["o_g2d", "d_g2d"])["daily_volume"].sum().reset_index()
t_agg = time.time() - t0
print(f"  Aggregated to {len(real_grid_flows)} grid-cell OD pairs in {t_agg:.2f}s")

# 6. Merge with gravity model
t0 = time.time()
demand_matrix = pd.read_csv("grid2demand_output/demand.csv")
merged = pd.merge(
    real_grid_flows, 
    demand_matrix, 
    left_on=["o_g2d", "d_g2d"], 
    right_on=["o_zone_id", "d_zone_id"], 
    how="inner"
)
t_merge = time.time() - t0
print(f"  Merged: {len(merged)} matched OD pairs in {t_merge:.2f}s")

# 7. CORRELATION + R-SQUARED
obs = merged["daily_volume"].values
mod = merged["volume"].values

corr_p, p_p = pearsonr(obs, mod)
corr_s, p_s = spearmanr(obs, mod)
r2 = corr_p ** 2

# OLS regression
slope, intercept, r_value, p_value, std_err = linregress(mod, obs)

rmse = float(np.sqrt(np.mean((obs - mod)**2)))
nrmse = rmse / obs.mean()

print("\n" + "=" * 60)
print("  MODEL PERFORMANCE METRICS")
print("=" * 60)
print(f"  Matched zone pairs:     {len(merged):>6,}")
print(f"  Pearson r:              {corr_p:>8.4f}  (p = {p_p:.2e})")
print(f"  R-squared (r²):         {r2:>8.4f}")
print(f"  Spearman rank ρ:        {corr_s:>8.4f}  (p = {p_s:.2e})")
print(f"  OLS slope:              {slope:>8.4f}")
print(f"  OLS intercept:          {intercept:>8.4f}")
print(f"  RMSE:                   {rmse:>10.1f}")
print(f"  NRMSE (RMSE/mean):      {nrmse:>8.4f}")
print(f"  Mean observed:          {obs.mean():>10.1f}")
print(f"  Mean modelled:          {mod.mean():>10.1f}")
print(f"  Observed total:         {obs.sum():>12,.0f}")
print(f"  Modelled total:         {mod.sum():>12,.0f}")
print("=" * 60)

total_time = time.time() - start
print(f"\n  Total analysis time:    {total_time:.2f}s")

# --- BAR CHARTS ---

# Chart 1: Observed vs Modelled — top 20 zone pairs
top20 = merged.sort_values("daily_volume", ascending=False).head(20)
fig, ax = plt.subplots(figsize=(12, 7))
x = np.arange(len(top20))
width = 0.35
ax.bar(x - width/2, top20["daily_volume"].values, width, 
       label="Observed (daily trips)", color="#2c7fb8", alpha=0.85)
ax.bar(x + width/2, top20["volume"].values, width,
       label="Modelled (gravity)", color="#f03b20", alpha=0.85)
ax.set_xlabel("Origin-destination zone pair", fontsize=11)
ax.set_ylabel("Trip volume", fontsize=11)
ax.set_title("Top 20 Observed vs Modelled OD Flows — Pamplona", fontsize=13, fontweight="bold")
ax.set_xticks(x)
ax.set_xticklabels([f"{int(r['o_g2d'])}→{int(r['d_g2d'])}" for _, r in top20.iterrows()], 
                   rotation=45, ha="right", fontsize=8)
ax.legend(fontsize=11)
ax.text(0.98, 0.95, f"R² = {r2:.3f}   ρ = {corr_s:.3f}", 
        transform=ax.transAxes, ha="right", va="top", fontsize=12,
        bbox=dict(boxstyle="round,pad=0.3", facecolor="wheat", alpha=0.8))
plt.tight_layout()
fig.savefig("images/bar-observed-vs-modelled.png", dpi=150)
plt.close(fig)
print("\n  Saved: images/bar-observed-vs-modelled.png")

# Chart 2: Correlation scatter with regression line
fig, ax = plt.subplots(figsize=(8, 7))
ax.scatter(mod, obs, alpha=0.4, s=15, c="#1f77b4", edgecolors="none")
x_line = np.linspace(max(mod.min(), 0.001), mod.max(), 100)
ax.plot(x_line, slope * x_line + intercept, "r-", linewidth=2, 
        label=f"OLS fit (slope={slope:.2f}, R²={r2:.3f})")
ax.plot(x_line, x_line, "k--", linewidth=1, alpha=0.5, label="1:1 line")
ax.set_xlabel("Modelled volume (gravity model)", fontsize=11)
ax.set_ylabel("Observed daily volume", fontsize=11)
ax.set_title("Gravity Model Validation — Pamplona OD Pairs", fontsize=13, fontweight="bold")
ax.legend(fontsize=10)
ax.text(0.05, 0.95, f"n = {len(merged)}\nPearson r = {corr_p:.4f}\nSpearman ρ = {corr_s:.4f}\nR² = {r2:.4f}", 
        transform=ax.transAxes, ha="left", va="top", fontsize=11,
        bbox=dict(boxstyle="round,pad=0.3", facecolor="wheat", alpha=0.8))
plt.tight_layout()
fig.savefig("images/bar-correlation-scatter.png", dpi=150)
plt.close(fig)
print("  Saved: images/bar-correlation-scatter.png")

# Chart 3: Model performance comparison — bar chart of key metrics
metrics_labels = ["Pearson r", "R-squared", "Spearman ρ", "NRMSE"]
metrics_values = [corr_p, r2, corr_s, nrmse]
colors = ["#2c7fb8", "#f03b20", "#7bccc4", "#fdcc8a"]

fig, ax = plt.subplots(figsize=(9, 5.5))
bars = ax.bar(metrics_labels, metrics_values, color=colors, alpha=0.85, 
              edgecolor="grey", linewidth=1.2, width=0.6)
for bar, val in zip(bars, metrics_values):
    y_pos = bar.get_height() + 0.015
    ax.text(bar.get_x() + bar.get_width()/2, y_pos, 
            f"{val:.4f}", ha="center", va="bottom", fontsize=12, fontweight="bold")
ax.set_ylabel("Metric value", fontsize=12)
ax.set_title("Gravity Model Performance Metrics", fontsize=14, fontweight="bold")
ax.set_ylim(0, max(metrics_values) * 1.3)
ax.axhline(y=0, color="grey", linewidth=0.8)
plt.tight_layout()
fig.savefig("images/bar-performance-metrics.png", dpi=150)
plt.close(fig)
print("  Saved: images/bar-performance-metrics.png")

# Chart 4: Distribution comparison — log-scaled histograms
fig, ax = plt.subplots(figsize=(10, 6))
ax.hist(obs, bins=50, alpha=0.6, label=f"Observed (n={len(obs)})", 
        color="#2c7fb8", density=True)
ax.hist(mod, bins=50, alpha=0.6, label=f"Modelled (n={len(mod)})", 
        color="#f03b20", density=True)
ax.set_xlabel("Trip volume", fontsize=11)
ax.set_ylabel("Density", fontsize=11)
ax.set_title("Distribution of Observed vs Modelled OD Flows", fontsize=13, fontweight="bold")
ax.legend(fontsize=11)
ax.set_yscale("log")
plt.tight_layout()
fig.savefig("images/bar-distribution-comparison.png", dpi=150)
plt.close(fig)
print("  Saved: images/bar-distribution-comparison.png")

# --- SAVE SUMMARY ---
summary = {
    "matched_pairs": len(merged),
    "pearson_r": round(corr_p, 4),
    "pearson_p": float(f"{p_p:.2e}"),
    "r_squared": round(r2, 4),
    "spearman_rho": round(corr_s, 4),
    "spearman_p": float(f"{p_s:.2e}"),
    "ols_slope": round(slope, 4),
    "ols_intercept": round(intercept, 4),
    "rmse": round(rmse, 1),
    "nrmse": round(nrmse, 4),
    "mean_observed": round(float(obs.mean()), 1),
    "mean_modelled": round(float(mod.mean()), 1),
    "total_observed": round(float(obs.sum()), 0),
    "total_modelled": round(float(mod.sum()), 0),
    "analysis_time_s": round(total_time, 2),
    "zones_mapped": len(zone_map),
    "total_zones": len(p_zones_df)
}
with open("results_summary.json", "w") as f:
    json.dump(summary, f, indent=2)
print(f"\n  Saved: results_summary.json")

print("\n" + "=" * 60)
print("  ANALYSIS COMPLETE")
print("=" * 60)
