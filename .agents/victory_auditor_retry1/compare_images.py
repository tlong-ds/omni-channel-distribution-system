import os
import datetime

def list_files_with_details(dir_path):
    print(f"\n--- Directory: {dir_path} ---")
    if not os.path.exists(dir_path):
        print("Does not exist.")
        return
    for f in sorted(os.listdir(dir_path)):
        p = os.path.join(dir_path, f)
        if os.path.isfile(p):
            stat = os.stat(p)
            mtime = datetime.datetime.fromtimestamp(stat.st_mtime).isoformat()
            print(f"File: {f} | Size: {stat.st_size} bytes | Modified: {mtime}")

if __name__ == "__main__":
    list_files_with_details("/Users/bunnypro/teamwork_projects/logage_slides/images")
    list_files_with_details("/Users/bunnypro/teamwork_projects/logage_slides/images_fixed")
