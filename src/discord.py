import re
from src.socialnetwork import *
from collections import defaultdict

class Discord(SocialNetwork):
    def start_process(self):
        actions = [
            Action("I want to do statistics on messages", self.messages_process)
        ]
        selected = ask("What do you want to do with your Snapchat package?", actions)
        selected.execute()

    def __snowflake_to_date(self, id):
        base_datetime = datetime(1970, 1, 1)
        convert = int(id) / 4194304 + 1420070400000
        delta = timedelta(0, 0, 0, convert)
        return base_datetime + delta

    def messages_stats(self):
        try:
            with zipfile.ZipFile(self.path, mode="r") as package:
                with package.open("Account/user.json", mode="r") as account:
                    sections = json.load(account)
                    pseudo = sections["username"]
                    date = self.__snowflake_to_date(sections["id"])
                    creation_date = f"{date.day}/{date.month}/{date.year} at {date.hour}:{date.minute}"
                    print(f"Your account named {pseudo}, created on {creation_date}, was found")

                with package.open("Messages/index.json", mode="r") as channel_list:
                    channels_name_id = json.load(channel_list)

                min_messages = ask_number("Minimum number of messages per contact (0 for no limit set)?")

                messages_per_day = {}  # date : { name : (nb_you, nb_oth), name : (nb_you, nb_oth) }
                hour_distribution = [0] * 24
                per_contact_stats = defaultdict(list)

                total_msg, total_chr = 0, 0
                for filename in tqdm(package.namelist()):
                    # print(filename)
                    if filename.startswith("Messages/") and filename.endswith("/messages.json"):
                        contact_id = re.search(r"c(\d+)/", filename)
                        if contact_id:
                            contact_id = contact_id.group(1)
                        if contact_id not in channels_name_id:
                            continue
                        contact = channels_name_id[contact_id]
                        if "Direct Message with" in contact:
                            contact = contact.replace("Direct Message with ", "")
                        with package.open(filename, mode="r") as msg:
                            messages = json.load(msg)

                            if min_messages > 0 and len(messages) < min_messages:
                                continue
                            msg_you = msg_oth = char_you = char_oth = 0
                            for message in tqdm(messages, leave=False):
                                # Hour distribution
                                dt = self.__snowflake_to_date(message["ID"])
                                date_str = dt.strftime("%m/%d/%Y")
                                hour = dt.hour
                                hour_distribution[hour] += 1
                                if date_str not in messages_per_day:
                                    messages_per_day[date_str] = {}

                                # Messages per day
                                nb_you, nb_oth = messages_per_day[date_str].get(contact, (0, 0))
                                nb_you += 1
                                messages_per_day[date_str][contact] = (nb_you, nb_oth)

                                # Number of messages and char by contact
                                content = message["Contents"]
                                nb_chars = len(content) if content else 0
                                msg_you += 1
                                char_you += nb_chars

                                total_chr += nb_chars
                                total_msg += 1

                            per_contact_stats["Contact"].append(contact)

                            per_contact_stats["Messages"].append(msg_you + msg_oth)
                            per_contact_stats["Messages sent by you"].append(msg_you)
                            per_contact_stats["Messages sent by your contact"].append(msg_oth)

                            per_contact_stats["Characters"].append(char_you + char_oth)
                            per_contact_stats["Characters sent by you"].append(char_you)
                            per_contact_stats["Characters sent by your contact"].append(char_oth)

                print(f"\nLoaded {total_msg} messages in total with {total_chr} characters")
                return per_contact_stats, messages_per_day, hour_distribution
            return {}, {}, []
        except Exception as e:
            print(e)