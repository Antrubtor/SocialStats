import io
import json
from tqdm import tqdm
from collections import defaultdict

from src.socialnetwork import *

class SnapChat(SocialNetwork):
    def start_process(self):
        actions = [
            Action("I want to do statistics on messages", self.messages_process),
            Action("I want to export conversations to a unified JSON format", self.export_process),
            Action("I want to export the media for my gallery (with their date and author)", self.medias_process),
            Action("I want to display all my journeys on a map", self.map_process)
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
                    messages_per_day = {} # date: { name: (nb_you, nb_oth), name : (nb_you, nb_oth) }
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
        try:
            with zipfile.ZipFile(self.path, mode="r") as package:
                export_folder = os.path.join("JSON_Chats", self.__class__.__name__)
                create_directory(export_folder)
                with package.open("json/chat_history.json", mode="r") as msg:
                    sections = json.load(msg)
                    JSON_messages = []
                    for contact, messages in tqdm(sections.items()):
                        for message in messages:
                            timestamp_ms = int(message["Created(microseconds)"]) // 1000
                            dt = datetime.fromtimestamp(timestamp_ms)
                            media = []
                            if message["Media IDs"] != "":
                                media.append(message["Media IDs"])
                            current_msg = {
                                "datetime": str(dt),
                                "author": message["From"],
                                "message": message["Content"],
                                "medias": media
                            }
                            JSON_messages.append(current_msg)
                        with open(f"{export_folder}/{contact}.json", 'w', encoding="utf-8") as f:
                            json.dump(JSON_messages, f, ensure_ascii=False, indent=4)
            print(f"All chats exported to {os.path.join(os.getcwd(), export_folder)}")
        except Exception as e:
            print(e)

    def medias_process(self):
        MP4 = lazy_import("mutagen.mp4").MP4
        piexif = lazy_import("piexif")
        try:
            with zipfile.ZipFile(self.path, mode="r") as package:
                with package.open("json/account.json", mode="r") as account:
                    sections = json.load(account)
                    pseudo = sections["Basic Information"]["Username"]
                media_ids_files = {}
                for filename in package.namelist():
                    if filename.startswith("chat_media/") and "_" in filename:
                        try:
                            media_ids_files[filename.split("_")[2].split(".")[0]] = {"filename": filename}
                        except IndexError:
                            continue
                nb = 0
                with package.open("json/chat_history.json", mode="r") as msg:
                    sections = json.load(msg)
                    export_folder = os.path.join("Media", self.__class__.__name__)
                    create_directory(export_folder)
                    for contact, messages in tqdm(sections.items()):
                        for message in tqdm(messages):
                            media_id = message.get("Media IDs")
                            if message["Media Type"] == "NOTE" and media_id:    # Remove all audio msg
                                media_ids_files.pop(media_id, None)

                            if message["Media Type"] == "MEDIA" and media_id and media_id in media_ids_files:
                                timestamp_ms = int(message["Created(microseconds)"]) // 1000
                                media_ids_files[media_id]["date"] = datetime.fromtimestamp(timestamp_ms)
                                media_ids_files[media_id]["contact"] = contact
                                if message["From"] == pseudo:
                                    media_ids_files[media_id]["send"] = pseudo
                                    media_ids_files[media_id]["res"] = contact
                                else:
                                    media_ids_files[media_id]["send"] = contact
                                    media_ids_files[media_id]["res"] = pseudo
                    for _, infos in tqdm(media_ids_files.items(), leave=False):
                        path = infos["filename"]
                        file_name = path.split("/")[1]
                        ext = os.path.splitext(file_name)[1].lower()

                        with package.open(path) as source_file:
                            data = source_file.read()
                            dt = None

                            if ext in [".jpg", ".jpeg"]:
                                try:
                                    exif_dict = piexif.load(data)
                                    dt_bytes = exif_dict["Exif"].get(piexif.ExifIFD.DateTimeOriginal)
                                    if dt_bytes:
                                        dt_str = dt_bytes.decode("utf-8")
                                        dt = datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S")
                                except Exception:
                                    pass

                            elif ext == ".mp4":
                                try:
                                    mp4 = MP4(io.BytesIO(data))
                                    if "\xa9day" in mp4:
                                        dt = datetime.strptime(mp4["\xa9day"][0], "%Y-%m-%d")
                                except Exception:
                                    pass
                            check_no_date = False
                            if not dt:
                                check_no_date = True
                                if "date" in infos:
                                    dt = infos["date"]
                                else:
                                    dt = datetime.strptime(file_name.split("_")[0], "%Y-%m-%d")
                            ctt = ""
                            send = None
                            res = None
                            if "contact" in infos and "send" in infos and "res" in infos:
                                ctt = "_" + infos["contact"]
                                send = infos["send"]
                                res = infos["res"]
                            # Conflict
                            counter = 1
                            base_name = dt.strftime("%Y-%m-%d %H.%M.%S")
                            new_filename = f"{base_name}{ctt}{ext}"
                            out_path = os.path.join(export_folder, new_filename)
                            while os.path.exists(out_path):
                                new_filename = f"{base_name}{ctt}_{counter}{ext}"
                                out_path = os.path.join(export_folder, new_filename)
                                counter += 1
                            with open(out_path, "wb") as target_file:
                                target_file.write(data)
                            if check_no_date or "contact" in infos:
                                if "contact" in infos:
                                    add_metadata(out_path, dt, ext, infos["contact"], send, res)
                                else:
                                    add_metadata(out_path, dt, ext)
                        nb += 1

                    memories_files = [file for file in package.infolist()
                                 if file.filename.startswith("memories")
                                 and (file.filename.endswith(".mp4") or file.filename.endswith(".jpg") or file.filename.endswith(".png") or file.filename.endswith(".webp"))
                                 and not file.is_dir()]
                    for memory in tqdm(memories_files, leave=False):
                        with package.open(memory.filename) as source_file:
                            data = source_file.read()
                        file_name = memory.filename.split("/")[-1]
                        ext = os.path.splitext(file_name)[1].lower()
                        dt = datetime.strptime(file_name.split("_")[0], "%Y-%m-%d")
                        counter = 1
                        base_name = dt.strftime("%Y-%m-%d %H.%M.%S")
                        new_filename = f"{base_name}{ext}"
                        out_path = os.path.join(export_folder, new_filename)
                        while os.path.exists(out_path):
                            new_filename = f"{base_name}_{counter}{ext}"
                            out_path = os.path.join(export_folder, new_filename)
                            counter += 1
                        with open(out_path, "wb") as target_file:
                            target_file.write(data)
                        add_metadata(out_path, dt, ext)
                        nb += 1
                    print(f"\n{nb} media exported in {os.path.join(os.getcwd(), export_folder)}")
        except Exception as e:
            print(e)

    @staticmethod
    def __parse_coord(coord_s):
        try:
            parts = coord_s.split(",")
            lat_str = parts[0].split("±")[0].strip()
            lon_str = parts[1].split("±")[0].strip()
            return float(lat_str), float(lon_str)
        except Exception as e:
            print(f"Failed to parse {coord_s}: {e}")
            return None, None

    def map_process(self):
        try:
            import folium
        except ImportError:
            raise RuntimeError("You must install all libraries to use this feature")
        try:
            with zipfile.ZipFile(self.path, mode="r") as package:
                with package.open("json/location_history.json", mode="r") as loc:
                    sections = json.load(loc)
                    data = sections["Location History"]

                    points = []
                    for date_s, coord_s in data:
                        dt = datetime.strptime(date_s, "%Y-%m-%d %H:%M:%S %Z")

                        lat, lon = self.__parse_coord(coord_s)
                        if dt is None or lat is None or lon is None:
                            continue
                        points.append((dt, lat, lon, coord_s))

                    points.sort(key=lambda x: x[0])

                    if not points:
                        print("Error with data")
                        return

                    m = folium.Map(location=[points[0][1], points[0][2]], zoom_start=6)

                    for i, (dt, lat, lon, orig) in enumerate(points, start=1):
                        popup_html = f"<b>{dt.isoformat()}</b><br/>{orig}"
                        folium.CircleMarker(
                            location=[lat, lon],
                            radius=4,
                            color="blue",
                            fill=True,
                            fill_color="blue",
                            popup=folium.Popup(popup_html, max_width=300),
                            tooltip=f"{i}. {dt.strftime('%Y-%m-%d %H:%M:%S')}"
                        ).add_to(m)

                    coords = [(lat, lon) for _, lat, lon, _ in points]
                    folium.PolyLine(coords, color="red", weight=3, opacity=0.8).add_to(m)

                    m.save("map.html")
                    print(f"Map successfully saved to {os.path.join(os.getcwd(), "map.html")}")
        except Exception as e:
            print(e)