# PCM audio capture and playback

For generic ARM64 external hosts, select `aarch64_host`: build with `-DPLATFORM=aarch64_host` (Python: `-Ccmake.define.PLATFORM=aarch64_host`) and load `lib/aarch64_host/`. Media support matches x86 remote mode: remote audio only. Orin local video/layout examples still use `aarch64`.

Media is enabled by default on x86_64, i386, and aarch64. SDK and device software versions must match.

| Mode | Capture / playback | Initialization |
|---|---|---|
| Local Orin | SHM audio/video capture, PCM RawBack playback, layout queries | `media.setup()` |
| Remote PC | Network PCM capture and RawBack playback | `media.setup(host)`, with the DV500 address |

Remote video subscriptions and layout queries return `kNotSupported`. Connect a High-level client before creating MediaBus. For remote audio, ensure the host can reach the robot and that its audio service and capture channels are enabled. Before local capture, check that the channels in `/etc/robot/sdk_config.json` match the device; see [local capture configuration](https://github.com/uniubi-ai/uniubi_robot_sdk/blob/main/docs/media-capture.md).

## Run the complete example

Python remote playback with simultaneous capture from source 0:

```bash
sudo env LD_LIBRARY_PATH="$LD_LIBRARY_PATH" python3 examples/example_audio_rawback.py input.pcm \
  --host <DV500_IP> --device-id <ROBOT_SN> --interface <DDS_INTERFACE> \
  --volume 20 --capture-channel 0
```

Omit `--host` and `--device-id` locally. Omit `--capture-channel` for playback only. The C++ counterpart is `example_audio_rawback`; see `--help` for arguments. `example_audio` is the local capture example, and `example_media_frames` is the local video/layout example.

## Capture four sources concurrently

Use the Python SDK [example_audio_capture.py](https://github.com/uniubi-ai/uniubi_robot_sdk_py/blob/main/examples/example_audio_capture.py). It keeps sources **0, 1, 2, and 3** subscribed on one MediaBus client and saves each source independently. It captures audio without acquiring motion control or playing sound. All four sources must be configured and enabled on the device; source indices do not represent four channels interleaved in one audio frame.

Install the platform-matched C++ runtime and Python SDK using the [build guide](https://github.com/uniubi-ai/uniubi-docs/blob/main/docs/BUILD.md). Run these commands from the Python SDK repository root, with `UNIUBI_SDK_ROOT` pointing to the matching C++ SDK repository. Choose a new output directory for every run; existing directories are never overwritten.

### Brain local mode (`aarch64`)

Use the board system Python and ensure its local audio channels are configured:

```bash
export UNIUBI_SDK_ROOT=/path/to/uniubi_robot_sdk
sudo env LD_LIBRARY_PATH="$UNIUBI_SDK_ROOT/lib/aarch64:${LD_LIBRARY_PATH:-}" \
  python3 examples/example_audio_capture.py \
  --seconds 20 --output /tmp/pcm4-brain-01
```

### x86 host (`x86_64`)

Replace `ROBOT_IP`, `ROBOT_SN`, and `HOST_INTERFACE` with the robot address, device SN, and host network interface that reaches the robot. External hosts require all three arguments:

```bash
export UNIUBI_SDK_ROOT=/path/to/uniubi_robot_sdk
LD_LIBRARY_PATH="$UNIUBI_SDK_ROOT/lib/x86_64:${LD_LIBRARY_PATH:-}" \
  python3 examples/example_audio_capture.py \
  --host ROBOT_IP --device-id ROBOT_SN --interface HOST_INTERFACE \
  --seconds 20 --output /tmp/pcm4-x86-01
```

### ARM64 host (`aarch64_host`)

Install the Python SDK with `-Ccmake.define.PLATFORM=aarch64_host` and use the matching host runtime libraries. Replace the arguments as described for x86 hosts:

```bash
export UNIUBI_SDK_ROOT=/path/to/uniubi_robot_sdk
LD_LIBRARY_PATH="$UNIUBI_SDK_ROOT/lib/aarch64_host:${LD_LIBRARY_PATH:-}" \
  python3 examples/example_audio_capture.py \
  --host ROBOT_IP --device-id ROBOT_SN --interface HOST_INTERFACE \
  --seconds 20 --output /tmp/pcm4-arm64-host-01
```

### Output, shutdown, and acceptance

The output directory contains `channel0.pcm` through `channel3.pcm` and per-source statistics in `summary.json`.

- **Format:** each file contains headerless 16 kHz, signed 16-bit little-endian, mono PCM. Sources remain separate, without interleaving or mixing.
- **Duration:** `--seconds` specifies the target sample duration per source, from 1 to 60 seconds, default 20. Each file must contain `seconds × 16000 × 2` bytes: **640000 bytes** for 20 seconds. Callbacks stop accumulating at this limit. After all subscriptions start, the example waits at most the requested duration plus 5 seconds.
- **Shutdown:** capture stops automatically when every source is complete, or earlier on Ctrl+C. The main thread stops every successfully started subscription, shuts down media, disconnects the client, and shuts down the SDK before saving each source. Partial startup failure also cleans up earlier subscriptions. Interruptions and errors produce a failed summary.
- **Pass criteria:** exit code 0, `result: PASS` in `summary.json`, nonzero frames and the exact target byte count for every source, zero `format_errors` and `timestamp_errors`, and an empty `errors` list. Initialization, subscription, cleanup, or file-write failures cannot pass; partial files alone do not establish success.
- **Limits:** timestamps must increase strictly within each source. Silence is valid PCM. Full files do not prove uninterrupted capture, a common start time, or exact synchronization across sources; those require separate validation.

Inspect file sizes and the summary, then optionally listen to individual sources:

```bash
wc -c /tmp/pcm4-brain-01/channel*.pcm
cat /tmp/pcm4-brain-01/summary.json
aplay -t raw -f S16_LE -r 16000 -c 1 /tmp/pcm4-brain-01/channel0.pcm
```

Replace the directory with your output path. These are execution and acceptance instructions, not a claim that four-source capture has been validated on all three physical platforms.

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
