import subprocess
import sys
import os
import datetime

def run_command(command, description, shell=False):
    print(f"--- {description} ---")
    try:
        # On Windows, shell=True is often needed for commands like 'git' if they are bat files or similar,
        # but for executables it's not strictly necessary. 
        # However, if we don't know where git is, relying on PATH (shell=True) is standard.
        # But we know 'git' failed in powershell. 
        # We will try to run it.
        result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
        print(result.stdout)
        print("Success.")
    except subprocess.CalledProcessError as e:
        print(f"Error running {description}:")
        print(e.stderr)
        print(e.stdout)
        
        # Allow git commit to fail (e.g. nothing to commit)
        # Check if the command string contains "commit"
        is_commit = False
        if isinstance(command, str):
            if "commit" in command:
                is_commit = True
        elif isinstance(command, list):
             if "commit" in command:
                 is_commit = True
                 
        if is_commit:
            print("Ignoring commit error (likely nothing to commit).")
            return

        # For other commands, exit if it's not a git command (or even if it is, maybe we should stop?)
        # But the original logic was trying to be lenient with git.
        # Let's just say: if it's a git command, don't exit.
        is_git = False
        if isinstance(command, str):
            if "git" in command.lower():
                is_git = True
        elif isinstance(command, list):
            if "git" in command[0].lower() or (len(command)>1 and "git" in command[1].lower()):
                is_git = True
        
        if not is_git:
             sys.exit(1)

def main():
    python_exe = sys.executable

    # 1. Run Scraper
    print("Running Scraper...")
    run_command([python_exe, "scraper.py"], "Scraper")

    # 2. Update Schedule.txt
    print("Updating schedule.txt...")
    try:
        # Force UTF-8 encoding for capture
        result = subprocess.run([python_exe, "display_schedule.py"], check=True, text=True, capture_output=True, encoding='utf-8')
        with open("schedule.txt", "w", encoding="utf-8") as f:
            f.write(result.stdout)
        print("schedule.txt updated.")
    except subprocess.CalledProcessError as e:
        print("Error updating schedule.txt")
        print(e.stderr)

    # 3. Generate ICS
    print("Generating ICS file...")
    run_command([python_exe, "create_ics.py"], "ICS Generation")

    # 4. Git Push
    print("Pushing to GitHub...")
    
    # Try to find git
    git_cmd = "git"
    
    # Check common paths if 'git' is not in PATH
    possible_paths = [
        "git",
        r"C:\Program Files\Git\cmd\git.exe",
        r"C:\Program Files\Git\bin\git.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Git\cmd\git.exe")
    ]

    found_git = False
    for path in possible_paths:
        try:
            subprocess.run([path, "--version"], check=True, capture_output=True, shell=True)
            git_cmd = f'"{path}"' # Quote path in case of spaces
            found_git = True
            print(f"Found git at: {path}")
            break
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue
            
    if not found_git:
        print("WARNING: 'git' command not found. Cannot push to GitHub.")
        print("Please install Git for Windows: https://git-scm.com/download/win")
        return

    commands = [
        f'{git_cmd} add events.csv schedule.txt public/events.ics',
        f'{git_cmd} commit -m "Auto-update events: {datetime.datetime.now()}"',
        f'{git_cmd} push'
    ]
    
    for cmd in commands:
        run_command(cmd, f"Git Operation: {cmd}")

if __name__ == "__main__":
    main()
