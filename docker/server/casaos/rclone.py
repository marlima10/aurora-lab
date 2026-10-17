import hashlib,json,pathlib,subprocess,urllib.request,zipfile

def install_rclone(lock,stage):
    item=json.loads(pathlib.Path(lock).read_text())
    archive=pathlib.Path(stage)/item['file']
    if not archive.exists():
        with urllib.request.urlopen(item['url'],timeout=180) as source:archive.write_bytes(source.read())
    assert hashlib.sha256(archive.read_bytes()).hexdigest()==item['sha256'],'rclone SHA-256 divergente'
    with zipfile.ZipFile(archive) as source:
        binary=source.read('rclone-v'+item['version']+'-linux-amd64/rclone')
    dest=pathlib.Path('/usr/local/bin/rclone');dest.write_bytes(binary);dest.chmod(0o755)
    folder=pathlib.Path('/etc/systemd/system/rclone.service.d');folder.mkdir(parents=True,exist_ok=True)
    (folder/'aurora.conf').write_text('[Service]\nExecStart=\nExecStart=/usr/local/bin/rclone rcd --rc-addr unix:///var/run/rclone/rclone.sock --rc-no-auth --rc-allow-origin "*"\nUMask=0077\n')
    subprocess.run(['systemctl','daemon-reload'],check=True)
    subprocess.run(['systemctl','restart','rclone'],check=True)

if __name__=='__main__':
    install_rclone(pathlib.Path(__file__).with_name('rclone.lock.json'),'/srv/auroralab/deploy-state/casaos-stage')
