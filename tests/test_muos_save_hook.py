import importlib.util
from pathlib import Path
import unittest

path=Path(__file__).parents[1]/'bin/install-muos-save-hook.py'
spec=importlib.util.spec_from_file_location('hook',path)
hook=importlib.util.module_from_spec(spec);spec.loader.exec_module(hook)

class MuosHookTests(unittest.TestCase):
 def test_new_hook_explicitly_selects_shared_config(self):
  source='#!/bin/sh\nRA_ARGS=$(CONFIGURE_RETROARCH)\n'+hook.needle+'\necho done\n'
  result=hook.update(source)
  self.assertIn(hook.configured,result)
  self.assertEqual(result.count(hook.sync),2)
  self.assertEqual(result.count(hook.gate_marker),2)
  self.assertLess(result.index(hook.gate.format('pre')),result.index(hook.configured))
  self.assertGreater(result.index(hook.gate.format('post')),result.index(hook.configured))
  self.assertEqual(hook.update(result),result)
 def test_existing_hook_gets_config_fix_without_duplicate_hooks(self):
  source=hook.marker+'\n'+hook.sync+'\n'+hook.needle+'\n'+hook.sync+'\n'
  result=hook.update(hook.add_gate(source))
  self.assertIn(hook.configured,result)
  self.assertEqual(result.count(hook.sync),2)
  self.assertEqual(result.count(hook.gate_marker),2)
  self.assertEqual(hook.update(result),result)
 def test_unknown_launch_format_is_rejected(self):
  with self.assertRaises(ValueError):hook.update('other-emulator "$FILE"')
