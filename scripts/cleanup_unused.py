import os
import shutil

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET_DIRS = [
    os.path.join(BASE_DIR, "Gurux.DLMS.Python", "Gurux.DLMS.Push.Listener.Example.python"),
    os.path.join(BASE_DIR, "Gurux.DLMS.Python", "Gurux.DLMS.XmlClient.python"),
]

def cleanup():
    for target in TARGET_DIRS:
        if os.path.exists(target):
            try:
                shutil.rmtree(target)
                print(f"[REMOVED] {target}")
            except Exception as e:
                print(f"[ERROR] Could not remove {target}: {e}")
        else:
            print(f"[NOT FOUND] {target}")

if __name__ == "__main__":
    cleanup()
