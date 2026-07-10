import json

with open("ddsa250.ipynb", "r") as f:
    nb = json.load(f)

for cell in nb.get("cells", []):
    if cell.get("cell_type") == "code":
        source = "".join(cell.get("source", []))
        if "process_year(year)" in source and "pl = pl.load()" in source:
            # Add the import if not there
            if "from dask.diagnostics import ProgressBar" not in source:
                source = "from dask.diagnostics import ProgressBar\n" + source
            
            # Replace the load lines
            old_load = "        # Pull this month into memory once (bounded ~<1 GB for India box)\n        pl = pl.load()\n        sfc = sfc.load()"
            new_load = "        # Pull this month into memory once (bounded ~<1 GB for India box)\n        print(f\"    {year}-{m:02d} fetching from Google Cloud...\")\n        with ProgressBar():\n            pl = pl.load()\n            sfc = sfc.load()"
            
            new_source = source.replace(old_load, new_load)
            
            lines = []
            for line in new_source.splitlines(True):
                lines.append(line)
            cell["source"] = lines

with open("ddsa250.ipynb", "w") as f:
    json.dump(nb, f, indent=1)

print("ddsa250.ipynb updated.")
