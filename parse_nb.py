import json

with open('/Users/abhimanyu/Downloads/ERA5_25km_DATA_DOWNLOAD_for_PET_2015-2026.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

for cell in reversed(nb['cells']):
    if cell['cell_type'] == 'code' and cell.get('outputs'):
        for output in cell['outputs']:
            if output.get('name') == 'stdout':
                lines = output['text']
                # Print the last 20 lines of the output
                print("".join(lines[-20:]))
                exit(0)
