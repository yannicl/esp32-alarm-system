import unittest
from app.alarm import ZoneReadings
from app.alarm import ZoneReading
from app.alarm import ZoneStatuses
from app.alarm import ZoneStatus
from app.alarm import ZoneConfig

class TestZone(unittest.TestCase):

    testConfig = [ZoneConfig.ARMED, ZoneConfig.ARMED, ZoneConfig.DISABLED, ZoneConfig.DISABLED, ZoneConfig.DISABLED, ZoneConfig.DISABLED, ZoneConfig.DISABLED, ZoneConfig.DISABLED]

    readingsAllNormal = [ZoneReading.NORMAL, ZoneReading.NORMAL, ZoneReading.NORMAL, ZoneReading.NORMAL, ZoneReading.NORMAL, ZoneReading.NORMAL, ZoneReading.NORMAL, ZoneReading.NORMAL]

    readingsTriggered1 = [ZoneReading.TRIGGERED, ZoneReading.NORMAL, ZoneReading.NORMAL, ZoneReading.NORMAL, ZoneReading.NORMAL, ZoneReading.NORMAL, ZoneReading.NORMAL, ZoneReading.NORMAL]
    readingsTriggered2 = [ZoneReading.NORMAL, ZoneReading.TRIGGERED, ZoneReading.NORMAL, ZoneReading.NORMAL, ZoneReading.NORMAL, ZoneReading.NORMAL, ZoneReading.NORMAL, ZoneReading.NORMAL]
    readingsTriggered3 = [ZoneReading.NORMAL, ZoneReading.NORMAL, ZoneReading.TRIGGERED, ZoneReading.NORMAL, ZoneReading.NORMAL, ZoneReading.NORMAL, ZoneReading.NORMAL, ZoneReading.NORMAL]

    def test(self):
        zones = ZoneStatuses()
        self.assertEqual(zones.hasTrippedZone(), False)

    def test_config(self):
        zones = ZoneStatuses()
        zones.config(self.testConfig)
        self.assertEqual(zones.hasTrippedZone(), False)

    def test_reading_all_normal(self):
        zones = ZoneStatuses()
        zones.config(self.testConfig)
        zones.handleZoneReadingsUpdate(self.readingsAllNormal)

        self.assertEqual(zones.hasTrippedZone(), False)

    def test_triggered_disabled_zone(self):
        zones = ZoneStatuses()
        zones.config(self.testConfig)
        zones.handleZoneReadingsUpdate(self.readingsTriggered3)

        self.assertEqual(zones.hasTrippedZone(), False)

    def test_triggered_armed_zone(self):
        zones = ZoneStatuses()
        zones.config(self.testConfig)
        zones.handleZoneReadingsUpdate(self.readingsTriggered1)

        self.assertEqual(zones.hasTrippedZone(), True)


    def test_tripped_zone_not_reset_when_all_readings_are_back_to_normal(self):
        zones = ZoneStatuses()
        zones.config(self.testConfig)
        zones.handleZoneReadingsUpdate(self.readingsTriggered1)

        self.assertEqual(zones.hasTrippedZone(), True)

        zones.handleZoneReadingsUpdate(self.readingsAllNormal)

        self.assertEqual(zones.hasTrippedZone(), True)
        
    def test_multiple_zones_tripped(self):
        zones = ZoneStatuses()
        zones.config(self.testConfig)
        zones.handleZoneReadingsUpdate(self.readingsTriggered1)
        zones.handleZoneReadingsUpdate(self.readingsTriggered2)

        self.assertEqual(zones.hasTrippedZone(), True)
        self.assertEqual(zones.get(0).state, ZoneStatus.TRIPPED)
        self.assertEqual(zones.get(1).state, ZoneStatus.TRIPPED)






