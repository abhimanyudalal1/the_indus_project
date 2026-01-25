# Indus Project Setup Guide

## 1. Create Virtual Environment

```bash
cd /Users/abhimanyu/Desktop/projects/the_indus_project

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
```

## 2. Install Python Packages

```bash
# Install all required packages
pip install -r requirements.txt

# Upgrade pip if needed
pip install --upgrade pip
```

## 3. Enable Jupyter Widget Extensions

```bash
# Enable widgets for Jupyter (optional - VS Code has built-in support)
# If you get "command not found", you can skip this step

# Try these commands (if jupyter-nbextension is available):
jupyter nbextension enable --py widgetsnbextension
jupyter nbextension enable --py --sys-prefix ipyleaflet

# Alternative: Just ensure ipywidgets is installed
pip install --upgrade ipywidgets ipyleaflet

# VS Code should handle widget rendering automatically
```

**Note:** VS Code Jupyter has built-in widget support, so these commands are optional. If they fail, it's okay - just make sure the packages are installed via pip.

## 4. Authenticate Google Earth Engine

```bash
# First time only - authenticate with Google Earth Engine
earthengine authenticate

# Follow the browser prompts to authenticate
```

## 5. VS Code Extensions

Install these extensions in VS Code:

1. **Jupyter** (`ms-toolsai.jupyter`)
2. **Python** (`ms-python.python`)
3. **Jupyter Notebook Renderers** (`ms-toolsai.jupyter-renderers`)

You can install them via:
- VS Code Command Palette (Cmd+Shift+P) → "Extensions: Install Extensions"
- Or click the Extensions icon in the sidebar and search for each

## 6. Select Python Interpreter in VS Code

1. Open Command Palette (Cmd+Shift+P)
2. Type "Python: Select Interpreter"
3. Choose the interpreter from your `venv` folder:
   `/Users/abhimanyu/Desktop/projects/the_indus_project/venv/bin/python`

## 7. Test Your Setup

Open `indusshapefileu.ipynb` and run the first cell. If it runs without errors, you're all set!

## Troubleshooting

### Map not displaying in notebook?
- Use Method 1 (Cell 3) with `IPython.display.HTML`
- Or use Method 2 (Cell 4) to open in browser

### "Module not found" error?
- Make sure virtual environment is activated
- Verify you selected the correct Python interpreter in VS Code
- Reinstall packages: `pip install -r requirements.txt`

### Earth Engine authentication issues?
- Run: `earthengine authenticate`
- Make sure you have a Google Earth Engine account
- Visit: https://earthengine.google.com/signup/

## Project Structure

```
the_indus_project/
├── venv/                      # Virtual environment (created by you)
├── data_downloader.py         # NASA POWER API data downloader
├── indusshapefileu.ipynb      # Upper Indus Basin shapefile notebook
├── uindus_shapefile.py        # Python script version
├── requirements.txt           # Python dependencies
├── setup.md                   # This file
└── README.md                  # Project documentation
```

## Deactivate Virtual Environment

When you're done working:

```bash
deactivate
```
