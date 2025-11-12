# 📊 SocialStats

**SocialStats** analyzes your personal data from multiple social networks and turns it into **clean Excel dashboards**: response delays, messaging activity over time, voice call durations, voice message time, and more.
It also supports **exporting media (Instagram & Snapchat)**, **standardized JSON exports**, **regex-based search**, and **location mapping for Snapchat**.

---

## 🧩 Features

* 📅 See how many messages you sent and received over time  
* ⏱️ Average response delays (you vs. contact) — **Instagram, Snapchat, WhatsApp**
* 🕐 View your activity by **hour**, **day**, **week**, **month**, or **year**  
* 📞 Get your total voice call time (Discord only)  
* 🎙️ See your total voice message time (Instagram, Snapchat)  
* 📊 Compare how much you interact with different people  
* 🔗 **Cross-network merge** into a single Excel (Discord/Instagram/Snapchat/WhatsApp)
* 🖼️ **Media export** (Instagram & Snapchat) — EXIF/metadata timestamps are normalized so **Android/iOS galleries sort them correctly in time**
* 🧾 **JSON export** of all messages
* 🔎 **Regex search** across all messages of a given social network
* 🗺️ **Snapchat map export (HTML)** with all recorded location points

> [!TIP]
> Don’t forget to check the **"Global"** sheet in the Excel file — it contains more specific and aggregated information.

> [!WARNING]
> Too many contacts = unreadable Excel.
> The program will ask you to define a **minimum number of messages per conversation** so only relevant ones are included.

---

## 🛠️ Requirements

- [Python 3.10+](https://www.python.org/downloads/)
- [pip](https://pip.pypa.io/en/stable/installation/)
- [Excel](https://www.microsoft.com/en-us/microsoft-365/excel) or [LibreOffice](https://www.libreoffice.org/)

---

## 🚀 Setup & Run

### 🔵 On Windows

```
python setup.py
.venv\Scripts\activate
python main.py
```

### 🟢 On Linux / macOS

```
python3 setup.py
source .venv/bin/activate
python3 main.py
```

> [!WARNING]
> If you encounter any bug, please open an **issue** and explain the problem in detail — so I can fix it quickly.

---

## 🗂️ How to download your data

### 🟣 Discord *(can take up to 30 days)*

1. Go to ⚙️ Settings > **Data & Privacy**
2. Click **Request all of my data**
3. Select **everything**

### 🟠 Instagram *(takes less than 1 hour)*

1. Go to **Settings > Account Center**
2. Choose **Your information and permissions**
3. Click **Download your information**
4. Options:

   * Date range: **All time**
   * Format: **JSON**
   * Media quality: **High**

### 🟡 Snapchat *(can take up to 1 day)*

1. Go to **Settings > My Data**
2. Select everything, especially **Export JSON files**, if the zip file doesn't contain everything, select at least:
   * Export JSON Files
   * User Information
   * Chat History
   * Ranking And Location
   * Export Chat Media
3. Choose **All time** as period

### 🟢 WhatsApp *(instant)*

1. Open a conversation
2. Tap `⋮ > More > Export Chat`
3. Choose **Without media**

---



## 📷 Example outputs

<table>
  <tr>
    <td><img src=".ressources/cumul_per_day.png" width="400"/></td>
    <td><img src=".ressources/answer_delay.png" width="400"/></td>
  </tr>
  <tr>
    <td><img src=".ressources/msg_per_hour.png" width="400"/></td>
    <td><img src=".ressources/proportion_contact.png" width="400"/></td>
  </tr>
</table>

---

## 🧪 JSON Export

Standard export of all your conversations in a **clean and unified JSON format**.
Useful for re-importing, cross-platform comparisons, or external analysis.

---

## 🖼️ Media Export

Automatically export all **images** and **videos** from **Instagram** and **Snapchat** into a single organized folder.
Files are renamed with date + sender, and their metadata is updated so they integrate seamlessly into Android and iOS galleries.

---

## 🔍 Regex Search

Run **regex-based** queries across all messages of a given platform to quickly find patterns (keywords, URLs, mentions, etc.).
Great for investigations and advanced filtering.

---

## 🗺️ Snapchat Location Map (HTML)

Generate an **interactive HTML map** of all geolocations saved by Snapchat.
Open it in your browser to explore your activity on a map.

---

## 📄 License

This project is licensed under the **MIT License**.
Forks and reuse are welcome — please **credit [Antrubtor](https://github.com/Antrubtor)**.

---