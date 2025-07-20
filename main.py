import os
from src.utils import *
from src.discord import Discord
from src.instagram import Instagram
from src.snapchat import SnapChat
from src.whatsapp import WhatsApp

txt_networks = [("Discord", Discord),
                ("Instagram", Instagram),
                ("SnapChat", SnapChat),
                ("WhatsApp", WhatsApp)] # name, class

def create_directory(nested_directory):
    try:
        os.makedirs(nested_directory)
        print(f"Directory '{nested_directory}' created successfully.")
    except FileExistsError:
        pass
    except PermissionError:
        print(f"Permission denied: Unable to create '{nested_directory}'.")
    except Exception as e:
        print(f"An error occurred: {e}")

def create_export_directories():
    for s in txt_networks:
        create_directory(f"social_exports/{s[0]}")

def set_path_whatsapp(folder, cls):
    paths = []
    for path in folder.glob(f"*.zip"):
        paths.append(path)
    return cls(paths)

def run_all_stats(s_n):
    for n in s_n:
        n.start_process()

def set_all_path():
    s_n = []
    for name, cls in txt_networks:
        folder = Path(f"social_exports/{name}")
        if name == "WhatsApp":
            s_n.append(set_path_whatsapp(folder, WhatsApp))
            break
        for path in folder.glob(f"*.zip"):
            s_n.append(cls(path))
    if s_n:
        s_n.append("All")
    return s_n

create_export_directories()
social_networks = set_all_path()
answer = ask("Which social network do you want to analyse?", social_networks)
if answer == "All":
    run_all_stats(social_networks)
else:
    answer.start_process()