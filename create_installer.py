import os
import sys
import subprocess
import shutil
import tempfile
import argparse

def create_installer(version, output_dir):
    """Create a Windows installer for the application"""
    print(f"Creating installer for Medical Rep Transaction Software v{version}")
    
    # Ensure PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Create build directory
    build_dir = os.path.join(os.path.dirname(__file__), "build")
    dist_dir = os.path.join(os.path.dirname(__file__), "dist")
    
    # Clean previous builds
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)
    
    os.makedirs(build_dir, exist_ok=True)
    os.makedirs(dist_dir, exist_ok=True)
    
    # Build executable
    print("Building executable...")
    subprocess.check_call([
        "pyinstaller",
        "--name=MedRepApp",
        "--windowed",
        "--icon=resources/icon.ico",
        "--add-data=resources;resources",
        "--add-data=src;src",
        "launcher.py"
    ])
    
    # Create Inno Setup script
    print("Creating Inno Setup script...")
    inno_script = f"""
    #define MyAppName "Medical Rep Transaction Software"
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
    LicenseFile=LICENSE.txt
    OutputDir={output_dir}
    OutputBaseFilename=MedRepApp_Setup_v{version}
    Compression=lzma
    SolidCompression=yes
    WizardStyle=modern

    [Languages]
    Name: "english"; MessagesFile: "compiler:Default.isl"

    [Tasks]
    Name: "desktopicon"; Description: "{{cm:CreateDesktopIcon}}"; GroupDescription: "{{cm:AdditionalIcons}}";

    [Files]
    Source: "dist\\MedRepApp\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs
    Source: "LICENSE.txt"; DestDir: "{{app}}"; Flags: ignoreversion
    Source: "README.md"; DestDir: "{{app}}"; Flags: ignoreversion

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
    
    # Create a license file if it doesn't exist
    license_path = os.path.join(os.path.dirname(__file__), "LICENSE.txt")
    if not os.path.exists(license_path):
        with open(license_path, 'w') as f:
            f.write(f"""
            Medical Rep Transaction Software v{version}
            Copyright (c) 2025 Your Company
            
            This is a placeholder license file. Replace with your actual license terms.
            """)
    
    # Create a readme file if it doesn't exist
    readme_path = os.path.join(os.path.dirname(__file__), "README.md")
    if not os.path.exists(readme_path):
        with open(readme_path, 'w') as f:
            f.write(f"""
            # Medical Rep Transaction Software
            
            Version {version}
            
            ## Installation
            
            Run the installer and follow the instructions.
            
            ## Usage
            
            Launch the application from the Start Menu or desktop shortcut.
            
            ## Support
            
            Contact support@yourcompany.com for assistance.
            """)
    
    # Create temporary Inno Setup script file
    with tempfile.NamedTemporaryFile(suffix='.iss', delete=False) as script_file:
        script_file.write(inno_script.encode('utf-8'))
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
            return False
        
        # Run Inno Setup compiler
        print("Building installer...")
        subprocess.check_call([inno_compiler, script_path])
        
        print(f"Installer created successfully in {output_dir}")
        return True
        
    finally:
        # Clean up temporary script file
        os.unlink(script_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create installer for Medical Rep Transaction Software")
    parser.add_argument('--version', default='1.0.0', help='Version number (default: 1.0.0)')
    parser.add_argument('--output', default='installers', help='Output directory (default: installers)')
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output, exist_ok=True)
    
    # Create installer
    create_installer(args.version, args.output)