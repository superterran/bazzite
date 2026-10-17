"""Let a core unload and write its battery save before a launcher exits."""
import signal
import socket
import subprocess
import sys
import time


def run_session(args, port):
    # Avoid directing a close request at another session using this port.
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
        probe.bind(('0.0.0.0', port))
    child = subprocess.Popen(args, start_new_session=True)
    requested = False

    def request_close(signum, frame):
        nonlocal requested
        requested = True

    previous = {sig: signal.signal(sig, request_close)
                for sig in (signal.SIGTERM, signal.SIGINT)}
    started = None
    warned = False
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            while True:
                if requested:
                    if started is None:
                        started = time.monotonic()
                    # QUIT runs RetroArch's content unload; SIGTERM can bypass it.
                    sock.sendto(b'QUIT', ('127.0.0.1', port))
                    if not warned and time.monotonic() - started > 10:
                        print('Waiting for RetroArch to close normally and write its save. '
                              'Use Quit RetroArch in its menu if it is not responding.',
                              file=sys.stderr, flush=True)
                        warned = True
                try:
                    return child.wait(timeout=0.5)
                except subprocess.TimeoutExpired:
                    pass
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)
