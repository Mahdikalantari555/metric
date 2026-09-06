# %%
"""
METRIC Dataset Preparation Script

This script:
1. Clones the METRIC repo
2. Installs dependencies
3. Downloads Landsat scenes **year-by-year** via run_metric_workflow.py
4. Zips scenes/ and products/ **per year** (e.g. 2023_scenes.zip, 2023_products.zip)
5. Pushes zips to a Hugging Face dataset repo with **resume & dedup**

If the connection drops, re-run the script -- completed years are skipped automatically.

Configure the parameters below before running.
"""

# %%
# Cell 1: Setup paths and clone repo
import os
import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime

# --- Detect Colab vs local ---
IN_COLAB = "google.colab" in sys.modules
if IN_COLAB:
    from google.colab import drive
    drive.mount("/content/drive")
    WORKSPACE_ROOT = Path("/content")
    DRIVE_STATE_DIR = Path("/content/drive/MyDrive/metric_hf_state")
    DRIVE_STATE_DIR.mkdir(parents=True, exist_ok=True)
else:
    WORKSPACE_ROOT = Path("/home/asus/Projects/metric").resolve()
    DRIVE_STATE_DIR = None

# --- Configuration ---
REPO_URL = "https://github.com/Mahdikalantari555/metric.git"
CLONE_DIR = WORKSPACE_ROOT / "metric_repo"
HF_DATASET_REPO = "mahdi555/MetricData"  # change to your HF dataset repo
ZIP_OUTPUT_DIR = WORKSPACE_ROOT / "zips"
STATE_FILE = (DRIVE_STATE_DIR / "hf_prep_state.json") if DRIVE_STATE_DIR else WORKSPACE_ROOT / "hf_prep_state.json"
# ----------------------

ZIP_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

if not CLONE_DIR.exists():
    print(f"Cloning {REPO_URL} -> {CLONE_DIR}")
    subprocess.run(["git", "clone", "--depth", "1", REPO_URL, str(CLONE_DIR)], check=True)
else:
    print(f"Repo already exists at {CLONE_DIR}, pulling latest...")
    subprocess.run(["git", "-C", str(CLONE_DIR), "pull"], check=False)

sys.path.insert(0, str(CLONE_DIR / "metric_et"))
print(f"Repo ready at: {CLONE_DIR}")

# --- Checkpoint helpers (state lives on Google Drive if Colab) ---
def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"completed_years": [], "uploaded_zips": []}

def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))

state = load_state()
print(f"State loaded from: {STATE_FILE}")
print(f"  completed years: {state['completed_years']}")
print(f"  uploaded zips:   {state['uploaded_zips']}")

# %%
# Cell 2: Install Python dependencies
print("Installing dependencies...")
subprocess.run(
    [sys.executable, "-m", "pip", "install", "-e", str(CLONE_DIR), "--quiet"],
    check=False
)

EXTRA_PACKAGES = [
    "huggingface_hub>=0.20.0",
    "stackstac>=0.1.0",
    "pystac-client>=0.7.0",
    "planetary-computer>=1.0.0",
]
subprocess.run(
    [sys.executable, "-m", "pip", "install", *EXTRA_PACKAGES, "--quiet"],
    check=False
)
print("Dependencies installed.")

# %%
# Cell 3: Helpers -- split date range into years + zip with dedup
import zipfile

def split_by_year(start_date: str, end_date: str):
    """Split a date range into (year_start, year_end) tuples per calendar year."""
    years = []
    cur = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    while cur <= end:
        ys = cur
        ye = datetime(cur.year, 12, 31)
        if ye > end:
            ye = end
        years.append((ys.strftime("%Y-%m-%d"), ye.strftime("%Y-%m-%d")))
        cur = datetime(cur.year + 1, 1, 1)
    return years

def zip_directory(directory: Path, zip_path: Path, skip_if_exists: bool = True):
    """Zip a directory, skipping if zip already exists."""
    if skip_if_exists and zip_path.exists():
        print(f"Zip already exists, skipping: {zip_path.name}")
        return zip_path
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in directory.rglob("*"):
            if file.is_file():
                arcname = file.relative_to(directory)
                zf.write(file, arcname)
    print(f"Created zip: {zip_path.name}  ({zip_path.stat().st_size / 1024 / 1024:.1f} MB)")
    return zip_path

print("Helpers ready.")

# %%
# Cell 4: Configure date range and run workflow per year
import logging
from pathlib import Path

# --- Workflow Configuration ---
ROI_PATH = "/content/drive/MyDrive/Path/to/RoI/Extent.geojson"  # UPDATE THIS
START_DATE = "2023-07-01"
END_DATE = "2023-07-10"
AOI_NAME = "AOI"
MAX_CLOUD_COVER = 50.0
SOURCE_CRS = "EPSG:4326"
INTERPOLATION_METHOD = "weighted"
EXTRAPOLATION_DAYS = 14
INCLUDE_SURFACE = True
SAVE_SCENES = True
VISUALIZATION = False
# ------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    force=True,
)

from run_metric_workflow import METRICWorkflow

year_ranges = split_by_year(START_DATE, END_DATE)
print(f"Date range spans {len(year_ranges)} year(s): {year_ranges}")

for yr_start, yr_end in year_ranges:
    year = datetime.strptime(yr_start, "%Y-%m-%d").year
    year_tag = str(year)

    if year_tag in state["completed_years"]:
        print(f"Skipping {year}: already completed")
        continue

    print(f"\n{'='*60}")
    print(f"Processing year {year}: {yr_start} -> {yr_end}")
    print(f"{'='*60}")

    year_output_dir = CLONE_DIR / "output" / f"metric_run_{year}"
    year_output_dir.mkdir(parents=True, exist_ok=True)

    workflow = METRICWorkflow(
        roi_path=ROI_PATH,
        output_dir=str(year_output_dir),
        start_date=yr_start,
        end_date=yr_end,
        aoi_name=AOI_NAME,
        max_cloud_cover=MAX_CLOUD_COVER,
        source_crs=SOURCE_CRS,
        interpolation_method=INTERPOLATION_METHOD,
        extrapolation_days=EXTRAPOLATION_DAYS,
        include_surface=INCLUDE_SURFACE,
        save_scenes=SAVE_SCENES,
        visualization=VISUALIZATION,
    )

    try:
        results = workflow.run()
        print(f"Workflow results for {year}:", results)
        state["completed_years"].append(year_tag)
        save_state(state)
        print(f"Year {year} completed and checkpoint saved.")
    except Exception as e:
        print(f"Year {year} FAILED: {e}")
        print("Re-run the script later to retry this year.")
        raise

print("\nAll requested years processed.")

# %%
# Cell 5: Zip scenes and products per year
for yr_start, yr_end in year_ranges:
    year = datetime.strptime(yr_start, "%Y-%m-%d").year
    year_tag = str(year)

    year_output_dir = CLONE_DIR / "output" / f"metric_run_{year}"
    scenes_dir = year_output_dir / "scenes"
    products_dir = year_output_dir / "products"

    scenes_zip = ZIP_OUTPUT_DIR / f"{year_tag}_scenes.zip"
    products_zip = ZIP_OUTPUT_DIR / f"{year_tag}_products.zip"

    if scenes_dir.exists():
        zip_directory(scenes_dir, scenes_zip, skip_if_exists=True)
    else:
        print(f"Scenes directory not found for {year}: {scenes_dir}")

    if products_dir.exists():
        zip_directory(products_dir, products_zip, skip_if_exists=True)
    else:
        print(f"Products directory not found for {year}: {products_dir}")

print("Zipping complete.")

# %%
# Cell 6: Push zips to Hugging Face dataset repo
from huggingface_hub import HfApi, create_dataset_repo

HF_TOKEN = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_TOKEN")
if not HF_TOKEN:
    token_path = Path.home() / ".cache" / "huggingface" / "token"
    if token_path.exists():
        HF_TOKEN = token_path.read_text().strip()

if not HF_TOKEN:
    from huggingface_hub import notebook_login
    print("No HF token found. Logging in interactively...")
    notebook_login()
    # After login, re-read token from cache
    token_path = Path.home() / ".cache" / "huggingface" / "token"
    if token_path.exists():
        HF_TOKEN = token_path.read_text().strip()

if not HF_TOKEN:
    raise ValueError(
        "No HF token found. Set HF_TOKEN env var or save token via `huggingface-cli login`."
    )

api = HfApi(token=HF_TOKEN)

# Create dataset repo if it doesn't exist
try:
    create_dataset_repo(repo_id=HF_DATASET_REPO, token=HF_TOKEN, repo_type="dataset", private=False)
    print(f"Dataset repo ready: {HF_DATASET_REPO}")
except Exception as e:
    print(f"Repo creation note: {e}")

# Build list of zips to upload
zips_to_upload = []
for yr_start, yr_end in year_ranges:
    year = datetime.strptime(yr_start, "%Y-%m-%d").year
    year_tag = str(year)
    scenes_zip = ZIP_OUTPUT_DIR / f"{year_tag}_scenes.zip"
    products_zip = ZIP_OUTPUT_DIR / f"{year_tag}_products.zip"
    for zp in [scenes_zip, products_zip]:
        if zp.exists():
            zips_to_upload.append(zp)
        else:
            print(f"Zip not found, skipping upload: {zp.name}")

# Upload, skipping already-uploaded zips
for zip_path in zips_to_upload:
    zip_name = zip_path.name
    if zip_name in state["uploaded_zips"]:
        print(f"Already uploaded, skipping: {zip_name}")
        continue

    print(f"Uploading {zip_name} -> {HF_DATASET_REPO}")
    try:
        api.upload_file(
            path_or_fileobj=str(zip_path),
            path_in_repo=zip_name,
            repo_id=HF_DATASET_REPO,
            repo_type="dataset",
            token=HF_TOKEN,
        )
        state["uploaded_zips"].append(zip_name)
        save_state(state)
        print(f"Uploaded: https://huggingface.co/datasets/{HF_DATASET_REPO}/resolve/main/{zip_name}")
    except Exception as e:
        print(f"Upload failed for {zip_name}: {e}")
        raise

print("All done.")
