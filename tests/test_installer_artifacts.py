"""Installation should copy skill source, not generated Python/test caches."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class InstallerArtifacts(unittest.TestCase):
    def test_generated_caches_are_not_installed(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source = base / 'source'
            source.mkdir()
            shutil.copyfile(ROOT / 'install.sh', source / 'install.sh')
            for name in ('opencode.jsonc', 'cli.json', 'AGENTS.md'):
                (source / name).write_text('{}')
            for name in ('agents', 'commands', 'skills'):
                (source / name).mkdir()
            scripts = source / 'skills/example/scripts'
            scripts.mkdir(parents=True)
            (scripts / 'helper.py').write_text('print("source")')
            (scripts / '__pycache__').mkdir()
            (scripts / '__pycache__/helper.cpython-313.pyc').write_bytes(b'cache')
            (scripts / 'legacy.pyc').write_bytes(b'cache')
            (scripts / '.pytest_cache').mkdir()
            (scripts / '.pytest_cache/state').write_text('cache')
            env = {**os.environ, 'XDG_CONFIG_HOME': str(base / 'xdg')}
            result = subprocess.run(['bash', str(source / 'install.sh'), '--apply'],
                                    env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            target = base / 'xdg/opencode'
            self.assertTrue((target / 'skills/example/scripts/helper.py').is_file())
            self.assertEqual(list(target.rglob('*.pyc')), [])
            self.assertEqual(list(target.rglob('.pytest_cache')), [])


if __name__ == '__main__':
    unittest.main()
