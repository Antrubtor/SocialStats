import os
import sys
from pathlib import Path
import zipfile
from InquirerPy import inquirer
from src.discord import Discord
from src.instagram import Instagram
from src.snapchat import SnapChat
from src.whatsapp import WhatsApp

txt_networks = [("Discord", "zip", Discord), ("Instagram", "zip", Instagram), ("SnapChat", "zip", SnapChat), ("WhatsApp", "zip", WhatsApp)] # name, extension of package's file, class

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

def ask(question, options):
    if sys.stdin.isatty():
        return inquirer.select(
            message=question,
            choices=options
        ).execute()
    else:
        print(question)
        for i, option in enumerate(options, 1):
            print(f"{i}. {option}")
        while True:
            try:
                choice = int(input("Choose an option: "))
                if 1 <= choice <= len(options):
                    return options[choice - 1]
            except ValueError:
                print("Please enter a valid choice.")

def set_all_path():
    s_n = []
    for name, ext, cls in txt_networks:
        folder = Path(f"social_exports/{name}")
        for path in folder.glob(f"*.{ext}"):
            s_n.append(cls(path))
    return s_n



create_export_directories()
social_networks = set_all_path()
answer = ask("Which social network do you want to analyse?", social_networks)
