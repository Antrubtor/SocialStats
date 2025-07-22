from src.utils import *

class SocialNetwork:
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