# build.py

import os
import sys
import shutil
import subprocess
import glob
from datetime import datetime

# =============================================
# Settings
# =============================================

APP_NAME = "GasStationManager"
EXE_NAME = "Gas Station Management.exe"
ICON_FILE = "gas_station.ico"
MAIN_SCRIPT = "main.py"

# Data folders that must be bundled INTO the exe (in _MEIPASS).
# These are read-only resources used by get_resource_path().
BUNDLED_FOLDERS = [
    "fonts",
    "asset",
    "components",
    "utils",
]

# Hidden imports required by PyInstaller.
HIDDEN_IMPORTS = [
    "jdatetime",
    "tkinter",
    "PIL",
    "reportlab",
    "cryptography",
    "arabic_reshaper",
    "bidi",
]

# =============================================
# Helpers
# =============================================

def run_command(cmd, cwd=None, capture=True):
    """Run a command and stream its output."""
    print(f"\n-> Running: {' '.join(cmd)}")
    if capture:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True,
            text=True, encoding='utf-8', errors='replace'
        )
        if result.returncode != 0:
            print("Execution error:")
            print(result.stderr)
            sys.exit(1)
        print(result.stdout)
    else:
        process = subprocess.Popen(
            cmd, cwd=cwd,
            stdout=sys.stdout, stderr=sys.stderr, text=True
        )
        process.wait()
        if process.returncode != 0:
            sys.exit(1)


def clean_previous_builds():
    """Remove previous build artifacts."""
    folders = ['build', 'dist', '__pycache__']
    specs = glob.glob("*.spec")

    print("\nCleaning previous files...")
    for folder in folders:
        if os.path.exists(folder):
            shutil.rmtree(folder, ignore_errors=True)
            print(f"  Removed: {folder}")

    for spec in specs:
        try:
            os.remove(spec)
            print(f"  Removed: {spec}")
        except OSError:
            pass


def check_dependencies():
    """Ensure required build tools are installed."""
    required = ['pyinstaller', 'jdatetime']
    missing = []

    for pkg in required:
        try:
            __import__(pkg.replace('-', '_'))
        except ImportError:
            missing.append(pkg)

    if missing:
        print("\nInstalling required dependencies:")
        for pkg in missing:
            print(f"  -> pip install {pkg}")
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", pkg]
            )
        print("Installation complete.\n")


# =============================================
# Build
# =============================================

def build_executable():
    """Build the executable with all bundled resources."""
    print("\nBuilding executable (onedir mode)...")

    cmd = [
        "pyinstaller",
        "--onedir",
        "--windowed",
        f"--name={APP_NAME}",
        "--noconfirm",
        "--clean",
    ]

    # Icon: passed only once, and also added as data so it can be
    # loaded at runtime by get_resource_path().
    if os.path.exists(ICON_FILE):
        cmd.append(f"--icon={ICON_FILE}")
        cmd.append(f"--add-data={ICON_FILE};.")

    # Bundle resource folders into _MEIPASS so get_resource_path works.
    for folder in BUNDLED_FOLDERS:
        if os.path.exists(folder):
            cmd.append(f"--add-data={folder};{folder}")

    # Hidden imports
    for imp in HIDDEN_IMPORTS:
        cmd.append(f"--hidden-import={imp}")

    cmd.append(MAIN_SCRIPT)

    run_command(cmd, capture=False)

    exe_dir_path = os.path.join("dist", APP_NAME)
    if not os.path.exists(exe_dir_path):
        print("\nExecutable directory build failed.")
        sys.exit(1)

    print(f"Executable directory created at: {exe_dir_path}")


# =============================================
# Client package
# =============================================

def create_client_package():
    """
    Assemble the final folder delivered to the customer.

    Layout after this step:
        GasStationManager_Client_YYYYMMDD/
        |-- run.bat
        |-- readme.txt
        |-- GasStationManager/
            |-- Gas Station Management.exe
            |-- _internal/           (bundled by PyInstaller)
            |-- fonts/               (copied here so customer can edit)
            |-- asset/               (copied here so customer can edit)
            |-- gas_station.ico
            |-- data/                (created on first run)
    """
    print("\nCreating final client package...")

    pkg_folder = f"{APP_NAME}_Client_{datetime.now().strftime('%Y%m%d')}"
    if os.path.exists(pkg_folder):
        shutil.rmtree(pkg_folder, ignore_errors=True)
    os.makedirs(pkg_folder)

    src_exe_dir = os.path.join("dist", APP_NAME)
    dst_exe_dir = os.path.join(pkg_folder, APP_NAME)

    if not os.path.exists(src_exe_dir):
        print(f"Build output not found: {src_exe_dir}")
        sys.exit(1)

    shutil.copytree(src_exe_dir, dst_exe_dir)
    print(f"  Executable directory copied to {APP_NAME}")

    # Copy editable resources next to the exe.
    # The app expects them in application_path (see main.py),
    # not inside _internal, so the customer can replace the logo
    # or font without touching the bundled files.
    for folder in ["fonts", "asset"]:
        if os.path.exists(folder):
            target = os.path.join(dst_exe_dir, folder)
            if os.path.exists(target):
                shutil.rmtree(target, ignore_errors=True)
            shutil.copytree(folder, target)
            print(f"  {folder}/ copied next to executable")

    if os.path.exists(ICON_FILE):
        shutil.copy2(ICON_FILE, dst_exe_dir)
        print(f"  {ICON_FILE} copied")

    # Ensure an empty data folder exists so the app can write to it.
    data_dir = os.path.join(dst_exe_dir, "data")
    os.makedirs(data_dir, exist_ok=True)

    # run.bat
    bat_content = (
        "@echo off\r\n"
        "title Gas Station Management System\r\n"
        "echo Running...\r\n"
        f'"{APP_NAME}\\{EXE_NAME}"\r\n'
        "pause\r\n"
    )
    with open(
        os.path.join(pkg_folder, "run.bat"), "w", encoding="utf-8"
    ) as f:
        f.write(bat_content)

    # readme.txt for the customer
    readme = f"""Gas Station Management System
Version {datetime.now().strftime('%Y-%m')}

How to use:
  1. Double-click "run.bat".
  2. On first launch, an activation window appears.
     Copy the System ID and send it to support.
  3. Place the received "gas_station.license" file in this folder
     (next to run.bat), then run again.

Notes:
  - The "fonts" and "asset" folders next to the executable are editable.
    You may replace the logo with your own.
  - All shift data is stored in the "data" folder inside the app folder.

Support:
  Email: support@example.com
  Telegram: @your_support
"""
    with open(
        os.path.join(pkg_folder, "readme.txt"), "w", encoding="utf-8"
    ) as f:
        f.write(readme)

    print(f"Client package ready: {pkg_folder}")


def copy_license_generator():
    """Copy seller-only tools into Support_Tools/ (not shipped to customer)."""
    support_folder = "Support_Tools"
    os.makedirs(support_folder, exist_ok=True)

    for fname in ("license_generator.py", "license_manager.py"):
        if os.path.exists(fname):
            shutil.copy2(fname, support_folder)
            print(f"  {fname} copied to {support_folder}/")


# =============================================
# Main
# =============================================

def main():
    print("=" * 70)
    print(" Build Executable - Gas Station Management System ".center(70))
    print("=" * 70)

    check_dependencies()
    clean_previous_builds()
    build_executable()
    create_client_package()
    copy_license_generator()

    print("\nOperation completed successfully.")
    print(f"  Executable: dist/{APP_NAME}/{EXE_NAME}")
    print(f"  Client package: {APP_NAME}_Client_YYYYMMDD/")
    print("=" * 70)

    input("\nPress Enter to exit...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation interrupted by user.")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")