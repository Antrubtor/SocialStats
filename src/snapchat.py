from src.socialnetwork import *

class SnapChat(SocialNetwork):
    def start_process(self):
        actions = [
            Action("I want to do statistics on messages", self.messages_process),
            Action("I want to tidy up the media", self.medias_process)
        ]
        selected = ask("What do you want to do with your Snapchat package?", actions)
        selected.execute()

    def messages_process(self):
        try:
            with zipfile.ZipFile(self.path, mode="r") as package:
                with package.open("json/account.json", mode="r") as account:
                    sections = json.load(account)
                    pseudo = sections["Basic Information"]["Username"]
                    creation_date = sections["Basic Information"]["Creation Date"]
                    print(f"Your account named {pseudo}, created on {creation_date}, was found")

                with package.open("json/chat_history.json", mode="r") as msg:
                    sections = json.load(msg)
                    messages_per_day = {} # date : { name : (nb_you, nb_oth), name : (nb_you, nb_oth) }

                    nb_msg, character = 0, 0
                    for contact, messages in sections.items():
                        nb_character_contact, nb_msg_contact = 0, 0
                        for message in messages:
                            nb_msg_contact += 1
                            if message["Media Type"] == "TEXT" and message["Content"] is not None:
                                nb_character_contact += len(message["Content"])
                            date = datetime.strptime(message["Created"], "%Y-%m-%d %H:%M:%S %Z").strftime("%Y/%m/%d")
                            if date not in messages_per_day:
                                messages_per_day[date] = {}
                            nb_you, nb_oth = messages_per_day[date].get(contact, (0, 0))
                            if message["From"] != pseudo:
                                nb_oth += 1
                            else:
                                nb_you += 1
                            messages_per_day[date][contact] = (nb_you, nb_oth)
                        print(f"{contact} contains {nb_msg_contact} messages with {nb_character_contact} characters")
                        character += nb_character_contact
                        nb_msg += nb_msg_contact

                    print(f"\nLoaded {nb_msg} messages in total with {character} characters")
                    return messages_per_day
        except Exception as e:
            print(e)


    def medias_process(self):
        print("Media processing")
        pass