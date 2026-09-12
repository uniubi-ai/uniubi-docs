# Use Voice, Lights, and Media Frames

**English** | [简体中文](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/how-to/use-media-and-device-io.zh-CN.md)

Voice playback, microphone audio, camera video, and camera lights are separate capabilities. Distinguish control-plane operations from media data first.

## Support matrix

| Capability | High-level | Low-level | Control requirement |
|---|---|---|---|
| Voice playback, pause, and file management | Supported | Not supported | High-level `kControlled` |
| Camera light | Supported | Not supported | High-level `kControlled` |
| Raw microphone audio | MediaBus | MediaBus | Independent of motion control |
| Raw / encoded camera video | MediaBus | MediaBus | Independent of motion control |

> MediaBus is enabled by default on x86_64, i386, and aarch64. Local Orin deployment supports video, audio, and layout queries; remote deployment supports PCM capture and RawBack playback via `media.setup(host)`. Remote video subscriptions and layout queries return `kNotSupported`. SDK headers, runtime libraries, Python extensions, and device software must use matching versions.

## High-level: play voice audio

Voice playback and file management are High-level control-plane operations and require `kControlled`.

```python
client.start_audio_play({
    "list": [{"id": "1"}],
    "volume": 50,
    "repeat": 1,
})

detail = client.query_audio_play_detail()
client.pause_audio_play()
client.stop_audio_play()
```

Use `add_audio_file()` / `delete_audio_file()` for custom files. See the High-level API for file IDs, URL/local-file modes, and format restrictions. Voice playback is not a microphone-capture interface.

## Custom audio: upload by URL and play

The playback service runs on **DV500**, while the SDK normally runs on **Orin or a PC**. Use `url` in these deployments. An Orin path is not a DV500-local path. `file` applies only when the file is already accessible to the playback service on DV500.

### 1. Prepare the file and HTTP URL

Place `turn_left_90.wav` in a dedicated directory on Orin and start an HTTP server there:

```bash
cd ~/audio
python3 -m http.server 8000 --bind 172.29.110.2
```

This assumes Orin uses `172.29.110.2` on `eth0.100`; check with `ip -4 addr show eth0.100`. The URL is `http://172.29.110.2:8000/turn_left_90.wav`. Keep this terminal running until import completes.

You can also serve a dedicated directory on a PC with `python3 -m http.server 8000`. Use a **PC IP reachable from DV500** and check routing and firewall access. Do not use `localhost` or pass the PC file path as `file`.

The hardware test used a 16 kHz, mono, 16-bit PCM WAV: 58,446 bytes, 1.824 seconds. Confirm other encodings and size limits for the target model.

### 2. Add and play from Orin

This example assumes the Python SDK is installed and `import robot_motion_sdk` works. Save it as `play_custom_audio.py` and run it in another terminal:

```bash
sudo python3 -u play_custom_audio.py
```

For a custom SDK location, use `sudo env PYTHONPATH=<SDK-package-parent> python3 -u play_custom_audio.py`. A root-owned SDK lock file requires sudo; the regular user's Python environment alone may not be sufficient.

```python
import time
import robot_motion_sdk as sdk

AUDIO_ID = "custom_turn_left_90"
URL = "http://172.29.110.2:8000/turn_left_90.wav"
client = None

def require(ok, operation):
    if not ok:
        raise RuntimeError(f"{operation}: {client.get_last_error()}")

def wait_until(check, seconds, message):
    deadline = time.monotonic() + seconds
    while not check():
        if time.monotonic() >= deadline:
            raise RuntimeError(message)
        time.sleep(0.2)

def audio_ready():
    result = client.query_audio_play_list({"type": "customVoice"})
    return result is not None and any(
        item["id"] == AUDIO_ID for item in result.get("customVoice", [])
    )

sdk.service.set_network_interface("eth0.100")
try:
    if not sdk.service.initial(None, "custom-audio-example"):
        raise RuntimeError("SDK initialization failed")
    if sdk.service.is_multi_device():
        raise RuntimeError("This example requires on-board Orin deployment")
    client = sdk.MotionHighLevelClient()
    require(client.connect(lease_ms=60000), "connect")
    wait_until(lambda: client.query_audio_play_detail() is not None,
               10, "Audio RPC unavailable")
    detail = client.query_audio_play_detail()
    if detail is None or detail.get("playing"):
        raise RuntimeError("Cannot start: status unavailable or audio already playing")
    require(client.start_control(timeout_ms=10000), "start_control")
    wait_until(lambda: client.get_state() == sdk.HighLevelState.kControlled,
               12, "Control acquisition timed out")
    if not audio_ready():
        require(client.add_audio_file({
            "id": AUDIO_ID,
            "name": "turn_left_90.wav",
            "url": URL,
            "describe": "Custom voice prompt",
        }, timeout_ms=30000), "add_audio_file")
        wait_until(audio_ready, 30, "Audio download/import did not finish")
    require(client.start_audio_play({
        "list": [{"id": AUDIO_ID}], "volume": 50, "repeat": 1,
    }), "start_audio_play")
    # Observe this short clip; retain control until playback has stopped.
    deadline = time.monotonic() + 15
    while True:
        detail = client.query_audio_play_detail()
        print(detail, flush=True)
        if detail is not None and detail.get("currentId") == AUDIO_ID:
            if not detail.get("playing"):
                break
        if time.monotonic() >= deadline:
            client.stop_audio_play()
            raise RuntimeError("Playback observation timed out")
        time.sleep(0.2)
finally:
    if client is not None:
        try:
            if client.get_state() == sdk.HighLevelState.kControlled:
                client.release_control()
        finally:
            client.disconnect()
    sdk.service.shutdown()
```

### 3. Check results and replay

- `start_control()` may return before ownership is acquired; wait for `kControlled`.
- **Success from `add_audio_file()` does not guarantee that download/import has completed.** Poll `query_audio_play_list({"type":"customVoice"})` until the target ID appears before playing. Immediate playback may be rejected.
- The HTTP log should show a DV500 `GET` with status `200`. Once imported, stop the HTTP server; playback uses the stored ID and needs no further download.
- Running the example again reuses the ID without overwriting its content. Use a unique new ID for a different file.
- `playing: true → false` indicates the device reported playback and then completion. Playback events are another option. The hardware test received `started → stopped`; audible output still needs an on-site check.

The script plays once at volume 50, releases control, and sends no motion actions. Its playback observation limit is 15 seconds; increase it for longer audio. If the ID does not appear within 30 seconds, inspect HTTP logs, DV500 connectivity, format, and storage capacity before attempting playback.

## High-level: control the camera light

```python
current = client.get_camera_light_brightness()
if not client.set_camera_light_brightness(50):
    raise RuntimeError(client.get_last_error())
```

Brightness ranges from 0 to 100. Follow the High-level API control requirements for both reading and writing.

## High-level / Low-level: subscribe to media frames

Either motion client can create the same `MediaBusClient`. Media subscription does not require `start_control()` or `set_motion_enable()`.

```python
if not sdk.MEDIA_ENABLED:
    raise RuntimeError("MediaBus is unavailable in this SDK build")

media = client.create_media_bus_client()  # High-level or Low-level client
if not media.setup():
    raise RuntimeError(media.get_last_error())

def on_video(channel, frame):
    print("raw video", channel, frame.size())

def on_encoded(channel, frame):
    print("encoded video", channel, frame.size())

def on_audio(channel, frame):
    print("microphone", channel, frame.size())

media.start_raw_video_frame(0, on_video)
media.start_encoded_video_frame(0, on_encoded)
media.start_raw_audio_frame(0, on_audio)
```

On shutdown, call the matching `stop_*_frame()` methods before `media.shutdown()`. Copy frame data inside the callback if it must outlive the callback; do not retain an underlying view indefinitely.
