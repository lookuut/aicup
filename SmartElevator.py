import command
import math 
import itertools


class SmartElevator :

    EL_STATE_WAITING = 0
    EL_STATE_MOVING = 1
    EL_STATE_OPENING = 2
    EL_STATE_FILLING = 3
    EL_STATE_CLOSE = 4

    EL_EMPTY_SPEED = 50
    EL_OPEN_DOOR_TIME = 100
    EL_CLOSE_DOOR_TIME = 100
    EL_LEAVE_PSG_TIME = 40

    MAX_PASSENGERS_COUNT = 20

    COORDINDATES = [-60, 60, -140, 140, -220, 220, -300, 300]

    def __init__(self, elevator):
        self.elevator = elevator
        self.appointedPsg = []
        self.x = SmartElevator.COORDINDATES[elevator.id - 1]

    def direction (dest_floor) :
        return 1 if dest_floor > self.elevator.floor else 0

    @staticmethod
    def get_elevator_x(id) :
        return SmartElevator.COORDINDATES[id - 1]        

    @staticmethod
    def clear_go_floor_time (start_floor, dest_floor, passengers) :
        if (start_floor > dest_floor) :
            return math.fabs(start_floor - dest_floor) * SmartElevator.EL_EMPTY_SPEED
        else :
            return math.fabs(start_floor - dest_floor) * SmartElevator.speed(passengers)

    @staticmethod
    def go_to_floor_time(elevator, floor) :
        time = 0
        if (elevator.state in [SmartElevator.EL_STATE_MOVING, SmartElevator.EL_STATE_CLOSE]) : 
            time += SmartElevator.clear_go_floor_time(elevator.y, elevator.next_floor, elevator.passengers)
            
            #minus exit passengers who go to dest floor
            rest_passengers = [psg for psg in elevator.passengers if psg.dest_floor != elevator.next_floor]
            time += SmartElevator.clear_go_floor_time(elevator.next_floor, floor, rest_passengers) 

            if elevator.state == SmartElevator.EL_STATE_CLOSE : 
                time += (SmartElevator.EL_CLOSE_DOOR_TIME + SmartElevator.EL_OPEN_DOOR_TIME + SmartElevator.EL_LEAVE_PSG_TIME - elevator.time_on_floor)
            if elevator.next_floor != floor : 
                time += SmartElevator.EL_OPEN_DOOR_TIME + SmartElevator.EL_CLOSE_DOOR_TIME + SmartElevator.EL_LEAVE_PSG_TIME
                    
            time += SmartElevator.EL_OPEN_DOOR_TIME
        
        elif (elevator.state in [SmartElevator.EL_STATE_FILLING, SmartElevator.EL_STATE_WAITING, SmartElevator.EL_STATE_OPENING]) :
            passengers = [psg for psg in elevator.passengers if psg.dest_floor != floor]
            time += SmartElevator.clear_go_floor_time(elevator.y, floor, passengers)
            
            if (floor != elevator.floor) :
                time += SmartElevator.EL_CLOSE_DOOR_TIME + SmartElevator.EL_OPEN_DOOR_TIME
            if (elevator.state == SmartElevator.EL_STATE_OPENING) :  #BAAAAG
                time += (SmartElevator.EL_STATE_OPENING - elevator.time_on_floor) + SmartElevator.EL_LEAVE_PSG_TIME if elevator.state == SmartElevator.EL_STATE_OPENING else 0
        return time

    @staticmethod
    def max_point_floor(elevator, _type) : 
        from SmartPsg import SmartPsg

        floors = [0,0,0,0,0,0,0,0,0,0,0]
        for psg in elevator.passengers :
            floors[psg.dest_floor] += SmartPsg.points(psg, _type)

        return floors.index(max(floors))

  
    @staticmethod
    def speed (passengers) :
        value = 1
        for psg in passengers :
            value = value * psg.weight 
        return value * SmartElevator.EL_EMPTY_SPEED

    def setPassenger(psg) :
        self.appointedPsgRefresh()
        
        #elevator already is full 
        if (len(elevator.passengers) + len (self.appointedPsg) >= SmartElevator.MAX_PASSENGERS_COUNT) : 
            return False
        #elevator can't get new psg
        elif not (elevator.state == SmartElevator.EL_STATE_WAITING or elevator.state  == elevator.EL_STATE_FILLING) : 
            return False
        #psg already in elevator or in wait state
        elif len([item for item in self.elevator.passengers if item.id  == psg.id]) > 0 or len([item for item in self.appointedPsg if item.id  == psg.id]) > 0 : 
            return False
        else : 
            psg.set_elevator(self.elevator)
            self.appointedPsg.append(psg)
            return True

    # clear elvator direction by passengers
    def defineElevatorDirection (elevator) :
        for psg in self.elevator.passengers : 
            if (psg.dest_floor > elevator.floor) :
                return 1
            if (psg.dest_floor < elevator.floor) :
                return 0 

    @staticmethod
    #call this function when elevator  not empty and state != 1
    def notEmptyElevatorLogic(elevator) :
        if len (elevator.passengers) > 0 :
            # this mean elevator go to up floors
            if (elevator.floor  <= elevator.passengers[0] ) :
                elevator.go_to_floor(SmartElevator.passengersMinDestFloor(elevator.passengers))
            else : # go to down floors
                elevator.go_to_floor(SmartElevator.passengersMaxDestFloor(elevator.passengers))

    @staticmethod
    def floors_logic(elevator_floor, passengers, strategy) :
        if len(passengers) == 0 :
            raise Exception('Fuck', 'Fuck your self')

        floors = []
        floor_passengers = {} 
        for psg in passengers : 
            if psg.dest_floor not in floors : 
                floors.append(psg.dest_floor)
            if psg.dest_floor not in floor_passengers : 
                floor_passengers[psg.dest_floor] = []
            
            floor_passengers[psg.dest_floor].append(psg)

        min_time_start_floor = None
        min_time = None
        min_time_pcombination = None
        points = 0
        for floor_combination in itertools.permutations(floors) : 
            time = 0
            start_floor = elevator_floor
            combination_passengers = passengers[:]

            for floor in floor_combination : 
                time += SmartElevator.clear_go_floor_time(start_floor, floor , combination_passengers)
                combination_passengers = [item for item in combination_passengers if item not in floor_passengers[floor]]
                start_floor = floor
                
                for psgp in floor_passengers[floor] : 
                    p = math.fabs(floor - start_floor) * 10
                    points += (p if psgp.type == strategy.type else p * 2)
           
            if min_time == None : 
                min_time = time
                min_time_start_floor = floor_combination[0]
                min_time_pcombination = floor_combination[:]
            elif min_time > time :
                min_time = time
                min_time_start_floor = floor_combination[0]
                min_time_pcombination = floor_combination[:]

        return min_time_start_floor , min_time_pcombination

    @staticmethod
    def call_passengers(elevator, psg_count, candidates, g_called_psgs, floors, type) : 
        called_psgs = []
        ignored_psgs = []
        for psg in sorted(candidates, key=lambda psg: ((3 if psg.type != type else 1 ) + ( 1 if psg.floor < elevator.floor else 0 ) + (2 if floors[psg.floor] > 0 else 0) ) , reverse = True) :
            
            if ((len(called_psgs) + psg_count < SmartElevator.MAX_PASSENGERS_COUNT and \
                (\
                    floors[psg.dest_floor] > 0 or (math.fabs(psg.dest_floor - psg.from_floor) >= 3 and psg.type != type) or\
                    math.fabs(psg.dest_floor - psg.from_floor) > 3 \
                )) or (
                    psg_count < 3 and len(candidates) < 8 and 
                    (floors[psg.dest_floor] > 0 or (math.fabs(psg.dest_floor - psg.from_floor) >= 2 and psg.type != type) or\
                    math.fabs(psg.dest_floor - psg.from_floor) >= 3) \
                )\
                ) :  
                psg.set_elevator(elevator)
                
                called_psgs.append(psg.id)
            elif psg.id not in g_called_psgs :
                ignored_psgs.append(psg.id)

        return called_psgs , ignored_psgs


    @staticmethod 
    def floors_to_visit(passengers) :
        my_floors = [0,0,0,0,0,0,0,0,0,0]
        max_floor = 0
        min_floor = 9

        for passenger in passengers :
            my_floors[passenger.dest_floor] += 1

            if max_floor < passenger.dest_floor : 
                max_floor = passenger.dest_floor

            if min_floor > passenger.dest_floor : 
                min_floor = passenger.dest_floor

        return my_floors , max_floor, min_floor


    @staticmethod 
    def visit_floors(elevator, going_to_elevator_psgs) :
        my_floors = [0,0,0,0,0,0,0,0,0,0]
        max_floor = 0
        min_floor = 9

        for passenger in elevator.passengers + going_to_elevator_psgs :
            my_floors[passenger.dest_floor] += 1

            if max_floor < passenger.dest_floor : 
                max_floor = passenger.dest_floor

            if min_floor > passenger.dest_floor : 
                min_floor = passenger.dest_floor

        return my_floors , max_floor, min_floor

    @staticmethod
    def go_next_floor (elevator, strategy) :
        if len (elevator.passengers) > 0 :
            # this mean elevator go to up floors
            floor, _ = SmartElevator.floors_logic(elevator.floor, elevator.passengers, strategy)
            return floor
    @staticmethod
    def passengersMinDestFloor(passengers) :
        min_dest_floor = 9
        for psg in passengers:
            if (min_dest_floor > psg.dest_floor and psg.has_elevator()) : 
                min_dest_floor =  psg.dest_floor
        return min_dest_floor

    @staticmethod
    def passengersMaxDestFloor(passengers) :
        max_dest_floor = 1
        for psg in passengers:
            if (max_dest_floor < psg.dest_floor and psg.has_elevator()) : 
                max_dest_floor =  psg.dest_floor
        return max_dest_floor


    @staticmethod
    def free (elevator) :
        return True if elevator.state == SmartElevator.EL_STATE_FILLING and len(elevator.passengers) < SmartElevator.MAX_PASSENGERS_COUNT else False

    """ distation to passenger """
    def psgDist(psg) : 
        if psg.state == ElCommand.PSG_STATE_RETURNING: 
            x = psg.x
        else :
            x = 80
        return math.fabs(psg.x - SmartElevator.get_elevator_x(self.elevator.id))

    def __getattr__(self, attr) :
        return self.elevator.__getattribute__(attr)

