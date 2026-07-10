import json

with open('/Users/abhimanyu/Downloads/ERA5_25km_DATA_DOWNLOAD_for_PET_2015-2026.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

for cell in reversed(nb['cells']):
    if cell['cell_type'] == 'code' and cell.get('outputs'):
        for output in cell['outputs']:
            if output.get('name') == 'stdout':
                text = "".join(output['text'])
                if 'tp_25km' in text:
                    lines = output['text']
                    error_lines = [l for l in lines if 'FAILED' in l]
                    print("Found tp_25km run! First 5 errors:")
                    print("".join(error_lines[:5]))
                    exit(0)
print("Could not find a run with tp_25km")
