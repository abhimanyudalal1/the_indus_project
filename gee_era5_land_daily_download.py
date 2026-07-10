import os
import time
import requests
import threading
from datetime import date
from concurrent.futures import ThreadPoolExecutor, as_completed
import ee

# ============================================================
# Google Earth Engine (GEE) - ERA5-Land Daily Download
# ------------------------------------------------------------
# Mirrors the concurrency and structure of your CDS script.
# Uses Earth Engine to fetch ECMWF/ERA5_LAND/HOURLY data,
# aggregates it to daily sums (for precipitation), and downloads
# each month as a multi-band GeoTIFF file.
# ============================================================

# Initialize Earth Engine. (Run `ee.Authenticate()` once if needed)
try:
    ee.Initialize()
except Exception as e:
    print("Please run `ee.Authenticate()` in your terminal/notebook first.")
    raise e

# ---- Setup ----
DOWNLOAD_DIR = r"D:\00. PHD Project\1st Objective. SM downscaling\1. PHYSICS BASED DL MODEL\SYNTHETIC_IRRIGATION_PIPELINE\step0b_extended_pet\downloads_gee_era5_land"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Area: [West, South, East, North] for the ENTIRE INDIA
AREA = [68.0, 6.0, 98.0, 38.0]
geom = ee.Geometry.Rectangle(AREA)

# Parallel workers for downloading (GEE can handle ~5-10 concurrent small requests well)
N_WORKERS = 4

START_YEAR, START_MONTH = 1980, 1
LAG_MONTHS = 2

# ---- Date range (DYNAMIC) ----
today = date.today()
end_y, end_m = today.year, today.month
for _ in range(LAG_MONTHS):
    end_m -= 1
    if end_m == 0:
        end_m = 12
        end_y -= 1

year_months = []
y, m = START_YEAR, START_MONTH
while (y, m) <= (end_y, end_m):
    year_months.append((str(y), f"{m:02d}"))
    m += 1
    if m == 13:
        m = 1
        y += 1

print(f"Today is        : {today}")
print(f"Date range      : {year_months[0][0]}-{year_months[0][1]}  →  {year_months[-1][0]}-{year_months[-1][1]}")
print(f"Months per var  : {len(year_months)}")
print(f"Parallel workers: {N_WORKERS}")
print(f"Output dir      : {DOWNLOAD_DIR}")
print("Setup done.\n")

# ---- Variable specs ----
VARIABLES = [
    ("tp_daily", {
        "collection": "ECMWF/ERA5_LAND/HOURLY",
        "band": "total_precipitation",
        "statistic": "sum",  # Hourly to daily using sum()
        "scale": 27830       # ~0.25 degrees resolution in meters
    }),
]

# ---- Helpers ----
def is_valid_file(fpath):
    try:
        # A valid downloaded tif is typically > 100 bytes. 
        # (GEE returns small error XMLs or text files if failed, which are tiny, but we use raise_for_status)
        if fpath.endswith('.tif') and os.path.getsize(fpath) > 100:
            return True
        return False
    except Exception:
        return False

def scan_existing(name, var_dir):
    needs = []
    n_valid = n_missing = n_corrupt = n_partial = 0
    for f in (os.listdir(var_dir) if os.path.isdir(var_dir) else []):
        if f.endswith(".part") or ".part." in f:
            try:
                os.remove(os.path.join(var_dir, f))
                n_partial += 1
            except OSError:
                pass
    for year, month in year_months:
        outfile = os.path.join(var_dir, f"{name}_{year}_{month}.tif")
        if not os.path.exists(outfile):
            needs.append((year, month))
            n_missing += 1
        elif is_valid_file(outfile):
            n_valid += 1
        else:
            try:
                os.remove(outfile)
            except OSError:
                pass
            needs.append((year, month))
            n_corrupt += 1
    return needs, n_valid, n_missing, n_corrupt, n_partial

_print_lock = threading.Lock()
def safe_print(msg):
    with _print_lock:
        print(msg, flush=True)

def download_one_month(name, specs, year, month, var_dir):
    """
    Constructs a monthly image of daily precipitation, grabs the GEE download URL, 
    and saves as a multi-band GeoTIFF (.tif).
    """
    final_path = os.path.join(var_dir, f"{name}_{year}_{month}.tif")
    part_path  = f"{final_path}.part.{threading.get_ident()}"
    
    try:
        y, m = int(year), int(month)
        start_date = ee.Date.fromYMD(y, m, 1)
        end_date = start_date.advance(1, 'month')
        
        # Base hourly collection
        col = ee.ImageCollection(specs["collection"]) \
                .filterDate(start_date, end_date) \
                .select(specs["band"])
        
        # Calculate daily values
        num_days = end_date.difference(start_date, 'day')
        
        def compute_daily(day_offset):
            d_start = start_date.advance(ee.Number(day_offset), 'day')
            d_end = d_start.advance(1, 'day')
            
            # GEE ERA5-Land HOURLY precipitation is un-accumulated. 
            # Summing the 24 hourly images gets the daily total.
            daily_img = col.filterDate(d_start, d_end).sum()
            return daily_img.set('system:time_start', d_start.millis())
        
        # Create a list of daily images and convert to an ImageCollection
        daily_list = ee.List.sequence(0, num_days.subtract(1)).map(compute_daily)
        daily_col = ee.ImageCollection(daily_list)
        
        # Convert ImageCollection to a single multi-band image for the month
        # Band names will automatically be '0_total_precipitation', '1_total_precipitation', etc.
        month_img = daily_col.toBands()
        
        # Get Download URL as GeoTIFF
        url = month_img.getDownloadURL({
            'region': geom,
            'scale': specs["scale"],
            'format': 'GEO_TIFF'
        })
        
        # Download the file atomically
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(part_path, 'wb') as fd:
            for chunk in response.iter_content(chunk_size=1024*1024):
                fd.write(chunk)
                
        os.replace(part_path, final_path)
        return (year, month, True, None)
        
    except Exception as e:
        if os.path.exists(part_path):
            try:
                os.remove(part_path)
            except OSError:
                pass
        return (year, month, False, str(e))

def download_variable(name, specs):
    var_dir = os.path.join(DOWNLOAD_DIR, name)
    os.makedirs(var_dir, exist_ok=True)
    print("=" * 60)
    print(f"{name}  ({specs['collection']})")
    print("=" * 60)
    t0 = time.time()

    print("  Scanning existing files...", end=" ", flush=True)
    needs, n_valid, n_missing, n_corrupt, n_partial = scan_existing(name, var_dir)
    parts = [f"{n_valid} valid"]
    if n_missing: parts.append(f"{n_missing} missing")
    if n_corrupt: parts.append(f"{n_corrupt} corrupted (deleted)")
    if n_partial: parts.append(f"{n_partial} partial (deleted)")
    print(", ".join(parts))

    if not needs:
        elapsed = (time.time() - t0) / 60.0
        print(f"  → nothing to do  ({elapsed:.1f} min)\n")
        return 0

    print(f"  Downloading {len(needs)} month(s) with {N_WORKERS} parallel workers...")
    n_done = n_fail = 0
    completed = 0
    total = len(needs)

    with ThreadPoolExecutor(max_workers=N_WORKERS) as pool:
        futures = {
            pool.submit(download_one_month, name, specs, year, month, var_dir): (year, month)
            for year, month in needs
        }
        for fut in as_completed(futures):
            year, month, ok, err = fut.result()
            completed += 1
            if ok:
                n_done += 1
                safe_print(f"    [{completed:>3}/{total}] {year}-{month}: done")
            else:
                n_fail += 1
                err_short = (err[:140] + '...') if len(err) > 140 else err
                safe_print(f"    [{completed:>3}/{total}] {year}-{month}: FAILED: {err_short}")

    elapsed = (time.time() - t0) / 60.0
    summary = f"  → {name}: {n_done} downloaded, {n_valid} pre-existing valid"
    if n_corrupt: summary += f", {n_corrupt} corrupted re-attempted"
    if n_fail:    summary += f", {n_fail} FAILED"
    summary += f"  ({elapsed:.1f} min)"
    print(summary + "\n")
    return n_fail

if __name__ == "__main__":
    overall_t0 = time.time()
    fail_summary = {}

    for name, specs in VARIABLES:
        fails = download_variable(name, specs)
        fail_summary[name] = fails

    total_min = (time.time() - overall_t0) / 60.0

    print("=" * 60)
    print("GEE ERA5-Land — ALL VARIABLES COMPLETE")
    print("=" * 60)
    print(f"Total wall time: {total_min:.1f} min")
    any_fails = sum(fail_summary.values())
    if any_fails:
        print(f"\n⚠ Failures by variable: {fail_summary}")
        print("  Re-run this script — already-valid files will be skipped.")
    else:
        print("\n✓ No failures.")
