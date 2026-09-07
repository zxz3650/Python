"""합성 Windows 아티팩트 CSV와 열 매핑 manifest를 생성한다."""
import argparse
import csv
import json
from pathlib import Path


def make_sample(root):
    root.mkdir(parents=True, exist_ok=False)
    sources = []

    def source(name, host, artifact, headers, rows, columns, kind):
        with (root / (name + '.csv')).open('w', encoding='utf-8-sig', newline='') as stream:
            writer = csv.writer(stream)
            writer.writerow(headers)
            writer.writerows(rows)
        sources.append({"id": name, "host": host, "artifact": artifact, "path": name+'.csv',
                        "parser": "synthetic-training-export", "parser_version": "1",
                        "timestamp_kind": kind, "columns": columns})

    headers = ['When', 'Id', 'Channel', 'Provider', 'Record', 'Account', 'Address', 'Type', 'Image']
    columns = dict(zip(['timestamp', 'event_id', 'channel', 'provider', 'record_id', 'user', 'src_ip', 'logon_type', 'path'], headers))
    security = 'Microsoft-Windows-Security-Auditing'
    image = r'C:\Users\analyst\AppData\Local\Temp\demo.exe'
    user = r'LAB\analyst'
    rows = [[f'2026-09-01T00:0{n}:00Z', '4625', 'Security', security, str(101+n), user, '192.0.2.50', '3', ''] for n in range(3)]
    rows += [
        ['2026-09-01T00:03:00Z', '1', 'Microsoft-Windows-Sysmon/Operational', 'Microsoft-Windows-Sysmon', '104', user, '', '', image],
        ['2026-09-01T00:04:00Z', '4624', 'Security', security, '105', user, '192.0.2.50', '3', ''],
    ]
    source('events-host-a', 'HOST-A', 'evtx', headers, rows, columns, 'event_created')
    source('events-host-b', 'HOST-B', 'evtx', headers, [
        ['2026-09-01T09:06:00+09:00', '4624', 'Security', security, '201', user, '192.0.2.50', '10', ''],
        ['2026-09-01T00:06:30Z', '4698', 'Security', security, '203', user, '', '', r'C:\Training\backup.exe'],
        ['2026-09-01T00:06:40Z', '7045', 'System', 'Service Control Manager', '204', user, '', '', r'C:\Training\inventory.exe'],
        ['2026-09-01T00:06:50Z', '4720', 'Security', security, '205', r'LAB\new-user', '', '', ''],
        ['2026-09-01 09:07:00', '4624', 'Security', security, '202', user, '192.0.2.50', '3', ''],
    ], columns, 'event_created')
    source('prefetch', 'HOST-A', 'prefetch', ['LastRun', 'Executable'], [
        ['2026-09-01T00:03:05Z', image],
        ['2026-09-01T00:05:00Z', r'C:\Windows\System32\notepad.exe'],
    ], {'timestamp': 'LastRun', 'path': 'Executable'}, 'prefetch_last_run')
    source('registry', 'HOST-A', 'registry', ['KeyWrite', 'KeyPath', 'ValueData'], [
        ['2026-09-01T00:02:30Z', r'HKCU\Software\Microsoft\Windows\CurrentVersion\Run', image],
    ], {'timestamp': 'KeyWrite', 'registry_key': 'KeyPath', 'path': 'ValueData'}, 'registry_key_last_write')
    source('mft', 'HOST-A', 'mft', ['SICreated', 'FNCreated', 'FullPath'], [
        ['2000-01-01T00:00:00Z', '2026-09-01T00:01:00Z', image],
    ], {'timestamp': 'SICreated', 'other_timestamp': 'FNCreated', 'path': 'FullPath'}, 'file_creation_si')
    source('shimcache', 'HOST-B', 'shimcache', ['FileModified', 'Path'], [
        ['', r'C:\Training\inventory.exe'],
    ], {'timestamp': 'FileModified', 'path': 'Path'}, 'cached_file_modified')
    sources.append({"id": "amcache", "host": "HOST-B", "artifact": "amcache", "path": "amcache.csv",
                    "parser": "synthetic-training-export", "parser_version": "1", "timestamp_kind": "inventory_time",
                    "columns": {"timestamp": "ObservedAt", "path": "FullPath"}})
    manifest = {"schema_version": 1, "case_id": "SYNTHETIC-CASE-001", "sources": sources}
    (root/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    return root/'manifest.json'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    print(make_sample(args.output))
