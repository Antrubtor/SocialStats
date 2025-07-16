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
        # try:
            with zipfile.ZipFile(self.path, mode="r") as package:
                with package.open("json/account.json", mode="r") as account:
                    sections = json.load(account)
                    pseudo = sections["Basic Information"]["Username"]
                    creation_date = sections["Basic Information"]["Creation Date"]
                    print(f"Your account named {pseudo}, created on {creation_date}, was found")

                with package.open("json/chat_history.json", mode="r") as msg:
                    sections = json.load(msg)
                    messages_per_day = {} # date : { name : (nb_you, nb_oth), name : (nb_you, nb_oth) }
                    hour_distribution = [0] * 24
                    per_contact_stats = {}  # contact: (char_you, char_oth, msg_you, msg_oth, voice_msg_you, voice_msg_oth)
                    total_msg, total_chr = 0, 0
                    for contact, messages in sections.items():
                        for message in messages:
                            is_you = message["IsSender"]
                            dt = datetime.fromtimestamp(int(message["Created(microseconds)"]) // 1000)
                            date_str = dt.strftime("%m/%d/%Y")
                            hour = dt.hour
                            if is_you:
                                hour_distribution[hour] += 1
                            if date_str not in messages_per_day:
                                messages_per_day[date_str] = {}

                            nb_you, nb_oth = messages_per_day[date_str].get(contact, (0, 0))
                            if is_you:
                                nb_oth += 1
                            else:
                                nb_you += 1
                            messages_per_day[date_str][contact] = (nb_you, nb_oth)
                            content = message["Content"]
                            nb_chars = len(content) if message["Media Type"] == "TEXT" and content else 0
                            char_you, char_oth, msg_you, msg_oth = per_contact_stats.get(contact, (0, 0, 0, 0))
                            if is_you:
                                char_you += nb_chars
                                msg_you += 1
                            else:
                                char_oth += nb_chars
                                msg_oth += 1
                            per_contact_stats[contact] = (char_you, char_oth, msg_you, msg_oth)

                            total_chr += nb_chars
                            total_msg += 1

                    print(f"\nLoaded {total_msg} messages in total with {total_chr} characters")
                    print(messages_per_day)
                    # print(per_contact_stats)
                    # print(hour_distribution)
                    return messages_per_day, per_contact_stats, hour_distribution
        # except Exception as e:
        #     print(e)


    def medias_process(self):
        print("Media processing")
        pass