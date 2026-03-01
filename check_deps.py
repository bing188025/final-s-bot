import subprocess, sys

pkgs = ["lxml", "cssselect"]
for p in pkgs:
    try:
        __import__(p)
        print(f"{p}: OK")
    except ImportError:
        print(f"{p}: MISSING - installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", p], check=True)
        print(f"{p}: installed")
