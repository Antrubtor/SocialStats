import re
import sys
import json
import struct
import zipfile
from tqdm import tqdm
from pathlib import Path
from InquirerPy import inquirer
from collections import defaultdict
from datetime import datetime, timedelta

from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.chart import BarChart, PieChart, Reference, LineChart

def ask(question, options):
    if sys.stdin.isatty():
        return inquirer.select(
            message=question,
            choices=options
        ).execute()
    else:
        print(question)
        for i, option in enumerate(options, 1):
            print(f"{i}. {option}")
        while True:
            try:
                choice = int(input("Choose an option: "))
                if 1 <= choice <= len(options):
                    return options[choice - 1]
            except ValueError:
                print("Please enter a valid choice.")

def ask_number(question):
    if sys.stdin.isatty():
        return int(inquirer.number(
            message=question
        ).execute())
    else:
        print(question)
        while True:
            try:
                value = int(input("⮕ "))
                return value
            except ValueError:
                print("Please enter a valid number.")

def get_mp4_duration(path, file_path):
    """Directly reads the duration of an MP4 file by parsing the 'mvhd' box."""
    try:
        with zipfile.ZipFile(path, mode="r") as package:
            with package.open(file_path, "r") as f:
                data = f.read()
                mvhd_pos = data.find(b'mvhd')
                if mvhd_pos == -1:
                    print(f"Error: 'mvhd' not found in {file_path}")
                    return 0
                mvhd_offset = mvhd_pos + 4
                version = data[mvhd_offset]

                if version == 0:
                    time_scale, duration = struct.unpack(">II", data[mvhd_offset + 12: mvhd_offset + 20])
                elif version == 1:
                    time_scale, duration = struct.unpack(">IQ", data[mvhd_offset + 20: mvhd_offset + 32])
                else:
                    print(f"Error: Unknown version of mvhd for {file_path}")
                    return 0
                return duration / time_scale if time_scale > 0 else 0
    except Exception as e:
        print(f"Error with {file_path} : {e}")
        return 0


def generate_excel(per_contact_stats, messages_per_day, hour_distribution, excel_name="analysis.xlsx"):
    wb = Workbook()

    # 1. GLOBAL SHEET
    ws1 = wb.active
    ws1.title = "Global"

    keys = list(per_contact_stats.keys())
    length = len(per_contact_stats[keys[0]])

    # Write headers
    for col, key in enumerate(keys, 1):
        ws1.cell(row=1, column=col, value=key)

    # Write data
    for row in range(length):
        for col, key in enumerate(keys, 1):
            ws1.cell(row=row + 2, column=col, value=per_contact_stats[key][row])

    # Write totals (row = length + 3)
    total_row = length + 3
    ws1.cell(row=total_row, column=1, value="TOTAL")

    for col, key in enumerate(keys[1:], 2):
        col_letter = get_column_letter(col)
        if "delay" in key.lower():
            ws1.cell(row=total_row, column=col,
                     value=f"=AVERAGE({col_letter}2:{col_letter}{length + 1})")
        else:
            ws1.cell(row=total_row, column=col,
                     value=f"=SUM({col_letter}2:{col_letter}{length + 1})")

    # Add bar chart for messages by hour
    ws1.cell(row=1, column=len(keys) + 2, value="Hour")
    ws1.cell(row=1, column=len(keys) + 3, value="Nb msg")
    for i in range(24):
        ws1.cell(row=i + 2, column=len(keys) + 2, value=f"{i}h")
        ws1.cell(row=i + 2, column=len(keys) + 3, value=hour_distribution[i])
    bar = BarChart()
    bar.title = "Message Activity by Hour"
    bar.x_axis.title = "Hour"
    bar.y_axis.title = "Messages Sent"

    data = Reference(ws1, min_col=len(keys) + 3, max_col=len(keys) + 3,
                          min_row=2, max_row=25)
    bar.add_data(data)
    ws1.add_chart(bar, f"{get_column_letter(len(keys) + 5)}2")

    # Add pie chart for message distribution
    pie = PieChart()
    pie.title = "Message Distribution by Contact"
    labels = Reference(ws1, min_col=1, min_row=2, max_row=length + 1)
    data = Reference(ws1, min_col=keys.index("Messages") + 1,
                     min_row=1, max_row=length + 1)
    pie.add_data(data, titles_from_data=True)
    pie.set_categories(labels)
    ws1.add_chart(pie, f"{get_column_letter(len(keys) + 5)}20")

    # 2. MESSAGES PER DAY SHEET
    ws2 = wb.create_sheet("Messages per day")

    all_dates = sorted(set(datetime.strptime(date, "%m/%d/%Y")
                           for date in messages_per_day.keys()))
    if not all_dates:
        all_dates = []

    # Build header
    contacts = sorted({c for daily in messages_per_day.values() for c in daily})
    ws2.cell(row=1, column=1, value="Date")
    for col, contact in enumerate(contacts, 2):
        ws2.cell(row=1, column=col, value=contact)
    ws2.cell(row=1, column=len(contacts) + 2, value="TOTAL")

    # Fill data
    for row, dt in enumerate(all_dates, 2):
        date_str = dt.strftime("%m/%d/%Y")
        ws2.cell(row=row, column=1, value=date_str)
        total = 0
        for col, contact in enumerate(contacts, 2):
            msg_count = sum(messages_per_day.get(date_str, {}).get(contact, (0, 0)))
            ws2.cell(row=row, column=col, value=msg_count)
            total += msg_count
        ws2.cell(row=row, column=len(contacts) + 2, value=total)

    # Graphs
    chart = BarChart()
    chart.title = "Messages per Day"
    chart.x_axis.title = "Date"
    chart.y_axis.title = "Messages"

    data = Reference(ws2, min_col=len(contacts) + 2, min_row=1, max_row=len(all_dates) + 1)
    cats = Reference(ws2, min_col=1, min_row=2, max_row=len(all_dates) + 1)
    chart.add_data(data, titles_from_data=True)
    chart.set_categories(cats)
    ws2.add_chart(chart, f"{get_column_letter(len(contacts) + 4)}2")

    # Weekly and monthly charts
    weekly_chart = BarChart()
    weekly_chart.title = "Messages per Week"
    weekly_data = {}
    for dt in all_dates:
        week = dt.strftime("%Y-W%U")
        weekly_data[week] = weekly_data.get(week, 0) + sum(
            messages_per_day.get(dt.strftime("%m/%d/%Y"), {}).get(c, (0, 0))[0] +
            messages_per_day.get(dt.strftime("%m/%d/%Y"), {}).get(c, (0, 0))[1]
            for c in contacts
        )

    start_row = len(all_dates) + 5
    for i, (week, count) in enumerate(sorted(weekly_data.items()), start=start_row):
        ws2.cell(row=i, column=1, value=week)
        ws2.cell(row=i, column=2, value=count)
    weekly_ref = Reference(ws2, min_col=2, min_row=start_row, max_row=start_row + len(weekly_data) - 1)
    weekly_cats = Reference(ws2, min_col=1, min_row=start_row, max_row=start_row + len(weekly_data) - 1)
    weekly_chart.add_data(weekly_ref)
    weekly_chart.set_categories(weekly_cats)
    ws2.add_chart(weekly_chart, f"D{start_row}")

    monthly_chart = BarChart()
    monthly_chart.title = "Messages per Month"
    monthly_data = {}
    for dt in all_dates:
        month = dt.strftime("%Y-%m")
        monthly_data[month] = monthly_data.get(month, 0) + sum(
            messages_per_day.get(dt.strftime("%m/%d/%Y"), {}).get(c, (0, 0))[0] +
            messages_per_day.get(dt.strftime("%m/%d/%Y"), {}).get(c, (0, 0))[1]
            for c in contacts
        )

    start_row = start_row + len(weekly_data) + 3
    for i, (month, count) in enumerate(sorted(monthly_data.items()), start=start_row):
        ws2.cell(row=i, column=1, value=month)
        ws2.cell(row=i, column=2, value=count)
    monthly_ref = Reference(ws2, min_col=2, min_row=start_row, max_row=start_row + len(monthly_data) - 1)
    monthly_cats = Reference(ws2, min_col=1, min_row=start_row, max_row=start_row + len(monthly_data) - 1)
    monthly_chart.add_data(monthly_ref)
    monthly_chart.set_categories(monthly_cats)
    ws2.add_chart(monthly_chart, f"D{start_row}")

    # 3. CUMULATIVE SHEET
    ws3 = wb.create_sheet("Cumulative per day")

    ws3.cell(row=1, column=1, value="Date")
    for col, contact in enumerate(contacts, 2):
        ws3.cell(row=1, column=col, value=contact)
    ws3.cell(row=1, column=len(contacts) + 2, value="TOTAL")

    cumulative = [0] * len(contacts)
    for row, dt in enumerate(all_dates, 2):
        date_str = dt.strftime("%m/%d/%Y")
        ws3.cell(row=row, column=1, value=date_str)
        total = 0
        for col, contact in enumerate(contacts, 2):
            msg_count = sum(messages_per_day.get(date_str, {}).get(contact, (0, 0)))
            cumulative[col - 2] += msg_count
            ws3.cell(row=row, column=col, value=cumulative[col - 2])
            total += cumulative[col - 2]
        ws3.cell(row=row, column=len(contacts) + 2, value=total)

    line_chart = LineChart()
    line_chart.title = "Cumulative Messages per Day"
    data = Reference(ws3, min_col=2, max_col=len(contacts) + 1, min_row=1, max_row=len(all_dates) + 1)
    cats = Reference(ws3, min_col=1, min_row=2, max_row=len(all_dates) + 1)
    line_chart.add_data(data, titles_from_data=True)
    line_chart.set_categories(cats)
    ws3.add_chart(line_chart, f"{get_column_letter(len(contacts) + 4)}2")

    wb.save(excel_name)


class Action:
    def __init__(self, label, func):
        self.label = label
        self.func = func

    def __str__(self):
        return self.label

    def execute(self):
        self.func()