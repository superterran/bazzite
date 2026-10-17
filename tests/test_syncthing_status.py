import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('status',Path(__file__).parents[1]/'bin/syncthing-status.py')
status=importlib.util.module_from_spec(spec);spec.loader.exec_module(status)

class StatusTests(unittest.TestCase):
 def test_offline_idle_does_not_claim_up_to_date(self):
  folder={'paused':False,'pullErrors':0,'receiveOnlyChangedFiles':0,'needFiles':0,'needBytes':0,'state':'idle'}
  self.assertEqual(status.summary(folder,False),'Waiting for connection')
  self.assertEqual(status.summary(folder,True),'Up to date')
  rendered=status.render({'checked':'12:00','connected':[],'folders':{'rom-saves':folder}})
  self.assertIn('Saves: Waiting for connection',rendered)
 def test_pending_files_still_report_work_remaining(self):
  folder={'paused':False,'pullErrors':0,'receiveOnlyChangedFiles':0,'needFiles':2,'needBytes':1024,'state':'idle'}
  self.assertIn('2 files left',status.summary(folder))
