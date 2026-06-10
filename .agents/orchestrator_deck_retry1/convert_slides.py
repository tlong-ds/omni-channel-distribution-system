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
        try
            open POSIX file "{pptx_path}"
        on error errText number errNum
            log "Open error: " & errText & " (" & errNum & ")"
        end try
        delay 3
    end tell

    tell application "System Events"
        tell process "Keynote"
            try
                if exists (sheet 1 of window 1) then
                    log "Dismissing warning sheet"
                    keystroke return
                    delay 1
                end if
            on error errText
                log "Sheet error: " & errText
            end try
        end tell
    end tell

    tell application "Keynote"
        try
            set doc to front document
            export doc to POSIX file "{pdf_path}" as PDF
            close doc saving no
            log "Export and close successful"
        on error errText number errNum
            log "Export error: " & errText & " (" & errNum & ")"
        end try
    end tell
    '''
    print("Running AppleScript to convert PPTX to PDF using Keynote...")
    code, out, err = run_applescript(applescript)
    print(f"Exit code: {code}")
    print(f"Stdout: {out}")
    print(f"Stderr: {err}")
    return code == 0 and os.path.exists(pdf_path)

def render_pdf_to_images(pdf_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    prefix = os.path.join(output_dir, "slide")
    
    cmd = [
        "/opt/homebrew/bin/pdftoppm",
        "-jpeg",
        "-r", "150",
        pdf_path,
        prefix
    ]
    print(f"Running pdftoppm: {' '.join(cmd)}")
    res = subprocess.run(cmd, capture_output=True, text=True)
    print(f"pdftoppm exit code: {res.returncode}")
    if res.returncode != 0:
        print(f"pdftoppm stderr: {res.stderr}")
        return False
        
    # Rename slide-1.jpg to slide-01.jpg etc.
    for filename in os.listdir(output_dir):
        if filename.startswith("slide-") and filename.endswith(".jpg"):
            # Extract number
            parts = filename.split("-")
            if len(parts) == 2:
                num_part = parts[1].replace(".jpg", "")
                if len(num_part) == 1:
                    new_filename = f"slide-0{num_part}.jpg"
                    os.rename(os.path.join(output_dir, filename), os.path.join(output_dir, new_filename))
                    print(f"Renamed {filename} -> {new_filename}")
                elif len(num_part) == 2:
                    # slide-10.jpg etc.
                    pass
    return True

if __name__ == "__main__":
    pptx = "/Users/bunnypro/teamwork_projects/logage_slides/output.pptx"
    pdf = "/Users/bunnypro/teamwork_projects/logage_slides/output.pdf"
    images_dir = "/Users/bunnypro/teamwork_projects/logage_slides/images"
    
    # Clean up old PDF if exists
    if os.path.exists(pdf):
        os.remove(pdf)
        
    success = convert_pptx_to_pdf(pptx, pdf)
    if success:
        print("PDF conversion completed successfully.")
        img_success = render_pdf_to_images(pdf, images_dir)
        if img_success:
            print("Images rendered successfully.")
        else:
            print("Failed to render images from PDF.")
    else:
        print("Failed to convert PPTX to PDF.")
