import sounddevice as sd

devices = sd.query_devices()
input_devs = [d for d in devices if d['max_input_channels'] > 0]

print(f'Total input devices: {len(input_devs)}\n')
for i, d in enumerate(input_devs):
    print(f'{i}: {d["name"]} ({d["max_input_channels"]} ch)')
