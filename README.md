# 🎥 Camera Access & Streaming Guide

This project provides tools and instructions for connecting, capturing snapshots, and streaming live video from the Eagle Cement Hikvision IP Camera (`192.168.100.134`).

---

## 📌 Camera & Network Information

| Parameter | Details |
|---|---|
| **IP Address** | `192.168.100.134` |
| **HTTP Web Port** | `80` / `443` |
| **RTSP Port** | `554` |
| **SDK / Control Port** | `8000` |
| **Username** | `admin` |
| **Password** | `REDACTED` |
| **Main Stream (HD 720p)** | `rtsp://admin:REDACTED@192.168.100.134:554/Streaming/Channels/101` |
| **Sub Stream (SD Fast)** | `rtsp://admin:REDACTED@192.168.100.134:554/Streaming/Channels/102` |

---

## 🛠️ Project Environment Setup & `venv` Management

### 1. How to Enter / Activate `venv`
Open your terminal and navigate to this project folder, then run:

```bash
cd /home/kaizen/Desktop/projects/geoplan/eagle-cement/camera-access
source venv/bin/activate
```
*(When active, your terminal prompt will show `(venv)` at the beginning.)*

### 2. How to Exit / Deactivate `venv`
To exit the virtual environment back to standard shell:

```bash
deactivate
```
*(The `(venv)` prefix will disappear from your prompt.)*

### 3. Verify Active Virtual Environment
```bash
which python
```
*(Output should point to `.../camera-access/venv/bin/python`)*

*(Optional) Install/restore dependencies on a new machine:*
```bash
pip install -r requirements.txt
```

---

## 🚀 Running the Python Script (`main.py`)

### Option A: Capture a Snapshot
To grab a frame and save it to `snapshots/snapshot.jpg`:
```bash
python main.py
```

### Option B: Open Live Video Stream
To open a live streaming window:
```bash
python main.py stream
```
*(Press **`q`** on your keyboard while focusing on the video window to stop streaming.)*

---

## 📺 Alternative Streaming Methods

### 1. Terminal Streaming with MPV (Zero Latency)
```bash
mpv --no-cache --untimed --no-demuxer-thread "rtsp://admin:REDACTED@192.168.100.134:554/Streaming/Channels/101"
```

### 2. Terminal Streaming with FFplay
```bash
ffplay -fflags nobuffer -flags low_delay -framedrop -rtsp_transport udp "rtsp://admin:REDACTED@192.168.100.134:554/Streaming/Channels/101"
```

### 3. Web Browser Control Panel
Open your browser and navigate to:
👉 **[http://192.168.100.134](http://192.168.100.134)**
- Enter `admin` / `REDACTED` to access live view and camera settings.

### 4. VLC Media Player
1. Open VLC Media Player.
2. Go to **Media** > **Open Network Stream** (`Ctrl + N`).
3. Enter URL: `rtsp://admin:REDACTED@192.168.100.134:554/Streaming/Channels/101`
4. Click **Play**.

---

## ⚡ Latency & Optimization Tips

- **Reduce Delay:** RTSP players default to 1–3s buffer delay. Use `Sub Stream (Channel 102)` or set `--no-cache` / `buffer_size=1` in OpenCV/MPV to reduce latency to <300ms.
- **Network Protocol:** If TCP stutters under poor network conditions, switch to UDP transport (`-rtsp_transport udp`).

---

## 📁 Project Directory Structure
```text
camera-access/
├── .env                 # Secret environment variables (RTSP URLs, credentials)
├── .gitignore           # Git ignore rules for venv, env, and output files
├── main.py              # Main Python script for snapshot & streaming
├── README.md            # Access guide & documentation (this file)
├── requirements.txt     # Python dependency manifest
├── snapshots/           # Directory where output frames are saved
└── venv/                # Isolated Python virtual environment
```
