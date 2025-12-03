"""
Build script for creating a multi-file (single directory) executable of Snapshot Decoder using PyInstaller.

Usage:
    python build_exe.py

Requirements:
    pip install pyinstaller
"""

import PyInstaller.__main__
import os
import sys

import re

# Read version from version.py
with open('version.py', 'r') as f:
    content = f.read()
match = re.search(r'APP_VERSION\s*=\s*["\']([^"\']+)["\']', content)
if match:
    version = match.group(1)
else:
    raise ValueError("APP_VERSION not found in version.py")

# Update the version number in create_installer.iss
with open('create_installer.iss', 'r') as f:
    iss_content = f.read()
iss_content = re.sub(r'#define MyAppVersion ".*?"', f'#define MyAppVersion "{version}"', iss_content)
with open('create_installer.iss', 'w') as f:
    f.write(iss_content)

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Define the main entry point
main_script = os.path.join(script_dir, 'main.py')

# Define data files to include (format: 'source:destination')
# These files will be bundled with the executable
datas = [
    (os.path.join(script_dir, 'data/images/logo.png'), 'data/images'),  # Logo for PDF exports
    (os.path.join(script_dir, 'data/images/Snapshot_Decoder_Icon.ico'), 'data/images'),  # App icon
    (os.path.join(script_dir, 'data/images/splash.png'), 'data/images'),  # Splash image
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
    '--onedir',  # Create a directory with executable and dependencies
    '--windowed',  # No console window (GUI app)
    f'--icon={os.path.join(script_dir, "data/images/Snapshot_Decoder_Icon.ico")}',  # App icon
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
    print(f"Output directory: {os.path.join(script_dir, 'dist', 'Snapshot Decoder')}")
    print("=" * 70)

    # Check for Inno Setup Compiler
    iscc_paths = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
    ]
    
    iscc_exe = None
    for path in iscc_paths:
        if os.path.exists(path):
            iscc_exe = path
            break
            
    if iscc_exe:
        print(f"\nFound Inno Setup Compiler at: {iscc_exe}")
        print("Compiling installer...")
        import subprocess
        iss_file = os.path.join(script_dir, 'create_installer.iss')
        try:
            subprocess.run([iscc_exe, iss_file], check=True)
            print("\n" + "=" * 70)
            print("Installer created successfully!")
            print(f"Installer location: {os.path.join(script_dir, 'SnapshotDecoder_Setup.exe')}")
            print("=" * 70)
        except subprocess.CalledProcessError as e:
            print(f"Installer compilation failed: {e}")
    else:
        print("\nInno Setup Compiler (ISCC.exe) not found.")
        print("To create the installer with uninstaller:")
        print("1. Install Inno Setup 6 (https://jrsoftware.org/isinfo.php)")
        print("2. Open 'create_installer.iss' and compile it")
        print("   OR add ISCC.exe to the script path check.")

except Exception as e:
    print(f"\nBuild failed with error: {e}", file=sys.stderr)
    sys.exit(1)
