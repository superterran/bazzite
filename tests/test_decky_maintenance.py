import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

spec = importlib.util.spec_from_file_location('maintenance', Path(__file__).resolve().parents[1] / 'bin/decky-maintenance.py')
maintenance = importlib.util.module_from_spec(spec)
spec.loader.exec_module(maintenance)


class MaintenanceTests(unittest.TestCase):
    def test_only_stable_versions_and_no_downgrade(self):
        self.assertIsNone(maintenance.version_key('v3.4.0-pre1'))
        self.assertGreater(maintenance.version_key('1.3.4'), maintenance.version_key('1.2.0'))

    def test_archive_metadata(self):
        data = io.BytesIO()
        with zipfile.ZipFile(data, 'w') as archive:
            archive.writestr('example/plugin.json', json.dumps({'name': 'Example'}))
            archive.writestr('example/package.json', json.dumps({'version': '1.0.0'}))
        with tempfile.TemporaryDirectory() as temp:
            root = maintenance.extract_plugin(data.getvalue(), 'Example', '1.0.0', Path(temp))
            self.assertEqual(root.name, 'example')
            with self.assertRaises(ValueError):
                maintenance.extract_plugin(data.getvalue(), 'Wrong name', '1.0.0', Path(temp))

    def test_archive_traversal_and_symlinks_rejected(self):
        for name, mode in [('../escape', 0), ('symlink', 0o120777 << 16)]:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp:
                data = io.BytesIO()
                with zipfile.ZipFile(data, 'w') as archive:
                    entry = zipfile.ZipInfo(name)
                    if mode:
                        entry.external_attr = mode
                    archive.writestr(entry, 'outside')
                with self.assertRaises(ValueError):
                    maintenance.extract_plugin(data.getvalue(), 'Example', '1.0.0', Path(temp))


if __name__ == '__main__':
    unittest.main()
