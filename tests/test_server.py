"""Démarrage d'un vrai serveur local et contrôle HTTP, puis arrêt garanti."""
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.request

def test_server_health(tmp_path):
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0))
        port=sock.getsockname()[1]
    root=Path(__file__).resolve().parents[1]
    env=os.environ.copy(); env['SMCA_DB']=str(tmp_path/'server.db')
    args=[sys.executable,'-m','streamlit','run',str(root/'app.py'),'--server.address=127.0.0.1',f'--server.port={port}','--server.headless=true','--browser.gatherUsageStats=false']
    with (tmp_path/'server.log').open('w') as log:
        process=subprocess.Popen(args,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT)
        try:
            deadline=time.monotonic()+30
            while time.monotonic()<deadline:
                assert process.poll() is None, 'Le serveur s’est arrêté avant le contrôle HTTP.'
                try:
                    with urllib.request.urlopen(f'http://127.0.0.1:{port}/_stcore/health',timeout=1) as response:
                        assert response.read()==b'ok'
                    with urllib.request.urlopen(f'http://127.0.0.1:{port}/',timeout=2) as response:
                        assert response.status==200
                    return
                except OSError:
                    time.sleep(.2)
            raise AssertionError('Le serveur ne répond pas dans les 30 secondes.')
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill(); process.wait()
