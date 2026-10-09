# build_no_license.py
# Build script for the portable version (no hardware lock, no license).
# Generates main_portable.py at build time, then packages everything
# into a ready-to-ship folder.

import os
import sys
import shutil
import subprocess
import glob
from datetime import datetime

# =============================================
# Settings
# =============================================

APP_NAME = "GasStationManager_Portable"
EXE_NAME = "Gas Station Management (Portable).exe"
ICON_FILE = "gas_station.ico"
MAIN_SCRIPT = "main_portable.py"   # generated below

# Read-only resources bundled inside the exe (_MEIPASS).
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
# Portable main.py generator
# =============================================

def create_portable_main():
    """
    Write main_portable.py to disk.

    This is a variant of main.py without the HardwareLock class
    and without the activation window. Uses the same
    get_resource_path() pattern for bundled resources.
    """
    print("\nCreating portable main file...")

    portable_main_content = '''# main_portable.py
# Portable edition: runs without a license file.
# Generated automatically by build_no_license.py.

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from PIL import Image, ImageTk
import json
import os
import sys

DEBUG = False


def debug_print(msg):
    if DEBUG:
        print(f"[DEBUG] {msg}")


# ==================== Resource paths ====================

def get_resource_path(relative_path):
    """Return the absolute path to a bundled resource."""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


# application_path is the folder next to the exe, used for
# writable files (data/, logs, etc.). Never use this for
# bundled resources.
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
    os.chdir(application_path)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))


# ==================== Optional imports ====================

try:
    import jdatetime
    JDATETIME_AVAILABLE = True
except ImportError:
    JDATETIME_AVAILABLE = False

try:
    from components.form1_component import Form1Component
    from components.form2SH_component import Form2SHComponent
    from components.form2_component import Form2Component
    from components.form3_component import Form3Component
    COMPONENTS_AVAILABLE = True
except ImportError as e:
    COMPONENTS_AVAILABLE = False
    debug_print(f"Component import failed: {e}")

try:
    from components.pdf_exporter import PDFExporter
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


# ==================== Temporary storage ====================

class TemporaryStorage:
    """Saves the day's shift data next to the exe."""

    def __init__(self):
        self.storage_file = "temporary_data.json"
        self.data_dir = "data"
        data_path = os.path.join(application_path, self.data_dir)
        os.makedirs(data_path, exist_ok=True)

    def get_storage_path(self):
        return os.path.join(
            application_path, self.data_dir, self.storage_file
        )

    def save_data(self, shift1_data, shift2_data=None,
                  form2_data=None, current_date=None):
        try:
            data = {
                "current_date": current_date,
                "shift1_data": shift1_data,
                "shift2_data": shift2_data,
                "form2_data": form2_data,
                "last_saved": datetime.now().isoformat(),
            }
            with open(self.get_storage_path(), 'w',
                      encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

    def load_data(self):
        try:
            path = self.get_storage_path()
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
        except Exception:
            return None

    def clear_data(self):
        try:
            path = self.get_storage_path()
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass


# ==================== Fonts ====================

import tkinter.font as tkfont


def load_persian_font(root, font_name="Vazir", size=11):
    """Load the Persian font from the bundled fonts folder."""
    try:
        font_path = get_resource_path(f"fonts/{font_name}.ttf")
        if os.path.exists(font_path):
            tkfont.Font(family=font_name, size=size)
            return font_name
        return "Tahoma"
    except Exception:
        return "Tahoma"


# ==================== Splash ====================

def show_splash(on_finish):
    splash = tk.Tk()
    splash.overrideredirect(True)
    splash.configure(bg="#f9f9f9")

    w, h = 460, 360
    x = (splash.winfo_screenwidth() // 2) - (w // 2)
    y = (splash.winfo_screenheight() // 2) - (h // 2)
    splash.geometry(f"{w}x{h}+{x}+{y}")

    LOGO_PATH = get_resource_path("asset/logo.png")
    try:
        img = Image.open(LOGO_PATH)
        img = img.resize((200, 200), Image.Resampling.LANCZOS)
        logo_tk = ImageTk.PhotoImage(img)
        logo_label = tk.Label(splash, image=logo_tk)
        logo_label.image = logo_tk
        logo_label.pack(pady=(30, 15))
    except Exception:
        title = tk.Label(
            splash, text="سیستم مدیریت پمپ بنزین",
            font=("Tahoma", 20, "bold"),
            bg="#f5f7fa", fg="#1f3a5f",
        )
        title.pack(pady=30)

    style = ttk.Style()
    style.theme_use("clam")
    style.configure(
        "blue.Horizontal.TProgressbar",
        foreground="#3498db", background="#3498db",
        troughcolor="#e0e0e0", thickness=10,
    )
    progress = ttk.Progressbar(
        splash, orient="horizontal", length=350,
        mode="determinate", style="blue.Horizontal.TProgressbar",
    )
    progress.pack(pady=25)

    status = tk.Label(
        splash, text="در حال راه‌اندازی...",
        bg="#f5f7fa", fg="#95a5a6", font=("Tahoma", 10),
    )
    status.pack(pady=(0, 20))

    def update_progress():
        cur = progress['value']
        if cur < 100:
            progress['value'] = min(cur + 2, 100)
            if cur < 30:
                status.config(text="در حال بارگذاری منابع اولیه...")
            elif cur < 70:
                status.config(text="اتصال به پایگاه داده...")
            else:
                status.config(text="تکمیل راه‌اندازی...")
            splash.after(30, update_progress)
        else:
            splash.destroy()
            on_finish()

    splash.after(100, update_progress)
    splash.mainloop()


# ==================== Main app ====================

class GasStationManagementSystem:
    def __init__(self, root):
        self.root = root
        self.temporary_storage = TemporaryStorage()

        saved_data = self.temporary_storage.load_data()
        if JDATETIME_AVAILABLE:
            if saved_data and 'current_date' in saved_data:
                self.current_date = saved_data['current_date']
            else:
                self.current_date = jdatetime.date.today().strftime(
                    "%Y%m%d"
                )
        else:
            if saved_data and 'current_date' in saved_data:
                self.current_date = saved_data['current_date']
            else:
                self.current_date = datetime.now().strftime("%Y%m%d")

        self.setup_ui()
        self.load_saved_data()

    def setup_ui(self):
        try:
            self.root.title("سیستم مدیریت پمپ بنزین v1.0 - پرتابل")
            self.root.geometry("1350x768")
            self.root.grid_rowconfigure(0, weight=1)
            self.root.grid_columnconfigure(0, weight=1)

            if COMPONENTS_AVAILABLE:
                self.notebook = ttk.Notebook(self.root)
                self.notebook.grid(
                    row=0, column=0, padx=10, pady=5, sticky='nsew'
                )

                self.form1 = Form1Component(
                    self.notebook, shift_id=f"{self.current_date}01"
                )
                self.form2sh = Form2SHComponent(
                    self.notebook, self.form1,
                    shift_id=f"{self.current_date}02"
                )
                self.form2 = Form2Component(
                    self.notebook, self.form1, self.form2sh
                )
                self.form3 = Form3Component(
                    self.notebook, self.form1, self.form2, self.form2sh
                )

                self.notebook.add(self.form1.frame, text='شیفت اول')
                self.notebook.add(self.form2sh.frame, text='شیفت دوم')
                self.notebook.add(self.form2.frame, text='مالی')
                self.notebook.add(self.form3.frame, text='شمارنده‌ها')

                btn_frame = ttk.Frame(self.root)
                btn_frame.grid(row=1, column=0, pady=5, sticky='ew')

                tk.Button(btn_frame, text="محاسبه همه",
                          command=self.calculate_all,
                          bg='green', fg='white').pack(side='left', padx=5)
                tk.Button(btn_frame, text="ذخیره موقت",
                          command=self.save_temporary_data,
                          bg='blue', fg='white').pack(side='left', padx=5)
                tk.Button(btn_frame, text="چاپ PDF",
                          command=self.print_forms_pdf,
                          bg='orange', fg='white').pack(side='left', padx=5)
                tk.Button(btn_frame, text="پایان روز (پاک کردن)",
                          command=self.finalize_day,
                          bg='red', fg='white').pack(side='left', padx=5)

                self.result_text = tk.Text(self.root, height=5)
                self.result_text.grid(row=2, column=0, sticky='ew', padx=10)

                info = tk.Label(
                    self.root,
                    text="نسخه پرتابل - بدون نیاز به فعالسازی",
                    font=('Tahoma', 9), fg='green',
                )
                info.grid(row=3, column=0, pady=5, sticky='s')

                self.pdf_exporter = PDFExporter(
                    self.form1, self.form2sh, self.form2,
                    self.form3, self.result_text
                )
            else:
                tk.Label(
                    self.root,
                    text="سیستم مدیریت پمپ بنزین (نسخه پرتابل)",
                    font=('Tahoma', 24, 'bold')
                ).pack(expand=True)

        except Exception as e:
            messagebox.showerror("خطا", f"خطا در راه‌اندازی: {e}")
            import traceback
            traceback.print_exc()

    def calculate_all(self):
        try:
            f1_data = self.form1.get_data()
            for nozzle_num, nozzle_data in f1_data['nozzles'].items():
                if nozzle_num in self.form2sh.entries:
                    end_value_f1 = nozzle_data['end']
                    start_entry_f2sh = self.form2sh.entries[
                        nozzle_num
                    ]['آغاز']
                    start_entry_f2sh.config(state='normal')
                    start_entry_f2sh.delete(0, tk.END)
                    start_entry_f2sh.insert(0, end_value_f1)
                    start_entry_f2sh.config(state='readonly')
            self.root.update()
            self.form1.calculate()
            self.form2sh.calculate()
            self.form2.calculate()
            self.form3.calculate()
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(1.0, "محاسبات تمام فرم‌ها انجام شد.")
        except Exception as e:
            messagebox.showerror("خطا", str(e))

    def save_temporary_data(self):
        try:
            s1 = self.form1.get_data()
            s2 = self.form2sh.get_data()
            form2_data = self.get_form2_data()
            if self.temporary_storage.save_data(
                s1, s2, form2_data, self.current_date
            ):
                self.result_text.insert(tk.END, "\\nذخیره موقت انجام شد.")
            else:
                messagebox.showerror("خطا", "ذخیره نشد.")
        except Exception as e:
            messagebox.showerror("خطا", str(e))

    def get_form2_data(self):
        try:
            if not hasattr(self, 'form2'):
                return None
            data = {}
            for key, entry in self.form2.entries.items():
                try:
                    data[key] = entry.get()
                except Exception:
                    data[key] = ""
            for key, entry in self.form2.detail_entries.items():
                try:
                    data[f"detail_{key}"] = entry.get()
                except Exception:
                    data[f"detail_{key}"] = ""
            return data
        except Exception:
            return None

    def load_saved_data(self):
        data = self.temporary_storage.load_data()
        if not data:
            return
        try:
            if 'shift1_data' in data and data['shift1_data']:
                self._populate_form(self.form1, data['shift1_data'])
            if 'shift2_data' in data and data['shift2_data']:
                self._populate_form(self.form2sh, data['shift2_data'])
            if 'form2_data' in data and data['form2_data'] \\
                    and hasattr(self, 'form2'):
                self._populate_form2(data['form2_data'])
                self.result_text.insert(
                    tk.END, "داده‌های قبلی بازیابی شدند.\\n"
                )
        except Exception as e:
            debug_print(f"Load error: {e}")

    def _populate_form2(self, form2_data):
        try:
            if not hasattr(self, 'form2'):
                return
            for key, entry in self.form2.entries.items():
                if key in form2_data:
                    try:
                        entry.config(state='normal')
                        entry.delete(0, tk.END)
                        entry.insert(0, form2_data[key])
                        if key not in [
                            'start_inv', 'end_inv', 'mech_diff',
                            'received', 'bank_exit', 'safe_box'
                        ]:
                            entry.config(state='readonly')
                    except Exception:
                        pass
            for key, entry in self.form2.detail_entries.items():
                data_key = f"detail_{key}"
                if data_key in form2_data:
                    try:
                        current_state = entry.cget('state')
                        entry.config(state='normal')
                        entry.delete(0, tk.END)
                        entry.insert(0, form2_data[data_key])
                        entry.config(state=current_state)
                    except Exception:
                        pass
        except Exception as e:
            debug_print(f"Populate form2 error: {e}")

    def _populate_form(self, form, data):
        try:
            if 'nozzles' in data:
                for n_str, vals in data['nozzles'].items():
                    n = int(n_str)
                    if n in form.entries:
                        if 'end' in vals:
                            form.entries[n]['پایان'].delete(0, tk.END)
                            form.entries[n]['پایان'].insert(
                                0, vals['end']
                            )
                        if 'start' in vals:
                            form.entries[n]['آغاز'].delete(0, tk.END)
                            form.entries[n]['آغاز'].insert(
                                0, vals['start']
                            )
            if 'financial' in data:
                fin = data['financial']
                if 'total_elec' in fin:
                    form.total_elec_entry.delete(0, tk.END)
                    form.total_elec_entry.insert(0, fin['total_elec'])
                if 'total_subsidy' in fin:
                    form.total_subsidy_entry.delete(0, tk.END)
                    form.total_subsidy_entry.insert(
                        0, fin['total_subsidy']
                    )
                if 'total_semi' in fin:
                    form.total_semi_entry.delete(0, tk.END)
                    form.total_semi_entry.insert(0, fin['total_semi'])
                if 'total_azad_1' in fin:
                    form.total_azad_entry_1.delete(0, tk.END)
                    form.total_azad_entry_1.insert(
                        0, fin['total_azad_1']
                    )
                if 'total_azad_2' in fin:
                    form.total_azad_entry_2.delete(0, tk.END)
                    form.total_azad_entry_2.insert(
                        0, fin['total_azad_2']
                    )
            if 'operator1' in data and hasattr(form, 'operator_entry_1'):
                form.operator_entry_1.delete(0, tk.END)
                form.operator_entry_1.insert(0, data['operator1'])
            if 'operator2' in data and hasattr(form, 'operator_entry_2'):
                form.operator_entry_2.delete(0, tk.END)
                form.operator_entry_2.insert(0, data['operator2'])
            if 'card_readers' in data:
                for i, val in enumerate(data['card_readers']):
                    if i < len(form.card_reader_entries):
                        form.card_reader_entries[i].delete(0, tk.END)
                        form.card_reader_entries[i].insert(0, val)
        except Exception as e:
            debug_print(f"Populate form error: {e}")

    def finalize_day(self):
        if messagebox.askyesno(
            "تایید", "آیا مطمئن هستید؟ داده‌های امروز پاک می‌شوند."
        ):
            self.temporary_storage.clear_data()
            self.root.destroy()
            python = sys.executable
            os.execl(python, python, *sys.argv)

    def print_forms_pdf(self):
        self.calculate_all()
        self.pdf_exporter.print_forms_pdf()


def main():
    try:
        root = tk.Tk()
        icon_path = get_resource_path("gas_station.ico")
        if os.path.exists(icon_path):
            root.iconbitmap(icon_path)

        load_persian_font(root, "Vazir")
        GasStationManagementSystem(root)
        root.mainloop()
    except Exception as e:
        debug_print(f"Fatal: {e}")
        try:
            messagebox.showerror("خطا", f"خطا در اجرای برنامه: {e}")
        except Exception:
            pass


if __name__ == "__main__":
    show_splash(main)
'''

    with open("main_portable.py", "w", encoding="utf-8") as f:
        f.write(portable_main_content)

    print("  main_portable.py created")


# =============================================
# Build
# =============================================

def build_executable():
    """Build the portable executable."""
    print("\nBuilding portable executable...")

    cmd = [
        "pyinstaller",
        "--onedir",
        "--windowed",
        f"--name={APP_NAME}",
        "--noconfirm",
        "--clean",
    ]

    # Icon: added once, and also as a bundled file.
    if os.path.exists(ICON_FILE):
        cmd.append(f"--icon={ICON_FILE}")
        cmd.append(f"--add-data={ICON_FILE};.")

    # Bundle resource folders into _MEIPASS.
    for folder in BUNDLED_FOLDERS:
        if os.path.exists(folder):
            cmd.append(f"--add-data={folder};{folder}")

    # Hidden imports.
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
    Assemble the portable package delivered to the customer.

    Layout:
        GasStationManager_Portable_YYYYMMDD/
        |-- run.bat
        |-- readme.txt
        |-- GasStationManager_Portable/
            |-- Gas Station Management (Portable).exe
            |-- _internal/
            |-- fonts/           (editable by customer)
            |-- asset/           (editable by customer)
            |-- gas_station.ico
            |-- data/            (created on first run)
    """
    print("\nCreating portable client package...")

    pkg_folder = (
        f"{APP_NAME}_Portable_{datetime.now().strftime('%Y%m%d')}"
    )
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

    # Editable resources next to the exe.
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

    # Data folder for temporary storage.
    data_dir = os.path.join(dst_exe_dir, "data")
    os.makedirs(data_dir, exist_ok=True)

    # run.bat
    bat_content = (
        "@echo off\r\n"
        "title Gas Station Management System (Portable)\r\n"
        "echo =============================================\r\n"
        "echo  Portable edition - no activation required\r\n"
        "echo =============================================\r\n"
        "echo.\r\n"
        "echo Starting...\r\n"
        f'"{APP_NAME}\\{EXE_NAME}"\r\n'
        "pause\r\n"
    )
    with open(
        os.path.join(pkg_folder, "run.bat"), "w", encoding="utf-8"
    ) as f:
        f.write(bat_content)

    # readme.txt
    readme = f"""Gas Station Management System - Portable Edition
================================================================

This edition requires no activation and no license file.
All data is stored inside the app folder.

How to use:
  1. Copy this folder anywhere you like.
  2. Double-click "run.bat".
  3. The app opens directly - no setup needed.

Folders:
  data/    Shift data is saved here.
  fonts/   Editable. Replace if you prefer a different font.
  asset/   Editable. Replace logo.png with your own logo.

Build date: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
    with open(
        os.path.join(pkg_folder, "readme.txt"), "w", encoding="utf-8"
    ) as f:
        f.write(readme)

    print(f"Portable package ready: {pkg_folder}")


# =============================================
# Main
# =============================================

def main():
    print("=" * 70)
    print(" Build Portable Executable - No License ".center(70))
    print("=" * 70)
    print("\nPortable edition: no hardware lock, no activation.")
    print("All data is saved inside the app folder.\n")

    check_dependencies()
    clean_previous_builds()
    create_portable_main()
    build_executable()
    create_client_package()

    print("\nOperation completed successfully.")
    print(f"  Executable: dist/{APP_NAME}/{EXE_NAME}")
    print(f"  Package:    {APP_NAME}_Portable_YYYYMMDD/")
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