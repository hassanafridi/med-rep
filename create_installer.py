import os
import sys
import subprocess
import shutil
import tempfile
import argparse
import time

def safe_rmtree(path, max_retries=3):
    """Safely remove directory tree with retries for locked files"""
    for attempt in range(max_retries):
        try:
            if os.path.exists(path):
                shutil.rmtree(path)
            return True
        except (PermissionError, OSError) as e:
            if attempt < max_retries - 1:
                print(f"Attempt {attempt + 1} failed to remove {path}: {e}. Retrying...")
                time.sleep(2)  # Wait 2 seconds before retry
            else:
                print(f"Failed to remove {path} after {max_retries} attempts: {e}")
                print("Please close any applications that might be using files in this directory and try again.")
                return False
    return False

def create_installer(version, output_dir):
    """Create a Windows installer for the application"""
    print(f"Creating installer for Medical Rep Transaction Software v{version}")
    
    # Get absolute paths for project directory
    project_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check if build.py exists and use it instead of duplicating build logic
    build_py_path = os.path.join(project_dir, "build.py")
    if os.path.exists(build_py_path):
        print("Using existing build.py to create executable...")
        try:
            subprocess.check_call([sys.executable, "build.py"])
        except subprocess.CalledProcessError as e:
            print(f"Build failed: {e}")
            return False
    else:
        # Fallback to original build logic
        # Ensure PyInstaller is installed
        try:
            import PyInstaller
        except ImportError:
            print("Installing PyInstaller...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        
        # Create build directory
        build_dir = os.path.join(os.path.dirname(__file__), "build")
        dist_dir = os.path.join(os.path.dirname(__file__), "dist")
        
        # Clean previous builds with safe removal
        print("Cleaning previous builds...")
        if not safe_rmtree(build_dir) or not safe_rmtree(dist_dir):
            print("Warning: Could not clean all build directories. Continuing anyway...")
        
        os.makedirs(build_dir, exist_ok=True)
        os.makedirs(dist_dir, exist_ok=True)
        
        # Build executable
        print("Building executable...")
        try:
            subprocess.check_call([
                "pyinstaller",
                "--name=MedRepApp",
                "--windowed",
                "--onefile",
                "--add-data=src;src",
                "--add-data=templates;templates" if os.path.exists("templates") else "--add-data=src;src",
                "--hidden-import=reportlab",
                "--hidden-import=PyQt5",
                "--hidden-import=pymongo",
                "main.py"
            ])
        except subprocess.CalledProcessError as e:
            print(f"PyInstaller build failed: {e}")
            return False
    
    # Verify that the executable was created
    exe_path = os.path.join(project_dir, "dist", "MedRepApp", "MedRepApp.exe")
    if not os.path.exists(exe_path):
        # Try alternative path
        exe_path = os.path.join(project_dir, "dist", "MedRepApp.exe")
        if not os.path.exists(exe_path):
            print("Error: Executable not found after build. Please check the build process.")
            return False
    
    # Ensure license file exists and get absolute path
    license_path = os.path.join(project_dir, "LICENSE.txt")
    if not os.path.exists(license_path):
        # Check for LICENSE file without extension
        alt_license_path = os.path.join(project_dir, "LICENSE")
        if os.path.exists(alt_license_path):
            # Copy LICENSE to LICENSE.txt
            shutil.copy2(alt_license_path, license_path)
        else:
            # Create placeholder license
            with open(license_path, 'w') as f:
                f.write(f"""Medical Rep Transaction Software v{version}
Copyright (c) 2025 Your Company

This is a placeholder license file. Replace with your actual license terms.
""")
    
    # Ensure readme file exists
    readme_path = os.path.join(project_dir, "README.md")
    if not os.path.exists(readme_path):
        with open(readme_path, 'w') as f:
            f.write(f"""# Medical Rep Transaction Software

Version {version}

## Installation

Run the installer and follow the instructions.

## Usage

Launch the application from the Start Menu or desktop shortcut.

## Support

Contact support@yourcompany.com for assistance.
""")
    
    # Create absolute output directory
    abs_output_dir = os.path.abspath(output_dir)
    os.makedirs(abs_output_dir, exist_ok=True)
    
    # Create Inno Setup script with absolute paths
    print("Creating Inno Setup script...")
    dist_path = os.path.join(project_dir, "dist", "MedRepApp")
    if not os.path.exists(dist_path):
        dist_path = os.path.join(project_dir, "dist")
    
    inno_script = f"""#define MyAppName "Medical Rep Transaction Software"
#define MyAppVersion "{version}"
#define MyAppPublisher "Your Company"
#define MyAppURL "https://yourcompany.com"
#define MyAppExeName "MedRepApp.exe"

[Setup]
AppId={{{{8A17BE89-23A4-4FF3-8B43-BF0E15A4E8CA}}}}
AppName={{#MyAppName}}
AppVersion={{#MyAppVersion}}
AppPublisher={{#MyAppPublisher}}
AppPublisherURL={{#MyAppURL}}
AppSupportURL={{#MyAppURL}}
AppUpdatesURL={{#MyAppURL}}
DefaultDirName={{autopf}}\\{{#MyAppName}}
DefaultGroupName={{#MyAppName}}
DisableProgramGroupPage=yes
LicenseFile={license_path}
OutputDir={abs_output_dir}
OutputBaseFilename=MedRepApp_Setup_v{version}
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{{cm:CreateDesktopIcon}}"; GroupDescription: "{{cm:AdditionalIcons}}";

[Files]
Source: "{dist_path}\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{license_path}"; DestDir: "{{app}}"; Flags: ignoreversion
Source: "{readme_path}"; DestDir: "{{app}}"; Flags: ignoreversion

[Icons]
Name: "{{group}}\\{{#MyAppName}}"; Filename: "{{app}}\\{{#MyAppExeName}}"
Name: "{{group}}\\Uninstall {{#MyAppName}}"; Filename: "{{uninstallexe}}"
Name: "{{commondesktop}}\\{{#MyAppName}}"; Filename: "{{app}}\\{{#MyAppExeName}}"; Tasks: desktopicon

[Run]
Filename: "{{app}}\\{{#MyAppExeName}}"; Description: "{{cm:LaunchProgram,{{#StringChange(MyAppName, '&', '&&')}}}}"; Flags: nowait postinstall skipifsilent

[Dirs]
Name: "{{app}}\\data"; Permissions: users-modify
Name: "{{app}}\\data\\backups"; Permissions: users-modify
"""
    
    # Create temporary Inno Setup script file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.iss', delete=False, encoding='utf-8') as script_file:
        script_file.write(inno_script)
        script_path = script_file.name
    
    try:
        # Find Inno Setup compiler
        inno_compiler = "C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe"
        if not os.path.exists(inno_compiler):
            # Look for Inno Setup 5
            inno_compiler = "C:\\Program Files (x86)\\Inno Setup 5\\ISCC.exe"
            
        if not os.path.exists(inno_compiler):
            print("Inno Setup not found. Please install Inno Setup to create the installer.")
            print("You can download it from: https://jrsoftware.org/isdl.php")
            print(f"Alternatively, you can distribute the application from: {dist_path}")
            return False
        
        # Debug: Print the script content and file paths
        print(f"License file: {license_path} (exists: {os.path.exists(license_path)})")
        print(f"Readme file: {readme_path} (exists: {os.path.exists(readme_path)})")
        print(f"Dist directory: {dist_path} (exists: {os.path.exists(dist_path)})")
        print(f"Output directory: {abs_output_dir}")
        
        # Run Inno Setup compiler
        print("Building installer...")
        subprocess.check_call([inno_compiler, script_path])
        
        print(f"Installer created successfully in {abs_output_dir}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Installer creation failed: {e}")
        return False
    finally:
        # Clean up temporary script file
        try:
            os.unlink(script_path)
        except OSError:
            pass  # Ignore cleanup errors

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create installer for Medical Rep Transaction Software")
    parser.add_argument('--version', default='1.0.0', help='Version number (default: 1.0.0)')
    parser.add_argument('--output', default='installers', help='Output directory (default: installers)')
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output, exist_ok=True)
    
    # Create installer
    success = create_installer(args.version, args.output)
    if not success:
        sys.exit(1)