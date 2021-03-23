import unittest
from app.alarm import Bell

class TestableBell(Bell):
    isOn = False
    def switchOn(self):
        self.isOn = True
    def switchOff(self):
        self.isOn = False

class TestBell(unittest.TestCase):

    def test_lifecycle(self):
        bell = TestableBell()
        self.assertEqual(bell.state, 'DISABLED')
        bell.handleAlarm()
        self.assertEqual(bell.state, 'DISABLED')
        bell.config("READY")
        bell.handleAlarm()
        self.assertEqual(bell.state, 'ON')
        self.assertEqual(bell.counter, 0)
        self.assertEqual(bell.isOn, True)
        for i in range(Bell.BELL_MAX_COUNTER_BEFORE_SUSPENSION):
            bell.handleTick()
            self.assertEqual(bell.counter, i + 1)
        self.assertEqual(bell.counter, Bell.BELL_MAX_COUNTER_BEFORE_SUSPENSION)
        self.assertEqual(bell.state, 'ON')
        bell.handleTick()
        self.assertEqual(bell.state, 'SUSPENDED')
        self.assertEqual(bell.isOn, False)

if __name__ == '__main__':
    unittest.main()