from src.socialnetwork import *

class SnapChat(SocialNetwork):
    def start_process(self):
        actions = [
            Action("I want to do statistics on messages", self.messages_process),
            Action("I want to export conversations to a unified JSON format (work in progress)", self.export_process),
            Action("I want to tidy up the media (work in progress)", self.medias_process)
        ]
        selected = ask(f"What do you want to do with your {self.__class__.__name__} package?", actions)
        selected.execute()

    def messages_stats(self, min_messages):
        try:
            with zipfile.ZipFile(self.path, mode="r") as package:
                with package.open("json/account.json", mode="r") as account:
                    sections = json.load(account)
                    pseudo = sections["Basic Information"]["Username"]
                    creation_date = sections["Basic Information"]["Creation Date"]
                    print(f"Your {self.__class__.__name__} account named {pseudo}, created on {creation_date}, was found")

                media_ids_files = {}
                for filename in package.namelist():
                    if filename.startswith("chat_media/") and "_" in filename:
                        try:
                            media_ids_files[filename.split("_")[2].split(".")[0]] = filename
                        except IndexError:
                            continue
                # media_ids_files = {}    # TODO: remove

                with package.open("json/chat_history.json", mode="r") as msg:
                    sections = json.load(msg)
                    messages_per_day = {} # date : { name : (nb_you, nb_oth), name : (nb_you, nb_oth) }
                    hour_distribution = [0] * 24
                    per_contact_stats = defaultdict(list)

                    total_msg, total_chr = 0, 0
                    for contact, messages in tqdm(sections.items()):
                        if min_messages > 0 and len(messages) < min_messages:
                            continue

                        msg_you = msg_oth = char_you = char_oth = voice_you = voice_oth = 0
                        delays_you, delays_oth = [], []
                        last_sender = None
                        last_timestamp = None
                        for message in tqdm(messages, leave=False):
                            is_you = message["IsSender"]

                            # Hour distribution
                            timestamp_ms = int(message["Created(microseconds)"]) // 1000
                            dt = datetime.fromtimestamp(timestamp_ms)
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
                            content = message["Content"]
                            nb_chars = len(content) if message["Media Type"] == "TEXT" and content else 0
                            if is_you:
                                msg_you += 1
                                char_you += nb_chars
                            else:
                                msg_oth += 1
                                char_oth += nb_chars

                            # Voice message time
                            media_id = message.get("Media IDs")
                            if message["Media Type"] == "NOTE" and media_id:
                                if media_id in media_ids_files:
                                    duration = get_mp4_duration(self.path, media_ids_files[media_id])
                                    if is_you:
                                        voice_you += duration
                                    else:
                                        voice_oth += duration

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

                        per_contact_stats["Voice message time"].append(timedelta(seconds=voice_you + voice_oth))
                        per_contact_stats["Your voice message time"].append(timedelta(seconds=voice_you))
                        per_contact_stats["Contact voice message time"].append(timedelta(seconds=voice_oth))

                        per_contact_stats["Your answer delay"].append(avg_delay_you)
                        per_contact_stats["Contact answer delay"].append(avg_delay_oth)

                    print(f"\nLoaded {total_msg} messages in total with {total_chr} characters")
                    return per_contact_stats, messages_per_day, hour_distribution, f"{self.__class__.__name__}_{pseudo}"
        except Exception as e:
            print(e)

    def export_process(self):
        print("Wait for next updates to get this feature")
        pass
    def medias_process(self):
        print("Wait for next updates to get this feature")
        pass