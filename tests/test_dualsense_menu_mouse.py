import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest

spec = importlib.util.spec_from_file_location('mouse', Path(__file__).resolve().parents[1] / 'bin/dualsense-menu-mouse.py')
mouse = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mouse)
E = mouse.E


class Output:
    def __init__(self): self.events = []
    def write(self, *event): self.events.append(event)
    def syn(self): pass


class MouseTests(unittest.TestCase):
    def setUp(self):
        self.out = Output()
        self.g = mouse.Gesture(self.out)
        self.g.enable(True)
        self.g.frame(0)  # neutral touchpad arms the first gesture

    def event(self, kind, code, value, now=0):
        self.g.event(SimpleNamespace(type=kind, code=code, value=value), now)

    def touch(self, slot, x, y, now=0):
        self.event(E.EV_ABS, E.ABS_MT_SLOT, slot)
        self.event(E.EV_ABS, E.ABS_MT_TRACKING_ID, slot+1)
        self.event(E.EV_ABS, E.ABS_MT_POSITION_X, x)
        self.event(E.EV_ABS, E.ABS_MT_POSITION_Y, y)
        self.g.frame(now)

    def lift(self, slot, now=.1):
        self.event(E.EV_ABS, E.ABS_MT_SLOT, slot)
        self.event(E.EV_ABS, E.ABS_MT_TRACKING_ID, -1)
        self.g.frame(now)

    def test_one_finger_tap_left_click(self):
        self.touch(0, 100, 100)
        self.lift(0)
        self.assertEqual(self.out.events, [(E.EV_KEY,E.BTN_LEFT,1),(E.EV_KEY,E.BTN_LEFT,0)])

    def test_two_finger_tap_right_click(self):
        self.touch(0,100,100)
        self.touch(1,200,100,.02)
        self.lift(0,.1)
        self.lift(1,.12)
        self.assertEqual(self.out.events, [(E.EV_KEY,E.BTN_RIGHT,1),(E.EV_KEY,E.BTN_RIGHT,0)])

    def test_drag_moves_without_click_on_release(self):
        self.touch(0,100,100)
        self.event(E.EV_ABS,E.ABS_MT_POSITION_X,140)
        self.g.frame(.05)
        self.lift(0)
        self.assertIn((E.EV_REL,E.REL_X,50),self.out.events)
        self.assertFalse(any(event[0]==E.EV_KEY for event in self.out.events))

    def test_right_half_press_right_click_without_extra_tap(self):
        self.touch(0,1500,100)
        self.event(E.EV_KEY,E.BTN_LEFT,1,.02)
        self.event(E.EV_KEY,E.BTN_LEFT,0,.08)
        self.lift(0)
        self.assertEqual(self.out.events,[(E.EV_KEY,E.BTN_RIGHT,1),(E.EV_KEY,E.BTN_RIGHT,0)])

    def test_switch_to_game_releases_held_click(self):
        self.touch(0,100,100)
        self.event(E.EV_KEY,E.BTN_LEFT,1,.02)
        self.g.enable(False)
        self.lift(0)
        self.assertEqual(self.out.events,[(E.EV_KEY,E.BTN_LEFT,1),(E.EV_KEY,E.BTN_LEFT,0)])

    def test_long_touch_does_not_click(self):
        self.touch(0,100,100)
        self.lift(0,1)
        self.assertEqual(self.out.events,[])

    def test_disabled_no_movement_or_click(self):
        self.g.enable(False)
        self.touch(0,100,100)
        self.lift(0)
        self.assertEqual(self.out.events,[])

    def test_dropped_events_release_and_wait_for_neutral(self):
        self.touch(0,100,100)
        self.event(E.EV_KEY,E.BTN_LEFT,1,.02)
        self.event(E.EV_SYN,E.SYN_DROPPED,0,.04)
        self.assertIsNone(self.g.held)
        self.assertFalse(self.g.armed)


class ReportTests(unittest.TestCase):
    def packet(self, bluetooth=True):
        data=bytearray(78 if bluetooth else 64)
        base=2 if bluetooth else 1
        data[0]=0x31 if bluetooth else 1
        data[base+32]=0x80
        data[base+36]=0x80
        return data,base

    def test_bluetooth_contact_and_buttons(self):
        data,base=self.packet()
        data[base+32:base+36]=bytes([5,0x34,0x12,0x26])
        data[base+9]=3
        self.assertEqual(mouse.parse_report(data),({0:(5,0x234,0x261)},True,True))

    def test_idle_and_usb_reports(self):
        for bluetooth in [False,True]:
            data,_=self.packet(bluetooth)
            self.assertEqual(mouse.parse_report(data),({},False,False))

    def test_bad_report_ignored(self):
        self.assertIsNone(mouse.parse_report(b'bad'))


if __name__=='__main__': unittest.main()
