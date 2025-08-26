import re
import json

from src.utils import *

class SocialNetwork:
    @property
    def export_JSON_folder(self):
        path = os.path.join("JSON_Chats", self.__class__.__name__)
        if not os.path.exists(path):
            create_directory(path)
        return path

    @property
    def export_MEDIA_folder(self):
        path = os.path.join("Media", self.__class__.__name__)
        if not os.path.exists(path):
            create_directory(path)
        return path

    def __init__(self, path):
        self.path = path

    def __str__(self):
        path = self.path.relative_to(f"social_exports/{self.__class__.__name__}")
        return f"{self.__class__.__name__}: {path}"

    def start_process(self):
        return NotImplemented

    def messages_stats(self, min_messages):
        return NotImplemented

    def messages_process(self):
        min_messages = ask_number("Minimum number of messages per contact (0 for no limit set)?")
        per_contact_stats, messages_per_day, hour_distribution, excel_name = self.messages_stats(min_messages)
        generate_excel(per_contact_stats, messages_per_day, hour_distribution, excel_name)

    def export_process(self):
        return NotImplemented

    def search_process(self):
        json_files = [f for f in os.listdir(self.export_JSON_folder) if f.endswith(".json")]
        if not json_files:
            self.export_process()

        pattern = str(input("Please give the regex: "))
        regex = re.compile(pattern, re.IGNORECASE)
        results = []

        for filename in os.listdir(self.export_JSON_folder):
            if not str(filename).endswith(".json"):
                continue

            filepath = os.path.join(self.export_JSON_folder, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                print(f"Can't read {filename}: {e}")
                continue

            for entry in data:
                message = entry.get("message", "")
                if message == "" or not message:
                    continue
                if regex.search(message):
                    results.append({
                        "file": filename,
                        "datetime": entry.get("datetime"),
                        "author": entry.get("author"),
                        "message": message
                    })

        for m in results:
            print(f"[{m['datetime']}] {m['author']} ({m['file']}): {m['message']}")
        print(f"{len(results)} results found")