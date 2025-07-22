import datetime

from src.socialnetwork import *

class WhatsApp(SocialNetwork):
    def __str__(self):
        string = f"{self.__class__.__name__}: ["
        for i in range(len(self.path)):
            string += str(self.path[i].relative_to(f"social_exports/{self.__class__.__name__}")).replace("WhatsApp Chat with ", "").replace(".zip", "")
            if i != len(self.path)-1:
                string += ", "
        return string + "]"

    def start_process(self):
        actions = [
            Action("I want to do statistics on messages", self.messages_process),
            Action("I want to export conversations to a unified JSON format (work in progress)", self.export_process)
        ]
        selected = ask(f"What do you want to do with your {self.__class__.__name__} package?", actions)
        selected.execute()


    def __parse_whatsapp_chat(self, text):
        msg_pattern = re.compile(r"^(\d{1,2}/\d{1,2}/\d{2,4}), (\d{2}:\d{2}) - ")
        messages = []
        current_msg = None

        for line in text.splitlines():
            if msg_pattern.match(line):
                match = msg_pattern.match(line)
                date_str = f"{match.group(1)}, {match.group(2)}" # parse date

                for fmt in ["%d/%m/%Y, %H:%M", "%d/%m/%y, %H:%M"]:
                    try:
                        timestamp = datetime.strptime(date_str, fmt)
                        break
                    except ValueError:
                        timestamp = None
                if not timestamp:
                    continue  # corrupted

                content = line[match.end():]

                if ": " in content:
                    author, message = content.split(": ", 1)
                else:
                    continue  # system message

                if current_msg:
                    messages.append(current_msg)

                current_msg = {
                    "datetime": timestamp,
                    "author": author,
                    "message": message
                }
            else: # Multiline messages
                if current_msg:
                    current_msg["message"] += "\n" + line
        if current_msg:
            messages.append(current_msg)
        return messages


    def messages_stats(self, min_messages):
        try:
            # min_messages = ask_number("Minimum number of messages per contact (0 for no limit set)?")
            messages_per_day = {}  # date : { name : (nb_you, nb_oth), name : (nb_you, nb_oth) }
            hour_distribution = [0] * 24
            per_contact_stats = defaultdict(list)

            total_msg, total_chr = 0, 0
            pseudo = None
            for chat in tqdm(self.path):
                with zipfile.ZipFile(chat, mode="r") as package:
                    for file in package.infolist():
                        if file.filename.endswith(".txt"):
                            contact = file.filename.replace("WhatsApp Chat with ", "").replace(".txt", "")
                            with package.open(file.filename, mode="r") as msg:
                                messages = self.__parse_whatsapp_chat(msg.read().decode("utf-8"))
                                if min_messages > 0 and len(messages) < min_messages:
                                    continue
                                if not pseudo:
                                    participants = set()
                                    for message in messages:
                                        participants.add(message["author"])
                                    pseudo = ask("What is your name ?", list(participants))
                                msg_you = msg_oth = char_you = char_oth = 0
                                delays_you, delays_oth = [], []
                                last_sender = None
                                last_timestamp = None
                                for message in tqdm(messages, leave=False):
                                    is_you = message["author"] == pseudo

                                    # Hour distribution
                                    dt = message["datetime"]
                                    date_str = dt.strftime("%d/%m/%Y")
                                    hour = dt.hour
                                    if is_you:
                                        hour_distribution[hour] += 1
                                    if date_str not in messages_per_day:
                                        messages_per_day[date_str] = {}

                                    # Messages per day
                                    nb_you, nb_oth = messages_per_day[date_str].get(contact, (0, 0))
                                    if is_you:
                                        nb_you += 1
                                    else:
                                        nb_oth += 1
                                    messages_per_day[date_str][contact] = (nb_you, nb_oth)

                                    # Number of messages and char by contact
                                    content = message["message"]
                                    nb_chars = len(content)
                                    if is_you:
                                        msg_you += 1
                                        char_you += nb_chars
                                    else:
                                        msg_oth += 1
                                        char_oth += nb_chars

                                    # Message delay
                                    if last_sender is not None and last_sender != is_you and last_timestamp is not None:
                                        delay = abs(dt - last_timestamp)
                                        if is_you:
                                            delays_you.append(delay)
                                        else:
                                            delays_oth.append(delay)
                                    last_sender = is_you
                                    last_timestamp = dt

                                    total_chr += nb_chars
                                    total_msg += 1
                                avg_delay_you = sum(delays_you, timedelta()) / len(delays_you) if delays_you else timedelta(0)
                                avg_delay_oth = sum(delays_oth, timedelta()) / len(delays_oth) if delays_oth else timedelta(0)

                                per_contact_stats["Contact"].append(contact)

                                per_contact_stats["Messages"].append(msg_you + msg_oth)
                                per_contact_stats["Messages sent by you"].append(msg_you)
                                per_contact_stats["Messages sent by your contact"].append(msg_oth)

                                per_contact_stats["Characters"].append(char_you + char_oth)
                                per_contact_stats["Characters sent by you"].append(char_you)
                                per_contact_stats["Characters sent by your contact"].append(char_oth)

                                per_contact_stats["Your answer delay"].append(avg_delay_you)
                                per_contact_stats["Contact answer delay"].append(avg_delay_oth)

            print(f"\nLoaded {total_msg} messages in total with {total_chr} characters")
            return per_contact_stats, messages_per_day, hour_distribution, f"{self.__class__.__name__}_{pseudo}"
        except Exception as e:
            print(e)

    def export_process(self):
        print("Wait for next updates to get this feature")
        pass