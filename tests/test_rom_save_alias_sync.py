import importlib.util,json,struct,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('bridge',Path(__file__).parents[1]/'bin/rom-save-alias-sync.py');bridge=importlib.util.module_from_spec(spec);spec.loader.exec_module(bridge)
class SaveBridgeTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)/'shared';self.root.mkdir();self.state=Path(self.tmp.name)/'state.json'
 def tearDown(self):self.tmp.cleanup()
 def setup_group(self,group,values):
  (self.root/'.save-aliases.json').write_text(json.dumps({'groups':[group]}))
  for name,data in values.items():(self.root/name).write_bytes(data)
  return bridge.reconcile(self.root,self.state,initialize=True,ignore_running=True)
 def test_new_local_save_reaches_other_names(self):
  group={'id':'test','canonical':{'path':'canonical.srm'},'aliases':[{'path':'first.srm'},{'path':'second.srm'}]};self.setup_group(group,{'canonical.srm':b'A'*8192})
  (self.root/'first.srm').write_bytes(b'B'*8192);r=bridge.reconcile(self.root,self.state,ignore_running=True)
  self.assertFalse(r['conflicts']);self.assertEqual((self.root/'canonical.srm').read_bytes(),b'B'*8192);self.assertEqual((self.root/'second.srm').read_bytes(),b'B'*8192)
 def test_simultaneous_different_progress_is_preserved(self):
  group={'id':'test','canonical':{'path':'canonical.srm'},'aliases':[{'path':'first.srm'},{'path':'second.srm'}]};self.setup_group(group,{'canonical.srm':b'A'*8192})
  (self.root/'first.srm').write_bytes(b'B'*8192);(self.root/'second.srm').write_bytes(b'C'*8192);r=bridge.reconcile(self.root,self.state,ignore_running=True)
  self.assertEqual(len(r['conflicts']),1);self.assertEqual((self.root/'canonical.srm').read_bytes(),b'A'*8192);self.assertEqual((self.root/'second.srm').read_bytes(),b'C'*8192)
 def test_incompatible_sizes_do_not_overwrite(self):
  group={'id':'test','canonical':{'path':'canonical.srm'},'aliases':[{'path':'first.srm'}]};self.setup_group(group,{'canonical.srm':b'A'*8192});(self.root/'first.srm').write_bytes(b'B'*16384);r=bridge.reconcile(self.root,self.state,ignore_running=True)
  self.assertTrue(r['errors']);self.assertEqual((self.root/'canonical.srm').read_bytes(),b'A'*8192)
 def test_smw_bidirectional_conversion_preserves_sa1_other_memory(self):
  def payload(exits):
   block=bytearray(143);block[140]=exits;struct.pack_into('<H',block,141,(0x5a5a-sum(block[:141]))&65535)
   return bytes(block)+b'\xff'*286+bytes(block)+b'\xff'*286
  a=payload(36);b=payload(40);g={'id':'smw','format':'smw-sa1','canonical':{'path':'canonical.srm','size':2048,'offset':0,'length':858},'aliases':[{'path':'normal.srm','size':2048,'offset':0,'length':858},{'path':'wide.srm','size':131072,'offset':0x1c000,'length':858}]}
  original=bytearray(b'Z'*131072);original[0x1c000:0x1c000+858]=a;self.setup_group(g,{'canonical.srm':a+b'\xff'*(2048-858),'wide.srm':original})
  normal=bytearray((self.root/'normal.srm').read_bytes());normal[:858]=b;(self.root/'normal.srm').write_bytes(normal);r=bridge.reconcile(self.root,self.state,ignore_running=True);self.assertFalse(r['errors'])
  wide=(self.root/'wide.srm').read_bytes();self.assertEqual(wide[:0x1c000],original[:0x1c000]);self.assertEqual(wide[0x1c000+858:],original[0x1c000+858:]);self.assertEqual(wide[0x1c000:0x1c000+858],b)
  modified=bytearray(wide);modified[0x1c000:0x1c000+858]=a;(self.root/'wide.srm').write_bytes(modified);bridge.reconcile(self.root,self.state,ignore_running=True);self.assertEqual((self.root/'normal.srm').read_bytes()[:858],a)
 def test_smw_missing_format_is_rejected(self):
  g={'id':'smw','format':'smw-sa1','canonical':{'path':'canonical.srm'},'aliases':[{'path':'normal.srm'}]}
  r=self.setup_group(g,{'canonical.srm':b'A'*2048})
  self.assertTrue(r['errors']);self.assertFalse((self.root/'normal.srm').exists())
 def test_running_game_prevents_reconciliation(self):
  with patch.object(bridge.subprocess,'run') as call:
   call.return_value.returncode=0;r=bridge.reconcile(self.root,self.state)
  self.assertEqual(r['updated'],0);self.assertFalse(self.state.exists())
if __name__=='__main__':unittest.main()
