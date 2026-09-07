import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

EXAMPLES = Path(__file__).parents[1] / 'examples/13-kape-triage'


def load(name):
    spec = importlib.util.spec_from_file_location(name, EXAMPLES / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pipeline = load('pipeline')
sample = load('make_sample')


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manifest = sample.make_sample(self.root / 'input')

    def read(self):
        return pipeline.load_case(self.manifest)

    def edit_manifest(self, fn):
        data = json.loads(self.manifest.read_text())
        fn(data)
        self.manifest.write_text(json.dumps(data))

    def test_sample_counts_provenance_and_input_preservation(self):
        original = {p.name: p.read_bytes() for p in self.manifest.parent.iterdir()}
        output = self.root / 'report'
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(pipeline.main([str(self.manifest), '--output', str(output)]), 2)
        report = json.loads((output / 'report.json').read_text())
        self.assertEqual(report['summary'], {'events': 14, 'findings': 8, 'issues': 1, 'undated': 1, 'missing_sources': 1})
        self.assertEqual(report['processing_status'], 'partial')
        self.assertEqual({p.name: p.read_bytes() for p in self.manifest.parent.iterdir()}, original)
        self.assertTrue(all(e['source_sha256'] and e['source_record'] >= 2 for e in report['events']))
        self.assertEqual(json.loads((output / 'complete.json').read_text())['report_sha256'], pipeline.sha256((output / 'report.json').read_bytes()))
        self.assertTrue(any(set(r['artifacts']) >= {'evtx', 'prefetch', 'registry', 'mft'} for r in report['related_paths']))

    def test_offset_and_unknown_timestamp(self):
        self.assertEqual(pipeline.utc_time('2026-09-01T09:00:00+09:00'), '2026-09-01T00:00:00Z')
        self.assertEqual(pipeline.utc_time('2026-09-01 09:00:00', '+09:00'), '2026-09-01T00:00:00Z')
        self.assertIsNone(pipeline.utc_time(''))
        for value in ('2026-09-01 09:00:00', '2026-09-01', '2026-09-01T00:00:00.1234567Z'):
            with self.assertRaises(ValueError):
                pipeline.utc_time(value)

    def test_timestamp_sort_is_numeric_not_string(self):
        path = self.manifest.parent / 'prefetch.csv'
        path.write_text('LastRun,Executable\n2026-09-01T00:00:00.100000Z,b.exe\n2026-09-01T00:00:00Z,a.exe\n')
        events = [e for e in self.read()[2] if e['artifact'] == 'prefetch']
        self.assertEqual([e['path'] for e in events], ['a.exe', 'b.exe'])

    def test_missing_empty_and_failed_are_distinct(self):
        (self.manifest.parent / 'prefetch.csv').write_text('LastRun,Executable\n')
        (self.manifest.parent / 'mft.csv').write_text('wrong,headers\n')
        coverage = {s['source_id']: s for s in self.read()[4]}
        self.assertEqual(coverage['prefetch']['status'], 'empty')
        self.assertEqual(coverage['mft']['status'], 'parse_failed')
        self.assertEqual(coverage['amcache']['status'], 'missing')

    def test_path_escape_and_duplicate_manifest_rejected(self):
        self.edit_manifest(lambda data: data['sources'][0].update(path='../outside.csv'))
        with self.assertRaises(ValueError):
            self.read()
        self.edit_manifest(lambda data: data['sources'][0].update(path='events-host-a.csv'))
        self.edit_manifest(lambda data: data['sources'].append(data['sources'][0].copy()))
        with self.assertRaises(ValueError):
            self.read()

    def test_duplicate_evtx_does_not_inflate_rule(self):
        events = self.read()[2]
        one_failure = next(e for e in events if e['event_id'] == '4625')
        copies = [{**one_failure, 'uid': str(index)} for index in range(4)]
        findings, _ = pipeline.review_findings(copies)
        self.assertFalse(any(f['rule_id'] == 'LAB-AUTH-01' for f in findings))

    def test_time_window_and_provider_are_respected(self):
        events = [e.copy() for e in self.read()[2]]
        for event in events:
            if event['record_id'] == '103':
                event['timestamp_utc'] = '2026-09-01T01:00:00Z'
        events.sort(key=lambda e: (e['timestamp_utc'] is None, e['timestamp_utc'] or ''))
        findings, _ = pipeline.review_findings(events)
        self.assertFalse(any(f['rule_id'] == 'LAB-AUTH-01' for f in findings))
        for event in events:
            event['provider'] = 'Unrelated-provider'
        findings, _ = pipeline.review_findings(events)
        self.assertFalse(any(f['rule_id'] in {'LAB-PROCESS-01', 'LAB-HOST-01'} for f in findings))

    def test_html_escapes_untrusted_values(self):
        manifest, _, events, issues, coverage = self.read()
        report = {'case_id': '<script>alert(1)</script>', 'processing_status': 'partial',
                  'summary': {'events': 0, 'findings': 0, 'issues': 0, 'missing_sources': 0},
                  'events': events, 'findings': [], 'issues': issues, 'coverage': coverage}
        html = pipeline.report_html(report)
        self.assertNotIn('<script>', html)
        self.assertIn('&lt;script&gt;', html)
        self.assertIn('default-src', html)

    def test_output_reuse_and_inside_input_rejected(self):
        existing = self.root / 'existing'
        existing.mkdir()
        with contextlib.redirect_stderr(io.StringIO()):
            for output in (existing, self.manifest.parent / 'results'):
                self.assertEqual(pipeline.main([str(self.manifest), '--output', str(output)]), 1)

    def test_empty_detection_result_does_not_mean_missing(self):
        self.edit_manifest(lambda data: data['sources'].append({
            'id': 'detection', 'host': 'HOST-A', 'artifact': 'detection', 'path': 'detection.csv',
            'parser': 'synthetic-rules-output', 'parser_version': '1', 'timestamp_kind': 'event_created',
            'columns': {'timestamp': 'Time', 'rule_id': 'Rule'}}))
        (self.manifest.parent / 'detection.csv').write_text('Time,Rule\n')
        coverage = {s['source_id']: s for s in self.read()[4]}
        self.assertEqual(coverage['detection']['status'], 'empty')

    def test_complete_input_and_reproducible_results(self):
        def fix(data):
            data['sources'] = [source for source in data['sources'] if source['id'] != 'amcache']
            for source in data['sources']:
                if source['id'] == 'events-host-b':
                    source['utc_offset'] = '+09:00'
        self.edit_manifest(fix)
        outputs = [self.root / 'run-1', self.root / 'run-2']
        with contextlib.redirect_stdout(io.StringIO()):
            for output in outputs:
                self.assertEqual(pipeline.main([str(self.manifest), '--output', str(output)]), 0)
        self.assertEqual((outputs[0] / 'report.json').read_bytes(), (outputs[1] / 'report.json').read_bytes())
        report = json.loads((outputs[0] / 'report.json').read_text())
        self.assertEqual(report['summary']['events'], 15)
        self.assertEqual(report['summary']['findings'], 8)

    def test_symlink_input_is_rejected(self):
        path = self.manifest.parent / 'prefetch.csv'
        target = self.root / 'outside.csv'
        target.write_bytes(path.read_bytes())
        path.unlink()
        try:
            path.symlink_to(target)
        except OSError:
            self.skipTest('symlink unavailable')
        with self.assertRaises(ValueError):
            self.read()


if __name__ == '__main__':
    unittest.main()
