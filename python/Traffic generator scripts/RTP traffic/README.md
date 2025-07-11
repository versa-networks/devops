GStreamer Audio Traffic Simulator
This Python script simulates bi-directional audio traffic over a network using GStreamer. It is designed for testing, monitoring, or demonstrating real-time audio streaming between multiple IP addresses using UDP and the Opus codec.


Features
Audio Generation: Sends synthetic sine wave audio to random target IPs using GStreamer pipelines.
Audio Reception: Continuously listens for incoming Opus-encoded audio streams on UDP port 5000.
Asynchronous Execution: Uses `asyncio` and `threading` to manage concurrent audio streams.
Randomized Behavior: Introduces variability in call duration and timing to simulate realistic traffic.


Requirements
- Python 3.7+ (tested in Python version 3.10.12)
- GStreamer 1.0 with the following plugins:
  - `audiotestsrc`, `audioconvert`, `audioresample`
  - `opusenc`, `rtpopuspay`, `rtpopusdepay`, `opusdec`
  - `autoaudiosink`, `udpsink`, `udpsrc`
- Python GObject Introspection bindings:
  sudo apt install python3-gi gir1.2-gst-plugins-base-1.0 gir1.2-gstreamer-1.0
  

Installation
1. Install GStreamer and required plugins:
   sudo apt install gstreamer1.0-tools gstreamer1.0-plugins-base \
                    gstreamer1.0-plugins-good gstreamer1.0-plugins-bad \
                    gstreamer1.0-plugins-ugly gstreamer1.0-libav
2. Install Python dependencies:
   pip install pygobject



How It Works
- A list of target IPs (`10.0.4.1` to `10.0.4.10`) is defined.
- The `initiate_call()` function sends a sine wave audio stream to a randomly selected IP.
- The `receive_call()` function listens on UDP port 5000 and plays any incoming Opus audio.
- The `manage_calls()` coroutine launches 5 concurrent calls at random intervals.
- The `main()` function starts the receiver in a background thread and runs the call manager loop.


Usage
Run the script with:
python3 audio_traffic_simulator.py

Make sure the receiving host is reachable and listening on the correct port.


Notes
- This script is intended for lab environments or controlled networks.
- Ensure firewall rules allow UDP traffic on port 5000.
- You can modify the IP range or port as needed.