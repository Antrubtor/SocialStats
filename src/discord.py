from tqdm import tqdm
from collections import defaultdict

from src.socialnetwork import *

class Discord(SocialNetwork):
    def start_process(self):
        actions = [
            Action("I want to do statistics on messages", self.messages_process),
            Action("I want to export conversations to a unified JSON format", self.export_process),
            Action("I want to search for messages with a regex", self.search_process)
        ]
        selected = ask(f"What do you want to do with your {self.__class__.__name__} package?", actions)
        selected.execute()

    @staticmethod
    def __snowflake_to_date(timestamp):
        base_datetime = datetime(1970, 1, 1)
        convert = int(timestamp) / 4194304 + 1420070400000
        delta = timedelta(0, 0, 0, convert)
        return base_datetime + delta

    @staticmethod
    def __voice_times_by_user(package, channels_name_id):
        def parse_discord_timestamp(ts):
            return datetime.fromisoformat(ts.strip('"').replace("Z", "+00:00"))
        call_per_id = defaultdict(tuple)  # {rtc_connection_id: (channel_id, join_voice_channel, leave_voice_channel)}
        event_files = [file for file in package.infolist()
                     if "events" in file.filename
                     and file.filename.endswith(".json")
                     and not file.is_dir()]
        for file in tqdm(event_files):
            with package.open(file, "r") as event_file:
                for raw_line in tqdm(event_file, leave=False):
                    try:
                        line = raw_line.decode("utf-8").strip()
                        if not line:
                            continue
                        event = json.loads(line)
                        if event["event_type"] == "join_voice_channel"  and "rtc_connection_id" in event:
                            end = None
                            rtc = call_per_id[event["rtc_connection_id"]]
                            if rtc is not None and rtc != ():
                                end = rtc[2]
                            call_per_id[event["rtc_connection_id"]] = (event["channel_id"], parse_discord_timestamp(event["timestamp"]), end)
                        if event["event_type"] == "leave_voice_channel" and "rtc_connection_id" in event:
                            start = None
                            rtc = call_per_id[event["rtc_connection_id"]]
                            if rtc is not None and rtc != ():
                                start = rtc[1]
                            call_per_id[event["rtc_connection_id"]] = (event["channel_id"], start, parse_discord_timestamp(event["timestamp"]))
                    except Exception as e:
                        print(f"Failed to parse event: {e}")
        call_per_user = defaultdict(timedelta)  # { user: time }
        total_voice_times = timedelta(0)
        max_time = timedelta(0)
        for rtc_id, call_data in call_per_id.items():
            if call_data[1] and call_data[2]:
                duration = call_data[2] - call_data[1]
                max_time = max(max_time, duration)
                if call_data[0] in channels_name_id:
                    call_per_user[channels_name_id[call_data[0]]] += duration
                total_voice_times += duration
        print(f"Your total call time is {total_voice_times} and your longest call was {max_time}.")
        return call_per_user

    @staticmethod
    def __get_file_and_id(package):
        messages_files_idx = [file for file in package.infolist()
                              if file.filename.endswith("index.json")
                              and not file.is_dir()]
        msg_file_name = "Messages"
        for msg_file in messages_files_idx: # check if "Messages/" is really the message folder
            try:
                with package.open(msg_file, mode="r") as channel_list:
                    channels_name_id = json.load(channel_list)
                    for chan_id, contact_name in channels_name_id.items():
                        if "Direct Message with" in contact_name:
                            channels_name_id[chan_id] = contact_name.replace("Direct Message with ", "")
                msg_file_name = msg_file.filename.split("/")[0]
            except:
                pass
        messages_files = [file.filename for file in package.infolist()
                          if msg_file_name in file.filename
                          and file.filename.endswith("/messages.json")
                          and not file.is_dir()]
        return messages_files, channels_name_id

    def messages_stats(self, min_messages):
        try:
            with zipfile.ZipFile(self.path, mode="r") as package:
                account_files = [file for file in package.infolist()
                                 if file.filename.endswith("user.json")
                                 and not file.is_dir()]
                for acc_file in account_files:
                    try:
                        with package.open(acc_file, mode="r") as account:
                            sections = json.load(account)
                            pseudo = sections["username"]
                            date = self.__snowflake_to_date(sections["id"])
                            creation_date = f"{date.day}/{date.month}/{date.year} at {date.hour}:{date.minute}"
                            print(f"Your {self.__class__.__name__} account named {pseudo}, created on {creation_date}, was found")
                            break
                    except:
                        pass

                messages_per_day = {}  # date: { name: (nb_you, nb_oth), name : (nb_you, nb_oth) }
                hour_distribution = [0] * 24
                per_contact_stats = defaultdict(list)

                total_msg, total_chr = 0, 0
                messages_files, channels_name_id = self.__get_file_and_id(package)
                for filename in tqdm(messages_files):
                    contact_id = re.search(r"c(\d+)/", filename)
                    if contact_id:
                        contact_id = contact_id.group(1)
                    if contact_id not in channels_name_id:
                        continue
                    contact = channels_name_id[contact_id].replace("#0", "")
                    with package.open(filename, mode="r") as msg:
                        messages = json.load(msg)
                        if min_messages > 0 and len(messages) < min_messages:
                            continue
                        msg_you = msg_oth = char_you = char_oth = 0
                        for message in tqdm(messages, leave=False):
                            # Hour distribution
                            dt = self.__snowflake_to_date(message["ID"])
                            date_str = dt.strftime("%d/%m/%Y")
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
                # call_per_user = {}    # TODO: remove
                call_per_user = self.__voice_times_by_user(package, channels_name_id)
                for user in per_contact_stats["Contact"]:
                    if user not in call_per_user:
                        per_contact_stats["Call time"].append("0h0m")
                    else:
                        hours, remainder = divmod(call_per_user[user].total_seconds(), 3600)
                        minutes, _ = divmod(remainder, 60)
                        per_contact_stats["Call time"].append(f"{int(hours)}h{int(minutes)}m")
                return per_contact_stats, messages_per_day, hour_distribution, f"{self.__class__.__name__}_{pseudo}"
        except Exception as e:
            print(e)


    def export_process(self):
        try:
            with zipfile.ZipFile(self.path, mode="r") as package:
                export_folder = self.export_JSON_folder
                messages_files, channels_name_id = self.__get_file_and_id(package)
                for filename in tqdm(messages_files):
                    contact_id = re.search(r"c(\d+)/", filename)
                    if contact_id:
                        contact_id = contact_id.group(1)
                    if contact_id not in channels_name_id:
                        continue
                    contact = channels_name_id[contact_id].replace("#0", "")
                    with package.open(filename, mode="r") as msg:
                        messages = json.load(msg)
                        JSON_messages = []
                        for message in messages:
                            dt = self.__snowflake_to_date(message["ID"])
                            current_msg = {
                                "datetime": str(dt),
                                "author": "You",
                                "message": message["Contents"],
                                "medias": []
                            }
                            JSON_messages.append(current_msg)
                        contact = re.sub(r'[\\/:*?"<>|]', "_", contact).rstrip(" .")    # remove bad char of filename
                        with open(f"{export_folder}/{contact}.json", 'w', encoding="utf-8") as f:
                            json.dump(JSON_messages, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(e)