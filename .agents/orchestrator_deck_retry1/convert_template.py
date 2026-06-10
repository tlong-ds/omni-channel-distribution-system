import os
import subprocess
import time

def run_applescript(script_content):
    process = subprocess.Popen(['osascript', '-e', script_content], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    return process.returncode, stdout.decode('utf-8'), stderr.decode('utf-8')

def convert_pptx_to_pdf(pptx_path, pdf_path):
    applescript = f'''
    tell application "Keynote"
        activate
    end tell
    
    tell application "System Events"
        tell process "Keynote"
            -- Check for crash recovery dialog and dismiss it
            delay 2
            try
                if exists (window 1) then
                    set wName to name of window 1
                    if wName contains "reopen" or wName contains "unexpectedly" then
                        log "Dismissing recovery dialog: " & wName
                        keystroke return
                        delay 2
                    end if
                end if
            on error errText
                log "Recovery check error: " & errText
            end try
        end tell
    end tell

    tell application "Keynote"
        try
            open POSIX file "{pptx_path}"
        on error errText number errNum
            log "Open error: " & errText & " (" & errNum & ")"
        end try
        delay 3
    end tell

    tell application "System Events"
        tell process "Keynote"
            set frontmost to true
            delay 1
            click menu item "PDF…" of menu 1 of menu item "Export To" of menu 1 of menu bar item "File" of menu bar 1
            delay 2
            click button "Save…" of sheet 1 of window 1
            delay 2
            keystroke "g" using {{command down, shift down}}
            delay 1.5
            keystroke "{pdf_path}"
            delay 1.5
            keystroke return
            delay 1.5
            keystroke return
            delay 3
        end tell
    end tell
    
    tell application "Keynote"
        close front document saving no
    end tell
    '''
    print("Running AppleScript to convert template PPTX...")
    code, out, err = run_applescript(applescript)
    print(f"Exit code: {code}")
    print(f"Stdout: {out}")
    print(f"Stderr: {err}")
    return os.path.exists(pdf_path)

if __name__ == "__main__":
    pptx = "/Users/bunnypro/Projects/LOGage2026/Red Modern Logistic Presentation.pptx"
    pdf = "/Users/bunnypro/Projects/LOGage2026/template.pdf"
    
    if os.path.exists(pdf):
        os.remove(pdf)
        
    success = convert_pptx_to_pdf(pptx, pdf)
    if success:
        print("PDF conversion completed successfully.")
        # Render image
        subprocess.run([
            "/opt/homebrew/bin/pdftoppm",
            "-jpeg",
            "-r", "150",
            pdf,
            "/Users/bunnypro/Projects/LOGage2026/template_slide"
        ])
    else:
        print("Failed to convert template PPTX.")
