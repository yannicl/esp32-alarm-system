NBR_ZONES = 8


class ZoneConfig:
    ARMED = "ARMED"
    DISABLED = "DISABLED"

class ZoneReading:
    NORMAL = "NORMAL"
    TRIGGERED = "TRIGGERED"


class ZoneStatus:
    # state : ARMED, DISABLED, TRIPPED
    TRIPPED = "TRIPPED"

    def __init__(self):
        self.state = ZoneConfig.DISABLED

    # zone config : 
    def config(self, zoneConfig):
        self.state = zoneConfig

    def handleZoneReadingUpdate(self, reading):
        if (reading == ZoneReading.TRIGGERED and self.state == ZoneConfig.ARMED):
            self.state = ZoneStatus.TRIPPED


class ZoneReadings:
    
    def __init__(self):
        self.list = []
        for i in range(NBR_ZONES):
            self.list.append(ZoneReading.NORMAL)

    def get(self, index):
        return self.list[index].value

    def updateReadings(self, readings):
        self.list = readings
    
    def export(self):
        return self.list

class ZoneStatuses:

    def __init__(self):
        self.list = []
        for i in range(NBR_ZONES):
            self.list.append(ZoneStatus())

    def get(self, index):
        return self.list[index]

    def handleZoneReadingsUpdate(self, zoneReadings):
        for zoneStatus, zoneReading in zip(self.list, zoneReadings):
            zoneStatus.handleZoneReadingUpdate(zoneReading)
    
    def config(self, zoneConfigs):
        print("update zones config: ", zoneConfigs)
        for zoneStatus, zoneConfig in zip(self.list, zoneConfigs):
            zoneStatus.config(zoneConfig)

    def hasTrippedZone(self):
        r = False
        for zone in self.list:
            if (zone.state == ZoneStatus.TRIPPED):
                r = True
        return r

    def export(self):
        l = []
        for zone in self.list:
            l.append(zone.state)
        return l

class Bell:
    STATE_ON = "ON"
    STATE_READY = "READY"
    STATE_SUSPENDED = "SUSPENDED"
    STATE_DISABLED = "DISABLED"

    BELL_MAX_COUNTER_BEFORE_SUSPENSION = 300 # seconds

    def __init__(self):
        self.state = Bell.STATE_DISABLED
        self.switchOff()

    def get(self):
        return self.state

    def handleAlarm(self):
        if (self.state == Bell.STATE_READY):
            self.state = Bell.STATE_ON
            self.counter = 0
            self.switchOn()


    def handleTick(self):
        if (self.state == Bell.STATE_ON):
            self.counter = self.counter + 1
        if (self.state == Bell.STATE_ON and self.counter > Bell.BELL_MAX_COUNTER_BEFORE_SUSPENSION):
            self.state = Bell.STATE_SUSPENDED
            self.switchOff()
    
    def config(self, newState):
        print("update bell config: ", newState)
        self.state = newState
        if (self.state == Bell.STATE_ON):
            self.switchOn()
        else:
            self.switchOff()

    def switchOn(self):
        print('this implementation do nothing')
    
    def switchOff(self):
        print('this implementation do nothing')
        

class AlarmStatus:
    def __init__(self, zoneReadings, zoneStatuses, bell):
        self.zoneReadings = zoneReadings
        self.zoneStatuses = zoneStatuses
        self.bell = bell

    def export(self):
        return {
            "sensorReadings": self.zoneReadings.export(),
            "zones" : self.zoneStatuses.export(), 
            "bell" : self.bell.state
        }

class AlarmStateProcessor:
    def __init__(self, bell):
        self.bell = bell
        self.zoneReadings = ZoneReadings()
        self.zoneStatuses = ZoneStatuses()
        self.alarmStatus = AlarmStatus(self.zoneReadings, self.zoneStatuses, bell)
    
    def handleZonesUpdate(self, zones):
        # is any pre-existing alarm condition
        preAlarmCondition = self.alarmStatus.zoneStatuses.hasTrippedZone()
        # update readings
        self.zoneReadings.updateReadings(zones)
        self.zoneStatuses.handleZoneReadingsUpdate(zones)
        # update zone status
        self.alarmStatus.zoneStatuses.handleZoneReadingsUpdate(self.alarmStatus.zoneReadings.list)
        postAlarmCondition = self.alarmStatus.zoneStatuses.hasTrippedZone()
        if (postAlarmCondition and not preAlarmCondition):
            self.handleNewAlarm()
        self.publishState()

    def handleTick(self):
        preTickBellState = self.bell.state
        self.bell.handleTick()
        postTickBellState = self.bell.state
        if (preTickBellState != postTickBellState):
            self.publishState()
        

    def handleNewAlarm(self):
        self.bell.handleAlarm()
        self.publishAlarm()

    def config(self, alarmConfig):
        self.bell.config(alarmConfig["bell"])
        self.zoneStatuses.config(alarmConfig["zones"])
        self.publishState()

    def publishAlarm(self):
        print('this implementation do nothing')

    def publishState(self):
        print('this implementation do nothing')
