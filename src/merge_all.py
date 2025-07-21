import csv
from functools import partial
from src.socialnetwork import *
from src.discord import Discord

class Merge:
    def __init__(self, packages):
        self.packages = packages

    def __str__(self):
        return "All (create an excel file that lists all the data from all the platforms)"

    def start_process(self):
        if not os.path.exists("merge_map.csv"):
            generate_merge_template("merge_map.csv")
            ask("Have you completed the merge_map.csv file that allows you to merge people who have different usernames between social networks?", ["Yes", "No"])
        else:
            print("If you haven't done so, you can complete the merge_map.csv file, which allows you to merge people who have different usernames between social networks.")
        all_stats = []
        only_your_msg_chat = 0
        for package in self.packages:
            if isinstance(package, SocialNetwork):
                all_stats.append(package.messages_stats())
            if isinstance(package, Discord):
                only_your_msg_chat += 1
        for stats in all_stats:
            per_contact_stats, messages_per_day, hour_distribution, excel_name = stats
            generate_excel(per_contact_stats, messages_per_day, hour_distribution, excel_name)
        mapping = self.__load_merge_mapping("merge_map.csv")
        if len(all_stats) >= 2 and len(all_stats) != only_your_msg_chat:
            actions = [
                Action("I want to keep only statistics on messages sent by me", partial(self.__keep_only_me, all_stats, mapping)),
                Action("I want to make an estimate to balance the number of messages sent by other people with other chats", partial(self.__make_estimation, all_stats, mapping)),
                Action("I want to keep all the statistics (not very representative because the number of messages will be like \"doubled\" for certain social networks).", partial(self.__keep_all, all_stats, mapping))
            ]
            selected = ask(f"There are some chats where only your messages are listed by the social network, so how do you want to merge them?", actions)
            selected.execute()
        else:
            per_contact_stats, messages_per_day, hour_distribution = self.__merge_all_stats(all_stats, mapping)
            generate_excel(per_contact_stats, messages_per_day, hour_distribution, "merge")

    def __load_merge_mapping(self, filepath="merge_map.csv"):
        mapping = []
        with open(filepath, mode='r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if not row or row[0].startswith("#"):
                    continue
                mapping.append([cell.strip() for cell in row])
        return mapping

    def __keep_only_me(self, all_stats, mapping):
        for stats in all_stats:
            if "Messages" in stats[0]:
                del stats[0]["Messages"]
            if "Messages sent by you" in stats[0]:
                stats[0]["Messages"] = stats[0].pop("Messages sent by you")

            for date, user_msg in stats[1].items():
                for user, value in user_msg.items():
                    stats[1][date][user] = (value[0], 0)
        per_contact_stats, messages_per_day, hour_distribution = self.__merge_all_stats(all_stats, mapping)
        generate_excel(per_contact_stats, messages_per_day, hour_distribution, "merge")

    def __make_estimation(self, all_stats, mapping):
        your_msg = 0
        contact_msg = 0
        for stats in all_stats:
            if "Discord" not in stats[3]:
                for date, user_msg in stats[1].items():
                    for user, value in user_msg.items():
                        your_msg += value[0]
                        contact_msg += value[1]
        average = your_msg / contact_msg
        print(f"Your contacts send {average}x more messages than you on average")
        for stats in all_stats:
            if "Discord" in stats[3]:
                for date, user_msg in stats[1].items():
                    for user, value in user_msg.items():
                        stats[1][date][user] = (value[0], int(value[0] * average))
                if "Messages" in stats[0] and "Messages sent by you" in stats[0] and "Messages sent by your contact" in stats[0]:
                    for i in range(len(stats[0]["Messages sent by you"])):
                        stats[0]["Messages sent by your contact"][i] = int(stats[0]["Messages sent by you"][i] * average)
                        stats[0]["Messages"][i] = stats[0]["Messages sent by you"][i] + stats[0]["Messages sent by your contact"][i]
        per_contact_stats, messages_per_day, hour_distribution = self.__merge_all_stats(all_stats, mapping)
        generate_excel(per_contact_stats, messages_per_day, hour_distribution, "merge")


    def __keep_all(self, all_stats, mapping):
        per_contact_stats, messages_per_day, hour_distribution = self.__merge_all_stats(all_stats, mapping)
        generate_excel(per_contact_stats, messages_per_day, hour_distribution, "merge")

    def __merge_all_stats(self, all_stats, mapping):
        merged_stats = all_stats[0]
        current_length = len(merged_stats[0]["Contact"])
        for stats in all_stats[1:]:
            # per_contact_stats merge
            for category, value in stats[0].items():
                if category in merged_stats[0]:
                    merged_stats[0][category].extend(value)
                else:
                    merged_stats[0][category].extend([type(value[0])(0)] * current_length)  # fill holes with type
                    merged_stats[0][category].extend(value)
            current_length += len(stats[0]["Contact"])
            for category, value in merged_stats[0].items():
                if len(value) != current_length:
                    merged_stats[0][category].extend([type(value[0])(0)] * (current_length - len(merged_stats[0][category])))

            # messages_per_day merge
            for date, value in stats[1].items():
                if date in merged_stats[1]:
                    for contact in value:
                        if contact in merged_stats[1][date]:
                            merged_stats[1][date][contact] += value[contact]
                        else:
                            merged_stats[1][date][contact] = value[contact]
                else:
                    merged_stats[1][date] = value

            # hour_distribution merge
            for i in range(len(stats[2])):
                merged_stats[2][i] += stats[2][i]

        for name in mapping:
            # per_contact_stats merge with mapping
            merge_index = []
            contact_names = merged_stats[0]["Contact"]
            for i in range(len(contact_names)):
                if contact_names[i] in name:
                    merge_index.append(i)
            if len(merge_index) >= 2:
                for category, value in merged_stats[0].items():
                    merged_val = value[merge_index[0]]
                    if type(merged_val) == str and category != "Contact":
                        merged_val = ""
                    elif type(merged_val) != str:
                        for val in merge_index[1:]:
                            merged_val += value[val]
                        if "delay" in category:
                            merged_val /= len(merge_index)
                    merged_stats[0][category].append(merged_val)
                for category, value in merged_stats[0].items():
                    for i in range(len(merge_index) - 1, -1, -1):
                        merged_stats[0][category].pop(merge_index[i])

            # messages_per_day merge with mapping
            for date, user_msg in merged_stats[1].items():
                new_user_association = {}
                for user, value in user_msg.items():
                    if user in name:
                        if name[0] in new_user_association: # we keep the first pseudo of the list
                            # print(new_user_association[name[0]])
                            nb_you, nb_oth = new_user_association[name[0]]
                            new_user_association[name[0]] = (value[0] + nb_you, value[1] + nb_oth)
                        else:
                            new_user_association[name[0]] = (value[0], value[1])
                    else:
                        new_user_association[user] = value
                merged_stats[1][date] = new_user_association
        return merged_stats[:-1]