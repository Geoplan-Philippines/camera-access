# 🎥 Eagle Cement CCTV Live Streaming Architecture & Integration Plan

> **Document Status**: Draft / Architecture Review  
> **Scope**: **Live Stream Only** *(Snapshot feature is intentionally deferred for future research & implementation)*  
> **Target Camera**: Hikvision IP Camera (`192.168.100.134`)  
> **Date**: August 2026  

---

## 📌 1. Executive Summary

This document defines the architectural blueprint for integrating live CCTV camera feeds into the **Eagle Cement** web application. 

Currently, the camera access scripts in [`camera-access/main.py`](file:///home/kaizen/Desktop/projects/geoplan/eagle-cement/camera-access/main.py) communicate directly with the Hikvision IP camera using OpenCV (`cv2.VideoCapture`). However, web browsers (Chrome, Edge, Firefox, Safari) cannot play raw RTSP (`rtsp://`) streams directly.

To achieve **sub-second (< 300ms) latency** live streaming inside the **Angular frontend** without exposing camera credentials or causing high CPU consumption, we propose deploying **`go2rtc`** as an RTSP-to-WebRTC (WHEP) gateway alongside PostgreSQL in [`docker-compose.yml`](file:///home/kaizen/Desktop/projects/geoplan/eagle-cement/docker-compose.yml).

---

## ⚡ 2. Current Camera Information

As documented in [`camera-access/README.md`](file:///home/kaizen/Desktop/projects/geoplan/eagle-cement/camera-access/README.md):

| Property | Value |
| :--- | :--- |
| **Camera IP (Default)** | `192.168.100.134` |
| **HTTP Port** | `80` / `443` |
| **RTSP Port** | `554` |
| **Main Stream (HD 720p/1080p)** | `rtsp://admin:REDACTED@192.168.100.134:554/Streaming/Channels/101` |
| **Sub Stream (SD Fast)** | `rtsp://admin:REDACTED@192.168.100.134:554/Streaming/Channels/102` |

> [!WARNING]
> **Dynamic / Changing IP Address Handling**:
> The camera IP address (`192.168.100.134`) may change in the future due to DHCP re-assignment or network infrastructure changes.
> * **Updating `go2rtc`**: Modify [`camera-access/go2rtc.yaml`](file:///home/kaizen/Desktop/projects/geoplan/eagle-cement/camera-access/go2rtc.yaml) with the new RTSP IP or hostname and restart the container (`docker compose restart go2rtc`).
> * **Updating Python Scripts**: Update `RTSP_URL` in [`camera-access/.env`](file:///home/kaizen/Desktop/projects/geoplan/eagle-cement/camera-access/.env).
> * **Recommended Solution**: Configure a **Static IP Reservation** on the local router/DHCP server or use a local domain name (e.g. `cctv-gate.local`) to avoid manual IP updates.

---

## 🏛️ 3. System Architecture & Topology

### 3.1. System Data Flow Diagram

```mermaid
flowchart TD
    subgraph IP Camera Network
        CAM["Hikvision IP Camera<br/>192.168.100.134:554<br/>(RTSP H.264 Stream)"]
    end

    subgraph Docker Infrastructure
        GO2RTC["go2rtc Proxy Container<br/>• Listens on RTSP:554<br/>• Serves WHEP (WebRTC):1984<br/>• Zero re-encoding passthrough"]
        POSTGRES["PostgreSQL DB<br/>(Port 5435)"]
    end

    subgraph Eagle Cement Web Application
        BACKEND["NestJS Backend API<br/>• User Authentication (JWT)<br/>• Stream Access Authorization<br/>• WHEP Signaling Proxy"]
        FRONTEND["Angular Frontend Application<br/>• Live CCTV Player Component<br/>• HTML5 Video Tag with WebRTC<br/>• Sub/Main Stream Toggle"]
    end

    CAM -->|1. RTSP Stream Channel 101/102| GO2RTC
    FRONTEND -->|2. HTTP POST /api/v1/cctv/whep (SDP Offer)| BACKEND
    BACKEND -->|3. Forward SDP Offer to WHEP Endpoint| GO2RTC
    GO2RTC -->|4. Return SDP Answer| BACKEND
    BACKEND -->|5. Return SDP Answer| FRONTEND
    FRONTEND <-->|6. WebRTC Direct Peer Connection (P2P / UDP)| GO2RTC
```

---

## 🔄 4. WebRTC WHEP Signaling Sequence

```mermaid
sequenceDiagram
    autonumber
    actor User as User (Angular UI)
    participant Front as Angular Frontend
    participant Back as NestJS Backend
    participant Gateway as go2rtc Container
    participant Cam as Hikvision Camera

    Note over Gateway,Cam: Background: go2rtc maintains active RTSP session
    Gateway->>Cam: RTSP DESCRIBE / SETUP / PLAY
    Cam-->>Gateway: H.264 Video Packets

    User->>Front: Open CCTV Dashboard / Monitoring Page
    Front->>Back: GET /api/v1/cctv/stream-info (Bearer JWT)
    Back-->>Front: 200 OK (Stream Status, WHEP URL, Channel Info)

    Front->>Front: Initialize RTCPeerConnection & Create SDP Offer
    Front->>Back: POST /api/v1/cctv/whep (Body: SDP Offer)
    Back->>Gateway: POST http://go2rtc:1984/api/ws?src=eagle_cam_sub (SDP Offer)
    Gateway-->>Back: 201 Created (SDP Answer)
    Back-->>Front: 200 OK (SDP Answer)

    Front->>Gateway: Establish WebRTC ICE Candidate & Media Flow
    Gateway-->>Front: Ultra-low Latency H.264 Video Stream (<300ms)
```

---

## 🛠️ 5. Technology Stack & Protocol Comparison

### 5.1. Protocol Selection Matrix

| Protocol | Latency | Browser Support | Server CPU Impact | Suitability |
| :--- | :--- | :--- | :--- | :--- |
| **WebRTC (WHEP)** | **< 300ms** | Native (Chrome, Safari, Firefox, Edge) | **Minimal** (Passthrough H.264) | **Selected Primary** |
| **WebSocket + MSE** | 500ms – 1s | Native via MediaSource API | Low | Backup / Fallback |
| **HLS (HTTP Live)** | 6s – 15s | Native Safari / HLS.js | Low | ❌ Too slow for live security |

### 5.2. Component Responsibilities

1. **`go2rtc` Docker Container**:
   * Bridges RTSP from `192.168.100.134` to WebRTC (WHEP HTTP endpoint).
   * Runs natively on Linux host without heavy transcoding overhead.
   * Handles client multiplexing so the camera only services a single RTSP connection regardless of active web viewers.

2. **NestJS Backend Gateway**:
   * Enforces JWT authentication so unauthorized users cannot access the stream.
   * Proxies WHEP SDP signaling to hide local camera IP addresses and RTSP credentials (`admin:REDACTED`) from public client inspect tools.

3. **Angular Frontend Video Player**:
   * Uses HTML5 standard `<video autoplay muted playsinline>` tag.
   * Leverages browser native `RTCPeerConnection` for hardware-accelerated rendering.
   * Includes connection health monitoring with automatic reconnect logic.

---

## 🔐 6. Security & Performance Guidelines

1. **Credential Protection**:
   * Camera credentials (`RTSP_URL` and passwords) MUST remain exclusively inside backend `.env` variables and `go2rtc.yaml` config.
   * Clients only receive secure ephemeral signaling responses.

2. **Stream Optimization (Sub-stream vs Main-stream)**:
   * **Sub Stream (`Channel 102`)**: Default for multi-camera grid views or dashboard preview widgets (low network overhead, lower resolution).
   * **Main Stream (`Channel 101`)**: Activated on-demand when the user clicks "Full Screen" or "HD Mode".

3. **Hikvision Encoding Configuration**:
   * Video Codec: **H.264** (Baseline or Main Profile).
   * Frame Rate: **15 - 25 FPS**.
   * Keyframe Interval (GOP): **1 or 2 seconds** (ensures fast initial playback hookup).
   * B-Frames: **Disabled (0)** to prevent WebRTC decoding latency jitter.

---

## 📅 7. Implementation Roadmap (Stream Only)

```mermaid
gantt
    title CCTV Live Stream Integration Phases
    dateFormat  YYYY-MM-DD
    section Phase 1: Gateway
    Configure go2rtc docker-compose :active, p1, 2026-08-10, 2d
    Verify camera connection via WHEP :p2, after p1, 1d
    section Phase 2: Backend
    Implement NestJS CCTV Controller & Service :p3, after p2, 2d
    Implement WHEP Proxy & Auth Validation :p4, after p3, 2d
    section Phase 3: Frontend
    Build Angular CCTV Player Component :p5, after p4, 3d
    Add Connection State & Channel Switcher :p6, after p5, 2d
    section Phase 4: QA
    Network Latency & Failover Testing :p7, after p6, 2d
```

> ⚠️ *Note: Snapshot feature design and implementation will be scheduled in a separate phase following live stream stabilization.*
