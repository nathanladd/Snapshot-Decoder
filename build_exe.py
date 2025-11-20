"""
Build script for creating a single-file executable of Snapshot Decoder using PyInstaller.

Usage:
    python build_exe.py

Requirements:
    pip install pyinstaller
"""

import PyInstaller.__main__
import os
import sys

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Define the main entry point
main_script = os.path.join(script_dir, 'main.py')

# Define data files to include (format: 'source:destination')
# These files will be bundled with the executable
datas = [
    (os.path.join(script_dir, 'logo.png'), '.'),  # Logo for PDF exports
    (os.path.join(script_dir, 'Snapshot_Decoder_Icon.ico'), '.'),  # App icon
]

# Define hidden imports (modules that PyInstaller might miss)
hidden_imports = [
    'tkinter',
    'tkinter.ttk',
    'PIL._tkinter_finder',  # Required for PIL/Pillow with tkinter
    'pandas',
    'matplotlib',
    'matplotlib.backends.backend_tkagg',
    'openpyxl',  # For reading .xlsx files
    'xlrd',  # For reading .xls files
]

# Build the PyInstaller command
pyinstaller_args = [
    main_script,
    '--name=Snapshot Decoder',  # Name of the executable
    '--onefile',  # Create a single executable file
    '--windowed',  # No console window (GUI app)
    f'--icon={os.path.join(script_dir, "Snapshot_Decoder_Icon.ico")}',  # App icon
    '--clean',  # Clean PyInstaller cache before building
    '--noconfirm',  # Replace output directory without asking
]

# Add data files
for source, dest in datas:
    if os.path.exists(source):
        pyinstaller_args.append(f'--add-data={source}{os.pathsep}{dest}')
    else:
        print(f"Warning: Data file not found: {source}")

# Add hidden imports
for module in hidden_imports:
    pyinstaller_args.append(f'--hidden-import={module}')

# Additional options for better compatibility
pyinstaller_args.extend([
    '--collect-all=matplotlib',  # Collect all matplotlib data files
    '--collect-all=pandas',  # Collect all pandas data files
])

print("=" * 70)
print("Building Snapshot Decoder executable...")
print("=" * 70)
print(f"Main script: {main_script}")
print(f"Output directory: {os.path.join(script_dir, 'dist')}")
print("=" * 70)

# Run PyInstaller
try:
    PyInstaller.__main__.run(pyinstaller_args)
    print("\n" + "=" * 70)
    print("Build completed successfully!")
    print(f"Executable location: {os.path.join(script_dir, 'dist', 'Snapshot Decoder.exe')}")
    print("=" * 70)
except Exception as e:
    print(f"\nBuild failed with error: {e}", file=sys.stderr)
    sys.exit(1)
