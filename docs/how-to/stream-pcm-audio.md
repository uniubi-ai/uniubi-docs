# PCM audio capture and playback

Media is enabled by default on x86_64, i386, and aarch64. SDK and device software versions must match.

| Mode | Capture / playback | Initialization |
|---|---|---|
| Local Orin | SHM audio/video capture, PCM RawBack playback, layout queries | `media.setup()` |
| Remote PC | Network PCM capture and RawBack playback | `media.setup(host)`, with the DV500 address |

Remote video subscriptions and layout queries return `kNotSupported`. Connect a High-level client before creating MediaBus. Remote audio uses the device service on TCP 1000; its audio service and channels must be configured and running. Local deployment uses `streamDefine` in `/etc/robot/sdk_config.json` and SHM, with RawBack channel `robotsdk.audioRawBack`.

## Run the complete example

Python remote playback with simultaneous capture from source 0:

```bash
sudo env LD_LIBRARY_PATH="$LD_LIBRARY_PATH" python3 examples/example_audio_rawback.py input.pcm \
  --host <DV500_IP> --device-id <ROBOT_SN> --interface <DDS_INTERFACE> \
  --volume 20 --capture-channel 0
```

Omit `--host` and `--device-id` locally. Omit `--capture-channel` for playback only. The C++ counterpart is `example_audio_rawback`; see `--help` for arguments. `example_audio` is the local capture example, and `example_media_frames` is the local video/layout example.

## Python API sequence

This fragment assumes a connected High-level client; the complete example also handles connection waits, error checks, file input, and cleanup.

```python
import time
import robot_motion_sdk as sdk

media = client.create_media_bus_client()
playback = None
try:
    if not media.setup(host):  # host="" locally
        raise RuntimeError(media.get_last_error())
    playback = media.create_audio_raw_back()
    if playback is None:
        raise RuntimeError(media.get_last_error())
    if not playback.setup():
        raise RuntimeError(playback.get_last_error())
    deadline = time.monotonic() + 5
    while not playback.ready():
        if time.monotonic() >= deadline:
            raise TimeoutError(playback.get_last_error())
        time.sleep(0.02)
    if not playback.set_volume(20):
        raise RuntimeError(playback.get_last_error())
    # Feed AudioFrame objects at the PCM sample rate; see the complete example.
finally:
    if playback is not None:
        playback.shutdown()
    media.shutdown()
```

C++ equivalents are `createMediaBusClient()` → `setup(host)` → `createAudioRawBack()` → `setup()` / `ready()` / `setVolume()` / `write()` / `shutdown()`. The playback interface is declared in `AudioRawBackStream.h`.

## PCM format and lifecycle

- Fixed 16 kHz, signed 16-bit little-endian, mono; no SDK resampling. Python `AudioFrameInfo` uses `sample_rate=16000`, `sample_format=16`, and `channel_count=1`.
- The example sends 1280 bytes every 40 ms, appends two silent frames, and waits for the tail. Successful writes do not prove speaker output; the protocol has no drain acknowledgement.
- `media.start_raw_audio_frame(source, callback)` starts capture with `(channel, AudioFrame)` callbacks. Remote source is the device audio-source index; select it from device configuration without querying remote layout.
- Successful `setup()` indicates initialization or connection startup. Wait for playback `ready()` and count actual capture frames to verify the data path.
- Repeated RawBack creation on the same media client shares the underlying stream. `reset()` clears queued playback. Close playback first, stop capture, shut down media, disconnect the client, then shut down the SDK service.
- Stop subscriptions and shut down on the application control thread, outside capture callbacks. Captured AudioFrame objects retain their audio data and metadata after callbacks return.

[Python example](https://github.com/uniubi-ai/uniubi_robot_sdk_py/blob/main/examples/example_audio_rawback.py) · [C++ example](https://github.com/uniubi-ai/uniubi_robot_sdk/blob/main/examples/example_audio_rawback.cpp)
