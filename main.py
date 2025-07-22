from src.utils import *
from src.discord import Discord
from src.instagram import Instagram
from src.snapchat import SnapChat
from src.whatsapp import WhatsApp
from src.merge_all import Merge

txt_networks = [("Discord", Discord),
                ("Instagram", Instagram),
                ("SnapChat", SnapChat),
                ("WhatsApp", WhatsApp)] # name, class

def create_export_directories():
    for s in txt_networks:
        create_directory(f"social_exports/{s[0]}")

def set_path_whatsapp(folder, cls):
    paths = []
    for path in folder.glob(f"*.zip"):
        paths.append(path)
    if len(paths) == 0:
        return None
    return cls(paths)

def run_all_stats(s_n):
    for n in s_n:
        n.start_process()

def set_all_path():
    s_n = []
    for name, cls in txt_networks:
        folder = Path(f"social_exports/{name}")
        if name == "WhatsApp":
            WA = set_path_whatsapp(folder, WhatsApp)
            if WA is not None:
                s_n.append(WA)
            continue
        for path in folder.glob(f"*.zip"):
            s_n.append(cls(path))
    if s_n:
        s_n.append(Merge(s_n))
    return s_n

if __name__ == "__main__":
    create_export_directories()
    social_networks = set_all_path()
    while not social_networks:
        input("No packages were found. Please add your zip files to social_export/SocialNetwork. Press Enter when finished.")
        social_networks = set_all_path()
    answer = ask("Which social network do you want to analyse?", social_networks)
    try:
        answer.start_process()
    except KeyboardInterrupt:
        print("Program interrupted.")