import sounddevice as sd

print("=== Host APIs ===")
for i, h in enumerate(sd.query_hostapis()):
    print(f"  [{i}] {h['name']}")

print("\n=== Dispositivos de entrada ===")
for i, d in enumerate(sd.query_devices()):
    if d["max_input_channels"] > 0:
        ha = sd.query_hostapis(d["hostapi"])
        print(f"  [{i}] {d['name']} | {ha['name']} | sr={d['default_samplerate']} | ch={d['max_input_channels']}")

print("\n=== Test abrir WASAPI ===")
hostapis = sd.query_hostapis()
wasapi_idx = None
for i, h in enumerate(hostapis):
    if "WASAPI" in h["name"]:
        wasapi_idx = i
        break

candidatos = [0, 1, 5, 6, 17, 18, 23, 24]
for i in candidatos:
    d = sd.query_devices(i)
    ha = sd.query_hostapis(d["hostapi"])
    sr = int(d["default_samplerate"])
    ch = min(2, d["max_input_channels"])
    try:
        with sd.InputStream(device=i, samplerate=sr, channels=ch, dtype="float32", blocksize=int(0.5*sr)):
            print(f"  OK: [{i}] {d['name']} | {ha['name']} | sr={sr} ch={ch}")
    except Exception as e:
        print(f"  FAIL [{i}] sr={sr} ch={ch}: {e}")

# Try default device with no explicit device
print("\n=== Test default (sin device) ===")
for sr in [44100, 48000, 16000]:
    try:
        with sd.InputStream(samplerate=sr, channels=1, dtype="float32", blocksize=int(0.5*sr)):
            print(f"  OK: default sr={sr} ch=1")
            break
    except Exception as e:
        print(f"  FAIL default sr={sr}: {e}")

# Try PyAudio as alternative
print("\n=== Test PyAudio ===")
try:
    import pyaudio
    p = pyaudio.PyAudio()
    info = p.get_default_input_device_info()
    print(f"  Default: {info['name']} sr={info['defaultSampleRate']} ch={info['maxInputChannels']}")
    stream = p.open(format=pyaudio.paFloat32, channels=1, rate=int(info["defaultSampleRate"]), input=True, frames_per_buffer=1024)
    data = stream.read(1024)
    stream.stop_stream()
    stream.close()
    p.terminate()
    print(f"  PyAudio OK! Capturó {len(data)} bytes")
except ImportError:
    print("  PyAudio no instalado")
except Exception as e:
    print(f"  PyAudio error: {e}")
