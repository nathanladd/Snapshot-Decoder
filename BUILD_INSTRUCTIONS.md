# Building Snapshot Decoder Executable

This guide explains how to build a single-file executable (.exe) for the Snapshot Decoder application.

## Prerequisites

1. **Python 3.8 or higher** installed
2. **All project dependencies** installed (see requirements below)
3. **PyInstaller** installed

## Installation Steps

### 1. Install PyInstaller

```bash
pip install pyinstaller
```

### 2. Verify All Dependencies

Make sure all required packages are installed:

```bash
pip install pandas matplotlib openpyxl xlrd pillow
```

## Building the Executable

### Simple Method

Run the build script:

```bash
python build_exe.py
```

### What Happens During Build

The build script will:
- Create a single-file executable named `SnapshotDecoder.exe`
- Bundle all Python dependencies
- Include the logo.png file for PDF exports
- Include the application icon
- Package matplotlib and pandas data files
- Create a GUI application (no console window)

### Build Output

After successful build, you'll find:
- **Executable**: `dist/SnapshotDecoder.exe`
- **Build files**: `build/` folder (can be deleted)
- **Spec file**: `SnapshotDecoder.spec` (auto-generated)

## Distribution

The single file `dist/SnapshotDecoder.exe` can be distributed to users. It contains:
- All Python code
- All dependencies
- Logo and icon files
- Everything needed to run the application

**Note**: The executable is platform-specific. A Windows .exe will only run on Windows.

## File Size

The single-file executable will be approximately 80-150 MB due to:
- Python interpreter
- Pandas and NumPy libraries
- Matplotlib and its dependencies
- Tkinter GUI framework

## Troubleshooting

### Build Fails

If the build fails:
1. Check that all dependencies are installed
2. Try running with `--debug=all` flag for more information
3. Ensure you have write permissions in the project directory

### Missing Modules at Runtime

If the executable fails with "ModuleNotFoundError":
1. Add the missing module to `hidden_imports` in `build_exe.py`
2. Rebuild the executable

### Logo Not Found

If the logo doesn't appear in PDFs:
1. Ensure `logo.png` exists in the project root
2. Check that it's listed in the `datas` section of `build_exe.py`
3. Rebuild the executable

### Icon Not Applied

If the executable doesn't have the correct icon:
1. Ensure `Snapshot_Decoder_Icon.ico` exists
2. Verify the path in `build_exe.py`
3. Rebuild the executable

## Advanced Options

### Creating a Directory-Based Build

To create a folder with separate files instead of a single executable:
- Change `--onefile` to `--onedir` in `build_exe.py`

### Including Console Window (for debugging)

To show a console window for debugging:
- Remove `--windowed` from `build_exe.py`

### Customizing the Build

Edit `build_exe.py` to:
- Add more data files to `datas` list
- Add more hidden imports to `hidden_imports` list
- Change the executable name
- Modify PyInstaller options

## Testing the Executable

After building:
1. Navigate to `dist/` folder
2. Double-click `SnapshotDecoder.exe`
3. Test all features:
   - Opening snapshot files
   - Creating charts
   - Exporting to PDF
   - Verify logo appears in PDFs

## Clean Build

To perform a clean build (recommended if you encounter issues):

```bash
# Delete build artifacts
rmdir /s /q build dist
del SnapshotDecoder.spec

# Run build again
python build_exe.py
```

## Version Information

The executable will use the version defined in `domain/constants.py`:
- `APP_TITLE = "Snapshot Decoder"`
- `APP_VERSION = "1.0.0 (Beta)"`

Update these values before building a release version.
