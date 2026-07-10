import json

with open("dds.ipynb", "r") as f:
    nb = json.load(f)

for cell in nb.get("cells", []):
    if cell.get("cell_type") == "code":
        source = "".join(cell.get("source", []))
        if "year_plan = []  # (year, [single_month]) pairs" in source:
            # We found the CDS download cell
            new_source = source.replace(
                "year_plan = []  # (year, [single_month]) pairs -- name kept for minimal diff\nfor y in range(START_YEAR, end_y + 1):\n    last_m = end_m if y == end_y else 12\n    for m in range(1, last_m + 1):\n        year_plan.append((str(y), [f\"{m:02d}\"]))",
                "year_plan = []\nfor y in range(START_YEAR, end_y + 1):\n    last_m = end_m if y == end_y else 12\n    m_h1 = [f\"{m:02d}\" for m in range(1, min(6, last_m) + 1)]\n    if m_h1: year_plan.append((str(y), m_h1))\n    if last_m > 6:\n        m_h2 = [f\"{m:02d}\" for m in range(7, last_m + 1)]\n        year_plan.append((str(y), m_h2))"
            )
            
            # Now update the download_task function to handle multiple months
            new_source = new_source.replace(
                "def download_task(task):\n    name, family, accum, stat, freq, year, months = task\n    month = months[0]\n    final = out_path_for(name, stat, year, month)\n    label = f\"{name}/{stat}/{year}-{month}\"",
                "def download_task(task):\n    name, family, accum, stat, freq, year, months = task\n    suffix = months[0] if len(months) == 1 else f\"{months[0]}-{months[-1]}\"\n    final = out_path_for(name, stat, year, suffix)\n    label = f\"{name}/{stat}/{year}-{suffix}\""
            )
            
            # And update the pre-scan loop to handle the suffix
            new_source = new_source.replace(
                "todo = [t for t in tasks if not is_valid(out_path_for(t[0], t[3], t[5], t[6][0]))]",
                "todo = [t for t in tasks if not is_valid(out_path_for(t[0], t[3], t[5], t[6][0] if len(t[6]) == 1 else f\"{t[6][0]}-{t[6][-1]}\"))]"
            )
            
            # Split back to list of strings
            lines = []
            for line in new_source.splitlines(True):
                lines.append(line)
            cell["source"] = lines

with open("dds.ipynb", "w") as f:
    json.dump(nb, f, indent=1)

print("Notebook updated successfully.")
