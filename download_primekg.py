"""
Download PrimeKG from Harvard Dataverse (doi:10.7910/DVN/IXA7BM).
Files land in ./data/primekg/.
"""

import requests
from pathlib import Path
from tqdm import tqdm

DATA_DIR = Path(__file__).parent / "data" / "primekg"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Harvard Dataverse file IDs for PrimeKG (doi:10.7910/DVN/IXA7BM)
# Full listing: curl https://dataverse.harvard.edu/api/datasets/export?exporter=dataverse_json&persistentId=doi:10.7910/DVN/IXA7BM
FILES = {
    "nodes.csv":           "6180617",   # 129K nodes (node_index, node_id, node_type, node_name, node_source)
    "edges.csv":           "6180616",   # ~4.1M edges, 386 MB (x_index, y_index, relation, display_relation, etc.)
    "drug_features.csv":   "6180619",   # drug molecular features
    "disease_features.csv":"6180618",   # disease BERT embeddings (114 MB)
}

BASE = "https://dataverse.harvard.edu/api/access/datafile/"

def download(name: str, file_id: str) -> None:
    dest = DATA_DIR / name
    if dest.exists() and dest.stat().st_size > 1_000:
        print(f"  [skip] {name} already present ({dest.stat().st_size/1e6:.1f} MB)")
        return
    url = BASE + file_id
    print(f"  Downloading {name} from {url} ...")
    r = requests.get(url, stream=True, timeout=120)
    r.raise_for_status()
    total = int(r.headers.get("content-length", 0))
    with open(dest, "wb") as f, tqdm(total=total, unit="B", unit_scale=True,
                                      desc=name, ncols=80) as bar:
        for chunk in r.iter_content(chunk_size=1 << 17):
            f.write(chunk)
            bar.update(len(chunk))
    print(f"  Saved → {dest}")

if __name__ == "__main__":
    print("=== PrimeKG downloader ===")
    for name, fid in FILES.items():
        download(name, fid)
    print("\nDone. All files in:", DATA_DIR)
