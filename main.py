import record

recorder = record.Recorder()

while True:
    try:
        recorder.monitor_keys()
    finally:
        recorder.close()

