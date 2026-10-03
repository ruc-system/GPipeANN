#!/usr/bin/env python3
"""Fault injection for search recovery. No GPU, sudo or SSD access."""
import csv
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import shutil
from recover_search_csv import snapshot, recover

SCRIPTS = Path(__file__).resolve().parent
MOCK = r'''#!/usr/bin/env python3
import csv, os, sys
from pathlib import Path
args = sys.argv[1:]
values = ['2']
for i, arg in enumerate(args):
    if arg in ('--num-blocks-list', '--mini-batch-list'):
        values = args[i+1].split(',')
    elif arg.startswith(('--num-blocks-list=', '--mini-batch-list=')):
        values = arg.split('=', 1)[1].split(',')
with open(os.environ['TRACE'], 'a') as f:
    f.write(','.join(values) + '\n')
axis = 'mini_batch' if any('mini-batch' in a for a in args) else 'num_blocks'
path = Path(os.environ['QUIVER_AE_METRICS_CSV'])
for value in values:
    print('Quiver Sweep: ' + axis + '=' + value, flush=True)
    fields = ['stem', 'num_blocks', 'mini_batch', 'qps', 'avg_ms', 'p99_ms']
    row = dict(stem=os.environ['QUIVER_AE_STEM'], num_blocks=0, mini_batch=0,
               qps=100, avg_ms=1, p99_ms=2)
    row[axis] = value
    empty = not path.exists() or not path.stat().st_size
    with path.open('a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        if empty: writer.writeheader()
        writer.writerow(row)
    marker = Path(os.environ['TRACE'] + '.failed')
    if value == '2' and (os.environ['MODE'] != 'transient' or not marker.exists()):
        marker.touch()
        if os.environ['MODE'] == 'hang':
            import time
            time.sleep(60)
        sys.exit(int(os.environ.get('FAIL_RC', '7')))
    print('Recall @ 10: 0.96', flush=True)
'''


class RecoveryTests(unittest.TestCase):
    def test_csv_recovery_preserves_other_results(self):
        with tempfile.TemporaryDirectory(prefix='quiver-csv-recovery-') as tmp:
            root = Path(tmp)
            metrics = root / 'metrics.csv'
            metrics.write_text('stem,num_blocks,qps\nother,99,100\n')
            samples = root / 'hop_samples.csv'
            samples.write_text('stem,sample_id\nother,0\n')
            prefix = samples.read_bytes()
            state = root / 'state.json'
            snapshot(root, state)
            with metrics.open('a') as output:
                output.write('case,1,100\ncase,2,100\n')
            with samples.open('a') as output:
                output.write('case,1\n')
            samples.chmod(0o444)
            recover(root, state, 'case', 'num_blocks', {'1'}, False)
            self.assertEqual(metrics.read_text(), 'stem,num_blocks,qps\nother,99,100\ncase,1,100\n')
            self.assertEqual(samples.read_bytes(), prefix)
            self.assertEqual(samples.stat().st_mode & 0o777, 0o444)
            archived = list(root.glob('.unassigned-samples-*/hop_samples.csv.raw'))
            self.assertEqual(len(archived), 1)
            self.assertIn('case,1', archived[0].read_text())

    def run_case(self, mode='permanent', axis='--num-blocks-list', rc='7', debug=False, retries=2):
        with tempfile.TemporaryDirectory(prefix='quiver-recovery-test-') as tmp:
            root = Path(tmp)
            mock = root / 'mock_search'
            mock.write_text(MOCK)
            mock.chmod(0o755)
            out = root / 'e2e' / 'runs' / 'test' if debug else root
            out.mkdir(parents=True, exist_ok=True)
            script = r'''
set -euo pipefail
source "$SCRIPTS/common.sh"
sudo() { if [[ "$1" == -n ]]; then shift; fi; "$@"; }
export SEARCH_RETRIES="$RETRIES" SEARCH_RETRY_DELAY=0
export HANG_FLOOR=1 HANG_FLOOR_FIRST=1 HANG_MULT=1
AE_NUMA_PREFIX=""
SPDK_BASE_LBA=0
SSD_LIST=/dev/null
AE_DEBUG_ROOT="$DEBUG_ROOT"
AE_DEBUG_FORCE=1
if [[ "$AXIS" == --num-blocks ]]; then
  run_search "$OUT/case.log" "$MOCK" "$AXIS" 2
elif [[ "$AXIS" == *=* ]]; then
  run_search "$OUT/case.log" "$MOCK" "$AXIS"
else
  run_search "$OUT/case.log" "$MOCK" "$AXIS" 1,2,3
fi
run_search "$OUT/next.log" "$MOCK" --num-blocks-list 4
'''
            env = dict(os.environ, SCRIPTS=str(SCRIPTS), OUT=str(out), MOCK=str(mock),
                       TRACE=str(root / 'trace'), MODE=mode, FAIL_RC=rc, AXIS=axis,
                       RETRIES=str(retries),
                       DEBUG_ROOT=str(root) if debug else '')
            result = subprocess.run(['bash', '-c', script], env=env,
                                    capture_output=True, text=True, timeout=45)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            calls = (root / 'trace').read_text().splitlines()
            expected = ['1,2,3', '2,3', '4'] if mode == 'transient' else (
                ['1,2,3'] + ['2,3'] * retries + ['3', '4'])
            if axis == '--num-blocks':
                expected = ['2'] * (retries + 1) + ['4']
            self.assertEqual(calls, expected)
            metrics = list(out.rglob('metrics.csv'))
            rows = []
            for path in metrics:
                with path.open() as handle:
                    rows.extend(csv.DictReader(handle))
            column = 'mini_batch' if axis == '--mini-batch-list' else 'num_blocks'
            case_values = [row[column] for row in rows if row['stem'] == 'case']
            expected_values = ['1', '2', '3'] if mode == 'transient' else ['1', '3']
            if axis == '--num-blocks':
                expected_values = []
            self.assertEqual(case_values, expected_values)
            self.assertEqual(sum(row['stem'] == 'next' for row in rows), 1)
            failures = list(out.rglob('failed_points.tsv'))
            self.assertEqual(len(failures), 0 if mode == 'transient' else 1)
            if failures:
                self.assertIn('\t2\t' + rc + '\t' + str(retries + 1), failures[0].read_text())
            if debug:
                self.assertIn('status=partial', (out / 'groups/case/manifest.env').read_text())

    def test_permanent_crash(self):
        self.run_case()

    def test_timeout_exit(self):
        self.run_case(rc='124')

    def test_watchdog_hang(self):
        self.run_case(mode='hang', rc='124')

    def test_transient_crash(self):
        self.run_case(mode='transient')

    def test_mini_batch(self):
        self.run_case(axis='--mini-batch-list')

    def test_partial_debug_group(self):
        self.run_case(debug=True)

    def test_scalar_point(self):
        self.run_case(axis='--num-blocks')

    def test_inline_list(self):
        self.run_case(axis='--num-blocks-list=1,2,3')

    def test_no_retries(self):
        self.run_case(retries=0)

    def test_run_all_continues_and_preserves_unpublished(self):
        with tempfile.TemporaryDirectory(prefix='quiver-run-all-test-') as tmp:
            root = Path(tmp)
            scripts = root / 'ae/scripts'
            scripts.mkdir(parents=True)
            for name in ('run_all.sh', 'paper_knobs.sh'):
                shutil.copy2(SCRIPTS / name, scripts / name)
            figures = ('latency_qps', 'io_latency', 'e2e', 'fusion', 'ablation', 'q_sensitivity')
            for name in figures:
                script = scripts / f'fig_{name}.sh'
                script.write_text('''#!/usr/bin/env bash
set -euo pipefail
name="${0##*/fig_}"; name="${name%.sh}"
mkdir -p "$AE_OUTPUT_ROOT/$name"
echo test > "$AE_OUTPUT_ROOT/$name/env.txt"
echo result > "$AE_OUTPUT_ROOT/$name/data.txt"
echo "$name" >> "$TEST_ROOT/tested.txt"
if [[ "$name" == e2e ]]; then
  printf 'case\\tnum_blocks\\t2\\t7\\t3\\n' > "$AE_OUTPUT_ROOT/$name/failed_points.tsv"
fi
if [[ "$name" == fusion ]]; then
  mkdir -p "$TEST_ROOT/ae/results/runs/test/fusion"
  echo untouched > "$TEST_ROOT/ae/results/runs/test/fusion/existing.txt"
fi
if [[ "$name" == io_latency ]]; then exit 7; fi
''')
                script.chmod(0o755)
            (scripts / 'plot_all.py').write_text('''import os, sys
from pathlib import Path
source = Path(sys.argv[1])
with (Path(os.environ['TEST_ROOT']) / 'plotted.txt').open('a') as output:
    output.write(source.name + '\\n')
raise SystemExit(1 if source.name == 'e2e' else 0)
''')
            result = subprocess.run(['bash', str(scripts / 'run_all.sh')],
                                    env=dict(os.environ, TEST_ROOT=str(root), AE_RUN_ID='test', AE_DEBUG_ROOT=''),
                                    capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertEqual((root / 'tested.txt').read_text().splitlines(), list(figures))
            self.assertEqual((root / 'plotted.txt').read_text().splitlines(), list(figures))
            published = root / 'ae/results/runs/test'
            self.assertEqual((published / 'e2e/status.env').read_text(), 'status=partial\n')
            self.assertEqual((published / 'io_latency/status.env').read_text(), 'status=failed\n')
            self.assertEqual((published / 'fusion/existing.txt').read_text(), 'untouched\n')
            retained = list(root.glob('.cache/ae-staging/run.*/fusion/data.txt'))
            self.assertEqual(len(retained), 1)
            self.assertIn('Unpublished results retained:', result.stderr)

    def test_real_partial_plot(self):
        with tempfile.TemporaryDirectory(prefix='quiver-partial-plot-') as tmp:
            root = Path(tmp)
            source = root / 'e2e'
            source.mkdir()
            (source / 'failed_points.tsv').write_text('case\tnum_blocks\t972\t7\t3\n')
            (source / 'metrics.csv').write_text(
                'stem,variant,system,dataset,ef,target_recall,num_blocks,mini_batch,queries_per_block,pipe_width,qps,avg_ms,p50_ms,p90_ms,p99_ms,p999_ms,max_ms,latency_kind\n'
                'case,,Quiver,deep1b,145,0.96,864,0,3,2,30000,8,8,9,10,11,12,QueryLatency(ms)\n')
            result = subprocess.run(['python3', str(SCRIPTS / 'plot_all.py'), str(source), '-o', str(root / 'plots')],
                                    capture_output=True, text=True, timeout=45)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            pdf = root / 'plots/figure5_e2e.pdf'
            self.assertTrue(pdf.is_file())
            self.assertIn('is partial', result.stderr)
            if shutil.which('pdftotext'):
                text = subprocess.check_output(['pdftotext', str(pdf), '-'], text=True)
                self.assertIn('Partial run: failed points omitted', text)


if __name__ == '__main__':
    unittest.main()
