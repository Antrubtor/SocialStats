import pathlib

class SocialNetwork:
    def __init__(self, path):
        self.path = path

    def __str__(self):
        return f"{self.__class__.__name__}: {self.path.relative_to(f"social_exports/{self.__class__.__name__}")}"