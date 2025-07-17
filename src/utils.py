import sys
import json
import zipfile
from tqdm import tqdm
from InquirerPy import inquirer
from datetime import datetime, timedelta

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

def ask_number(question):
    if sys.stdin.isatty():
        return int(inquirer.number(
            message=question
        ).execute())
    else:
        print(question)
        while True:
            try:
                value = int(input("⮕ "))
                return value
            except ValueError:
                print("Please enter a valid number.")

class Action:
    def __init__(self, label, func):
        self.label = label
        self.func = func

    def __str__(self):
        return self.label

    def execute(self):
        self.func()