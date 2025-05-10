import os
import subprocess
import sys
import shutil

def build_application():
    """Build the application into an executable"""
    print("Building Medical Rep Transaction Software...")
    
    # Ensure PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Create spec file if it doesn't exist
    spec_file = "medrepapp.spec"
    if not os.path.exists(spec_file):
        print("Creating spec file...")
        subprocess.check_call([
            "pyinstaller",
            "--name=MedRepApp",
            "--windowed",
            "--onefile",
            "--add-data=src;src",
            "main.py"
        ])
    
    # Build the application
    print("Building executable...")
    subprocess.check_call(["pyinstaller", spec_file])
    
    # Create data directory
    dist_dir = os.path.join("dist", "MedRepApp")
    if not os.path.exists(dist_dir):
        os.makedirs(dist_dir)
    
    data_dir = os.path.join(dist_dir, "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    backups_dir = os.path.join(data_dir, "backups")
    if not os.path.exists(backups_dir):
        os.makedirs(backups_dir)
    
    print("Build completed successfully!")
    print(f"Executable is located at: {os.path.abspath(os.path.join('dist', 'MedRepApp.exe'))}")

if __name__ == "__main__":
    build_application()