# ============================================================
# ERA5 DAILY statistics — CDS derived datasets — India
# For S2S. Fastest CDS path to DAILY data: the derived
# daily-statistics datasets aggregate server-side and return
# tiny files (24× less transfer than downloading hourly).
#
# Datasets (published late 2024):
#   derived-era5-pressure-levels-daily-statistics  (u,v,T,q,RH @ levels)
#   derived-era5-single-levels-daily-statistics    (precip, MSLP, 2m, 10m)
#
# Design choices (see notes at each config block):
#   • daily_mean for state variables, daily_sum for precipitation.
#     To also grab extremes, add "daily_maximum"/"daily_minimum"
#     to STATISTICS — costs one extra request per variable-year.
#   • One variable per request (dataset requirement), per year.
#   • 6-hourly sampling for means (fast); 1-hourly forced for
#     sums and extremes (needed for correctness / true extremes).
#   • Derived requests are server-compute heavy → few workers.
#   • Output is a zip per request; the .nc inside is extracted.
#   • Resume: valid files skipped, corrupt/partial redone.
#
# Deps: pip install "cdsapi>=0.7" xarray netCDF4
# ============================================================

import os
import time
import shutil
import zipfile
import warnings
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date

import cdsapi
import xarray as xr

warnings.filterwarnings("ignore", category=xr.SerializationWarning)

# ------------------------------------------------------------
# Config
# ------------------------------------------------------------

DOWNLOAD_DIR = r"downloads_era5_daily"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# India (CDS: [North, West, South, East])
AREA = [37.1, 68.12, 6.75, 97.42]

PRESSURE_LEVELS = ["250", "500", "850"]

START_YEAR = 1980
LAG_MONTHS = 2                      # skip most recent (ERA5 production lag)

# ---- STATISTIC CHOICE (the main speed lever) ----
# Speed-optimal default: mean only (precip always uses sum below).
# To hedge for extremes, add the max/min values — one extra request
# per variable-year each. If a max/min request 400s, the exact enum
# may be "daily_max"/"daily_min"; grab it from the dataset's
# "Show API request" button on the CDS site.
STATISTICS = ["daily_mean"]        # e.g. + ["daily_maximum", "daily_minimum"]

TIME_ZONE = "utc+00:00"

# Server-compute per request → keep modest. Check live per-user
# limits: https://cds.climate.copernicus.eu/live
N_WORKERS = 4

PL_DATASET = "derived-era5-pressure-levels-daily-statistics"
SL_DATASET = "derived-era5-single-levels-daily-statistics"

# ---- Variables (11) ----
# family: "pl" (pressure levels) or "sfc"; accum=True → daily_sum only.
VARIABLES = [
    # pressure-level, instantaneous
    ("u_component_of_wind",      "pl",  False),
    ("v_component_of_wind",      "pl",  False),
    ("temperature",              "pl",  False),
    ("specific_humidity",        "pl",  False),
    ("relative_humidity",        "pl",  False),
    # surface, instantaneous
    ("mean_sea_level_pressure",  "sfc", False),
    ("2m_temperature",           "sfc", False),
    ("10m_u_component_of_wind",  "sfc", False),
    ("10m_v_component_of_wind",  "sfc", False),
    ("2m_dewpoint_temperature",  "sfc", False),
    # surface, accumulated → daily sum
    ("total_precipitation",      "sfc", True),
]

# ------------------------------------------------------------
# Date range → per-year month lists
# ------------------------------------------------------------

today = date.today()
end_y, end_m = today.year, today.month
for _ in range(LAG_MONTHS):
    end_m -= 1
    if end_m == 0:
        end_m = 12
        end_y -= 1

ALL_MONTHS = [f"{m:02d}" for m in range(1, 13)]
DAYS = [f"{d:02d}" for d in range(1, 32)]

year_plan = []
for y in range(START_YEAR, end_y + 1):
    months = [f"{m:02d}" for m in range(1, end_m + 1)] if y == end_y else ALL_MONTHS
    if months:
        year_plan.append((str(y), months))


def stats_for(accum):
    """Which (statistic, frequency) pairs to fetch for a variable."""
    if accum:
        return [("daily_sum", "1_hourly")]          # sum needs full 24 h
    out = []
    for s in STATISTICS:
        freq = "6_hourly" if s == "daily_mean" else "1_hourly"  # extremes need 1 h
        out.append((s, freq))
    return out


# Build the full task list
tasks = []
for name, family, accum in VARIABLES:
    for stat, freq in stats_for(accum):
        for year, months in year_plan:
            tasks.append((name, family, accum, stat, freq, year, months))

print(f"Today is        : {today}")
print(f"Year range      : {year_plan[0][0]} → {year_plan[-1][0]}")
print(f"Variables       : {len(VARIABLES)}  |  PL levels {PRESSURE_LEVELS}")
print(f"Statistics      : {STATISTICS}  (+ daily_sum for precip)")
print(f"Total requests  : {len(tasks)}")
print(f"Parallel workers: {N_WORKERS}")
print(f"Output dir      : {DOWNLOAD_DIR}")
print("Setup done.\n")

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def is_valid(path):
    try:
        with xr.open_dataset(path, engine="netcdf4") as d:
            return bool(d.data_vars) and d[list(d.data_vars)[0]].size > 0
    except Exception:
        return False


def out_path_for(name, stat, year):
    var_dir = os.path.join(DOWNLOAD_DIR, name)
    os.makedirs(var_dir, exist_ok=True)
    return os.path.join(var_dir, f"{name}_{stat}_{year}.nc")


def finalize(tmp, final):
    """Derived daily returns a zip with one .nc inside; extract it."""
    if zipfile.is_zipfile(tmp):
        with zipfile.ZipFile(tmp) as z:
            ncs = [n for n in z.namelist() if n.endswith(".nc")]
            if not ncs:
                raise RuntimeError("zip contained no .nc")
            with z.open(ncs[0]) as src, open(final, "wb") as dst:
                shutil.copyfileobj(src, dst)
        os.remove(tmp)
    else:
        os.replace(tmp, final)


_print_lock = threading.Lock()


def safe_print(msg):
    with _print_lock:
        print(msg, flush=True)


def download_task(task):
    name, family, accum, stat, freq, year, months = task
    final = out_path_for(name, stat, year)
    label = f"{name}/{stat}/{year}"

    if os.path.exists(final):
        if is_valid(final):
            return (label, "skip", None)
        os.remove(final)

    tmp = f"{final}.part.{threading.get_ident()}"
    dataset = PL_DATASET if family == "pl" else SL_DATASET

    request = {
        "product_type": "reanalysis",
        "variable": [name],
        "year": [year],
        "month": months,
        "day": DAYS,
        "daily_statistic": stat,
        "time_zone": TIME_ZONE,
        "frequency": freq,
        "area": AREA,
        "data_format": "netcdf",
    }
    if family == "pl":
        request["pressure_level"] = PRESSURE_LEVELS

    try:
        client = cdsapi.Client(quiet=True, wait_until_complete=True)
        client.retrieve(dataset, request, tmp)
        finalize(tmp, final)
        if not is_valid(final):
            raise RuntimeError("downloaded file failed validation")
        return (label, "done", None)
    except Exception as e:
        for p in (tmp, final):
            if os.path.exists(p):
                try:
                    os.remove(p)
                except OSError:
                    pass
        return (label, "fail", str(e))


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

if __name__ == "__main__":
    t0 = time.time()

    # Pre-scan so the progress counter reflects real work
    todo = [t for t in tasks if not is_valid(out_path_for(t[0], t[3], t[5]))]
    n_skip = len(tasks) - len(todo)
    print(f"{n_skip} already valid, {len(todo)} to download.\n")

    done = fail = 0
    fails = []
    completed = 0
    total = len(todo)

    with ThreadPoolExecutor(max_workers=N_WORKERS) as pool:
        futures = {pool.submit(download_task, t): t for t in todo}
        for fut in as_completed(futures):
            label, status, err = fut.result()
            completed += 1
            if status == "done":
                done += 1
                safe_print(f"  [{completed:>4}/{total}] {label}: done")
            else:
                fail += 1
                fails.append(label)
                short = err[:180] + "..." if err and len(err) > 180 else err
                safe_print(f"  [{completed:>4}/{total}] {label}: FAILED: {short}")

    mins = (time.time() - t0) / 60.0
    print("\n" + "=" * 60)
    print(f"DONE in {mins:.1f} min — {done} downloaded, {n_skip} pre-existing, {fail} failed")
    print("=" * 60)
    if fails:
        print("Failed tasks (re-run to retry; valid files are skipped):")
        for f in fails[:40]:
            print(f"  {f}")
        if len(fails) > 40:
            print(f"  ... and {len(fails) - 40} more")
