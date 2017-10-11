
from SmartElevator import SmartElevator

import math



class PotentialPassenger :

    def __init__(self, time, x, floor, id, psg, type) :
        self.time = time
        self.x = x
        self.floor = floor
        self.id = id
        self.psg = psg
        self.type = type

class SmartPsg : 

    PSG_STATE_WAIT_EL = 1
    PSG_STATE_MOVING_TO_EL = 2
    PSG_STATE_RETURNING = 3
    PSG_STATE_MOVING_TO_FLOOR = 4
    PSG_STATE_USING_EL = 5
    PSG_STATE_EXITING = 6

    PSG_FLOOR_DOWN_SPEED = 100 
    PSG_FLOOR_UP_SPEED = 200 
    PSG_FLOOR_TIMEOUT = 500
    
    FIRST_PLAYER_X = -20
    SECOND_PLAYER_X = 20

    PSG_EXIT_TIMEOUT = 40 
    PSG_ENEMY_CAPTURE_TIMEOUT = 40
    PSG_MAX_WAIT_TIME = 500
    PSG_FLOOR_SPEED = 2

    def __init__ (self, psg, type, strategy) : 
        self.init(psg, type, strategy)
        
    def init (self, psg, type, strategy) :
        self.psg = psg
        self.type = type 
        self.strategy = strategy

        self.to_be_available_time = 0 #time when passenger will be in wait state
        self.to_be_available_x = SmartPsg.FIRST_PLAYER_X if self.psg.type == Strategy.FIRST_PLAYER else SmartPsg.SECOND_PLAYER_X # x coordinate when passenger will be in wait state
        self.to_stairs_time = self.psg.time_to_away #time when passenger go to stairs
        self.to_be_available_floor = self.psg.dest_floor #floor when passenger will be in wait time

        self.update()  

    def update (self) : 
        if (self.psg.state == SmartPsg.PSG_STATE_WAIT_EL or self.psg.state == SmartPsg.PSG_STATE_RETURNING) :
            self.to_be_available_floor = self.psg.from_floor
            self.to_be_available_x = self.psg.x

        if (self.psg.state == SmartPsg.PSG_STATE_MOVING_TO_FLOOR) : 
            self.to_be_available_time = math.fabs(self.psg.dest_floor - self.psg.y) * self.floorSpeed() + SmartPsg.PSG_FLOOR_TIMEOUT
            self.to_stairs_time = self.to_be_available_time + SmartPsg.PSG_MAX_WAIT_TIME

        if (self.psg.state == SmartPsg.PSG_STATE_EXITING) :
            self.to_be_available_floor = self.psg.dest_floor
            self.to_be_available_time = SmartPsg.PSG_FLOOR_TIMEOUT + (SmartPsg.PSG_EXIT_TIMEOUT - self.strategy.getElevator(self.psg.elevator).time_on_floor) #time when passenger will be in wait state
            self.to_stairs_time = self.to_be_available_time + SmartPsg.PSG_MAX_WAIT_TIME

        if (self.psg.state == SmartPsg.PSG_STATE_MOVING_TO_EL or self.psg.state == SmartPsg.PSG_STATE_USING_EL) : 
            height = math.fabs(self.psg.y -  self.psg.dest_floor)
            elevator = self.strategy.getElevator(self.psg.elevator)
            x = 20 #elevator.x in future will available
            el_dest_time = (SmartElevator.EL_EMPTY_SPEED if self.psg.dest_floor < self.psg.y else elevator.speed(elevator.passengers)) * height
            time_to_elevator = (self.psg.x - x) / SmartPsg.PSG_FLOOR_SPEED
            self.to_be_available_time = SmartPsg.PSG_FLOOR_TIMEOUT + SmartPsg.PSG_EXIT_TIMEOUT + time_to_elevator + el_dest_time
            self.to_stairs_time = self.to_be_available_time + SmartPsg.PSG_MAX_WAIT_TIME

        self.to_be_available_time += self.strategy.tick_number
        self.to_stairs_time += self.strategy.tick_number

    @staticmethod
    def getAvailableTime (psg, strategy) :
        to_be_available_time = 0
        
        if (psg.state == SmartPsg.PSG_STATE_MOVING_TO_FLOOR) : 
            to_be_available_time = math.ceil(math.fabs(psg.dest_floor - psg.y) * SmartPsg.floorSpeed(psg)) + SmartPsg.PSG_FLOOR_TIMEOUT

        if (psg.state == SmartPsg.PSG_STATE_EXITING) :
            to_be_available_time = SmartPsg.PSG_FLOOR_TIMEOUT + (SmartPsg.PSG_EXIT_TIMEOUT + SmartElevator.EL_OPEN_DOOR_TIME - strategy.getElevator(psg.elevator).time_on_floor) #time when passenger will be in wait state
            

        if (psg.state == SmartPsg.PSG_STATE_MOVING_TO_EL or psg.state == SmartPsg.PSG_STATE_USING_EL) : 
            height = math.fabs(psg.y -  psg.dest_floor)
            elevator = strategy.getElevator(psg.elevator)
            x = 20 #elevator.x in future will available
            el_dest_time = (SmartElevator.EL_EMPTY_SPEED if psg.dest_floor < psg.y else elevator.speed(elevator.passengers)) * height
            time_to_elevator = (psg.x - x) / SmartPsg.PSG_FLOOR_SPEED
            to_be_available_time = SmartPsg.PSG_FLOOR_TIMEOUT + SmartPsg.PSG_EXIT_TIMEOUT + time_to_elevator + el_dest_time

        return to_be_available_time

    @staticmethod
    def go_floor_time(start_floor, end_floor) : 
        return abs(end_floor - start_floor) * (SmartPsg.PSG_FLOOR_UP_SPEED if end_floor > start_floor else SmartPsg.PSG_FLOOR_DOWN_SPEED)

    @staticmethod
    def floorSpeed (psg) :
        return SmartPsg.PSG_FLOOR_UP_SPEED if psg.dest_floor > psg.floor  else SmartPsg.PSG_FLOOR_DOWN_SPEED
    

    @staticmethod
    def floorSpeed (psg) :
        return SmartPsg.PSG_FLOOR_UP_SPEED if psg.dest_floor > psg.floor  else SmartPsg.PSG_FLOOR_DOWN_SPEED
    
    @staticmethod
    def points (psg, type) : 
        return math.fabs(psg.from_floor - psg.dest_floor) * 10 * (2 if psg.type != type else 1)


    @staticmethod
    def go_to_coordinate_time(dest_x, start_x) : 
        return math.ceil((math.fabs(dest_x - start_x))/float(SmartPsg.PSG_FLOOR_SPEED)) 

    def isEnemyPsg (self) : 
        return self.psg.type != self.type

    def set_elevator(self, elevator) :
        self.psg.set_elevator(elevator)

    def has_elevator(self) : 
        return self.psg.has_elevator()

    #future points of passenger
    def get_future_points (self) :
        floor = 4 #avg floors
        if self.psg.state in [ SmartPsg.PSG_STATE_WAIT_EL, SmartPsg.PSG_STATE_RETURNING] :
            floor = math.fabs(self.psg.floor - self.psg.dest_floor)

        return 10 * (2 if self.isEnemyPsg() else 1) * floor

    def __getattr__(self, attr) :
        return self.psg.__getattribute__(attr)
    

