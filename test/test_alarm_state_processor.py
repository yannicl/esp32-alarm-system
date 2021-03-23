import unittest
from app.alarm import Bell
from app.alarm import AlarmStateProcessor
from app.alarm import ZoneReading

class TestableBell(Bell):
    isOn = False
    def switchOn(self):
        self.isOn = True
    def switchOff(self):
        self.isOn = False

class TestableAlarmStateProcessor(AlarmStateProcessor):
    publishingAlarmCounter = 0
    publishingStateCounter = 0
    def publishAlarm(self):
        self.publishingAlarmCounter = self.publishingAlarmCounter + 1
    def publishState(self):
        self.publishingStateCounter = self.publishingStateCounter + 1

class TestAlarmStateProcessor(unittest.TestCase):

    alarmConfig = {
        "bell" : "READY",
        "zones" : ["ARMED", "ARMED", "DISABLED", "DISABLED", "DISABLED", "DISABLED", "DISABLED", "DISABLED"]
    }

    readingsAllNormal = [ZoneReading.NORMAL, ZoneReading.NORMAL, ZoneReading.NORMAL, ZoneReading.NORMAL, ZoneReading.NORMAL, ZoneReading.NORMAL, ZoneReading.NORMAL, ZoneReading.NORMAL]

    readingsTriggered1 = [ZoneReading.TRIGGERED, ZoneReading.NORMAL, ZoneReading.NORMAL, ZoneReading.NORMAL, ZoneReading.NORMAL, ZoneReading.NORMAL, ZoneReading.NORMAL, ZoneReading.NORMAL]
    

    bell = TestableBell()

    def test_initial_state(self):
        processor = TestableAlarmStateProcessor(self.bell)
        self.assertEqual(processor.publishingStateCounter, 0)
        self.assertEqual(processor.publishingAlarmCounter, 0)

    def test_first_configuration(self):
        processor = TestableAlarmStateProcessor(self.bell)
        processor.config(self.alarmConfig)
        self.assertEqual(processor.alarmStatus.export()["sensorReadings"], self.readingsAllNormal)
        self.assertEqual(processor.alarmStatus.export()["zones"], self.alarmConfig["zones"])
        self.assertEqual(processor.alarmStatus.export()["bell"], self.alarmConfig["bell"])
        self.assertEqual(self.bell.isOn, False)
        self.assertEqual(processor.publishingStateCounter, 1)
        self.assertEqual(processor.publishingAlarmCounter, 0)


    def test_normal_readings(self):
        processor = TestableAlarmStateProcessor(self.bell)
        processor.config(self.alarmConfig)
        processor.handleZonesUpdate(self.readingsAllNormal)

        self.assertEqual(processor.alarmStatus.export()["zones"], self.alarmConfig["zones"])
        self.assertEqual(processor.alarmStatus.export()["bell"], self.alarmConfig["bell"])
        self.assertEqual(self.bell.isOn, False)

    def test_triggered(self):
        processor = TestableAlarmStateProcessor(self.bell)
        processor.config(self.alarmConfig)
        processor.handleZonesUpdate(self.readingsTriggered1)

        self.assertEqual(processor.alarmStatus.export()["sensorReadings"], self.readingsTriggered1)
        self.assertEqual(processor.alarmStatus.export()["zones"][0], "TRIPPED")
        self.assertEqual(processor.alarmStatus.export()["bell"], "ON")
        self.assertEqual(self.bell.isOn, True)

        self.assertEqual(processor.publishingStateCounter, 2)
        self.assertEqual(processor.publishingAlarmCounter, 1)

