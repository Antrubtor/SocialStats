from src.socialnetwork import *

class Instagram(SocialNetwork):
    def start_process(self):
        actions = [
            Action("I want to do statistics on messages", self.messages_process),
            Action("I want to export conversations to a unified JSON format (work in progress)", self.export_process),
            Action("I want to tidy up the media", self.medias_process)
        ]
        selected = ask(f"What do you want to do with your {self.__class__.__name__} package?", actions)
        selected.execute()

    def messages_stats(self, min_messages):
        try:
            with zipfile.ZipFile(self.path, mode="r") as package:
                with package.open("personal_information/personal_information/personal_information.json", mode="r") as account:
                    sections = json.load(account)
                    pseudo = sections["profile_user"][0]["string_map_data"]["Name"]["value"]

                with package.open("security_and_login_information/login_and_profile_creation/signup_details.json", mode="r") as account:
                    sections = json.load(account)
                    creation_date = datetime.fromtimestamp(sections["account_history_registration_info"][0]["string_map_data"]["Time"]["timestamp"])
                print(f"Your {self.__class__.__name__} account named {pseudo}, created on {creation_date}, was found")

                messages_per_day = {}  # date : { name : (nb_you, nb_oth), name : (nb_you, nb_oth) }
                hour_distribution = [0] * 24
                per_contact_stats = defaultdict(list)

                total_msg, total_chr = 0, 0
                msg_files = [file for file in package.infolist()
                             if file.filename.startswith("your_instagram_activity/messages/inbox")
                             and file.filename.endswith(".json")
                             and not file.is_dir()]
                for file in tqdm(msg_files):
                    with package.open(file, "r") as msg:
                        contact = file.filename.replace("your_instagram_activity/messages/inbox/", "").rsplit('/', 1)[0].rsplit('_', 1)[0]
                        chat = json.load(msg)
                        messages = chat["messages"]

                        if min_messages > 0 and len(messages) < min_messages:
                            continue

                        msg_you = msg_oth = char_you = char_oth = voice_you = voice_oth = 0
                        delays_you, delays_oth = [], []
                        last_sender = None
                        last_timestamp = None
                        for message in tqdm(messages, leave=False):
                            is_you = message["sender_name"] == pseudo

                            # Hour distribution
                            timestamp_ms = int(message["timestamp_ms"]) // 1000
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
                            if "content" in message:
                                content = message["content"]
                                nb_chars = len(content)
                                if is_you:
                                    msg_you += 1
                                    char_you += nb_chars
                                else:
                                    msg_oth += 1
                                    char_oth += nb_chars

                            # Voice message time
                            if "audio_files" in message:
                                for audio_file in message["audio_files"]:
                                    duration = get_mp4_duration(self.path, audio_file["uri"])
                                    # duration = 0    # TODO: remove
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
        try:
            with zipfile.ZipFile(self.path, mode="r") as package:
                msg_files = [file for file in package.infolist()
                             if file.filename.startswith("your_instagram_activity/messages/inbox")
                             and file.filename.endswith(".json")
                             and not file.is_dir()]
                for file in tqdm(msg_files):
                    with package.open(file, "r") as msg:
                        contact = file.filename.replace("your_instagram_activity/messages/inbox/", "").rsplit('/', 1)[0].rsplit('_', 1)[0]
                        chat = json.load(msg)
                        messages = chat["messages"]
                        for message in tqdm(messages, leave=False):

                            # Voice message time
                            if "audio_files" in message:
                                for audio_file in message["audio_files"]:
                                    duration = get_mp4_duration(self.path, audio_file["uri"])
                                    # duration = 0    # TODO: remove
                                    if is_you:
                                        voice_you += duration
                                    else:
                                        voice_oth += duration

                print(f"\nLoaded {total_msg} messages in total with {total_chr} characters")
                return per_contact_stats, messages_per_day, hour_distribution, f"{self.__class__.__name__}_{pseudo}"
        except Exception as e:
            print(e)