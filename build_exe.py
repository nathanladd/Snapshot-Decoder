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
    (os.path.join(script_dir, 'data/images'), 'data/images'),  # All images (logo, icons, help screenshots)
    (os.path.join(script_dir, 'data/help'), 'data/help'),  # Help files
]

# Define hidden imports (modules that PyInstaller might miss)
hidden_imports = [
    'PySide6',
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'pandas',
    'matplotlib',
    'matplotlib.backends.backend_qtagg',  # PySide6 canvas
    'matplotlib.backends.backend_agg',    # Chart cart thumbnails
    'matplotlib.backends.backend_pdf',    # PDF export
    'mplcursors',
    'openpyxl',  # For reading .xlsx files
    'numpy',
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
    '--collect-all=PySide6',  # Collect all PySide6 modules and plugins
])

# Exclude modules not used by this application to reduce build size
exclude_modules = [
    # Chromium / web engine (removed – using default browser instead)
    'PySide6.QtWebEngineWidgets',
    'PySide6.QtWebEngineCore',
    'PySide6.QtWebChannel',
    # Heavy Qt modules not used by this app
    'PySide6.Qt3DCore',
    'PySide6.Qt3DRender',
    'PySide6.Qt3DInput',
    'PySide6.Qt3DLogic',
    'PySide6.Qt3DAnimation',
    'PySide6.Qt3DExtras',
    'PySide6.QtMultimedia',
    'PySide6.QtMultimediaWidgets',
    'PySide6.QtQml',
    'PySide6.QtQuick',
    'PySide6.QtQuickWidgets',
    'PySide6.QtBluetooth',
    'PySide6.QtNfc',
    'PySide6.QtPositioning',
    'PySide6.QtSensors',
    'PySide6.QtSerialPort',
    'PySide6.QtSql',
    'PySide6.QtTest',
    'PySide6.QtXml',
    'PySide6.QtDesigner',
    'PySide6.QtHelp',
    'PySide6.QtOpenGL',
    'PySide6.QtOpenGLWidgets',
    'PySide6.QtSvgWidgets',
    'PySide6.QtPdf',
    'PySide6.QtPdfWidgets',
    # tkinter – not used (PySide6 app), pulled in by matplotlib default backend
    'tkinter',
    '_tkinter',
    'tk',
    'tcl',
]
for mod in exclude_modules:
    pyinstaller_args.append(f'--exclude-module={mod}')

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

    # ---- Post-build cleanup: strip unused Qt modules from dist ----
    # --collect-all=PySide6 copies every file in the package; we only use
    # QtCore, QtGui, QtWidgets, and QtNetwork (implicit dep). Everything
    # else is dead weight. Match filenames/dirs whose lowercase form
    # contains any of these substrings and delete them.
    import shutil
    from pathlib import Path

    dist_internal = os.path.join(script_dir, 'dist', 'Snapshot Decoder', '_internal')

    # Substrings to match (case-insensitive) in file/dir names
    remove_substrings = [
        'webengine', 'webchannel',
        'qt3d', 'qt63d',
        'qtbluetooth', 'qt6bluetooth',
        'qtcharts', 'qt6charts',
        'qtdatavisualization', 'qt6datavisualization',
        'qtdesigner', 'qt6designer',
        'qtgraphs', 'qt6graphs',
        'qthelp', 'qt6help',
        'qthttpserver', 'qt6httpserver',
        'qtlabs', 'qt6labs',
        'qtlocation', 'qt6location',
        'qtmultimedia', 'qt6multimedia',
        'qtnfc', 'qt6nfc',
        'qtopengl', 'qt6opengl',
        'qtpdf', 'qt6pdf',
        'qtpositioning', 'qt6positioning',
        'qtqml', 'qt6qml',
        'qtquick', 'qt6quick',
        'qtremoteobjects', 'qt6remoteobjects',
        'qtscxml', 'qt6scxml',
        'qtsensors', 'qt6sensors',
        'qtserialbus', 'qt6serialbus',
        'qtserialport', 'qt6serialport',
        'qtshadertools', 'qt6shadertools',
        'qtspatialaudio', 'qt6spatialaudio',
        'qtsql', 'qt6sql',
        'qtstatemachine', 'qt6statemachine',
        'qtsvg', 'qt6svg',
        'qttest', 'qt6test',
        'qttexttospeech', 'qt6texttospeech',
        'qtuitools', 'qt6uitools',
        'qtvirtualkeyboard', 'qt6virtualkeyboard',
        'qtwebsockets', 'qt6websockets',
        'qtwebview', 'qt6webview',
        'qtxml', 'qt6xml',
    ]

    def _should_remove(name_lower):
        return any(s in name_lower for s in remove_substrings)

    removed_bytes = 0
    removed_count = 0

    # Walk bottom-up so directory removals don't interfere with traversal
    for dirpath, dirnames, filenames in os.walk(dist_internal, topdown=False):
        # Remove matching files
        for fname in filenames:
            if _should_remove(fname.lower()):
                fpath = os.path.join(dirpath, fname)
                try:
                    removed_bytes += os.path.getsize(fpath)
                    os.remove(fpath)
                    removed_count += 1
                except OSError:
                    pass
        # Remove matching directories
        for dname in dirnames:
            if _should_remove(dname.lower()):
                dpath = os.path.join(dirpath, dname)
                try:
                    removed_bytes += sum(
                        f.stat().st_size for f in Path(dpath).rglob('*') if f.is_file()
                    )
                    shutil.rmtree(dpath)
                    removed_count += 1
                except OSError:
                    pass

    # Also remove the qml/ directory entirely (QML engine not used)
    qml_dir = os.path.join(dist_internal, 'PySide6', 'qml')
    if os.path.isdir(qml_dir):
        removed_bytes += sum(
            f.stat().st_size for f in Path(qml_dir).rglob('*') if f.is_file()
        )
        shutil.rmtree(qml_dir)
        removed_count += 1

    if removed_count:
        print(f"\nPost-build cleanup: removed {removed_count} unused items "
              f"({removed_bytes / 1_048_576:.1f} MB saved)")

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
