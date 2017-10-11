from base_strategy import BaseStrategy

import math
from command import ElCommand
from command import ElGoCommand
from command import ElWaitCommand
from command import ElFillCommand
from command import ElGetPsgCommand

from SmartPsg import SmartPsg
from SmartElevator import SmartElevator
from SmartFloor import SmartFloor
from SmartPsg import PotentialPassenger

# [99, 100, 51, 52, 64, 128, 8, 7]
#[182, 181, 29, 33, 173, 174]
#[99, 100, 51, 52, 64, 128, 8, 7]
#177563022614 - 
class Strategy(BaseStrategy) :

    ELEVATORS_COUNT = 4
    MAX_FLOOR = 9
    MAX_PASSENGER_COUNT = 100
    tick_number = 1

    FIRST_PLAYER = "FIRST_PLAYER"
    SECOND_PLAYER = "SECOND_PLAYER"

    MAX_TICK_NUMBER = 7200

    def __init__(self, debug, type):
        self.debug = debug.log
        self.type = type
        self.my_elevators = []
        self.enemy_elevators = []

        self.floor_elevators = {}
        self.elevator_floors = [[9,7],[9,7],[8,6],[8,6],[9,5,7],[9,5,7],[5,8,4],[5,8,4]]
        self.floors = {}
        self.tick_number = 1
        
        self.passengers = []
        self.commands = {}

        self.psg_floor_count = [0] * 200

        index = 1 if self.type == Strategy.FIRST_PLAYER else 0
        for i in range (1, 5) :
            self.commands[2 * i - index] = [ElFillCommand(SmartElevator.MAX_PASSENGERS_COUNT ,self)]

        for floor in range (1,Strategy.MAX_FLOOR + 1) : 
            self.floors[floor] = SmartFloor(floor, self)
        
        index = 1
        for id in range (1, Strategy.MAX_PASSENGER_COUNT + 1) :
            p_psg = PotentialPassenger(id * 20 + 1, -20, 1, index, None, Strategy.FIRST_PLAYER )
            self.floors[1].addPsg(p_psg)
            index += 1
            
            p_psg = PotentialPassenger(id * 20 + 1, 20, 1, index, None, Strategy.SECOND_PLAYER)
            self.floors[1].addPsg(p_psg)
            index += 1

        self.floors[1].refresh()

        debug_string = "version 1.1.6 my side " + self.type
        self.debug(debug_string)

    def getElevator (self, elevator_id) :
        elevator_id = elevator_id if isinstance( elevator_id , ( int, long ) ) else elevator_id.id
        index = int(math.ceil(elevator_id / float(2))) - 1

        if self.type == Strategy.FIRST_PLAYER : 
            if elevator_id % 2 == 0 :
                return self.enemy_elevators[index]
            else:
                return self.my_elevators[index]
        else :
            if elevator_id % 2 == 0 :
                return self.my_elevators[index]
            else:
                return self.enemy_elevators[index]

    def updateFloors (self) :
        
        refreshed_floors = {}
        
        for psg in self.passengers :
            if psg.state in [SmartPsg.PSG_STATE_USING_EL , SmartPsg.PSG_STATE_MOVING_TO_FLOOR, SmartPsg.PSG_STATE_MOVING_TO_EL]  and self.floors[psg.from_floor].is_have_psg(psg.id) :
                #self.floors[psg.from_floor].removePsg(psg.id)
                refreshed_floors[psg.from_floor] = True
        

        states = [SmartPsg.PSG_STATE_WAIT_EL , SmartPsg.PSG_STATE_MOVING_TO_EL, SmartPsg.PSG_STATE_RETURNING]

        for psg in self.passengers :
            floor = psg.dest_floor 
            if psg.state in states and psg.time_to_away == 0 and  (psg.x != SmartElevator.get_elevator_x(psg.elevator) if (psg.elevator > 0) else True) and \
                self.floors[floor].is_have_psg(psg.id) == False:
                time = SmartPsg.go_floor_time(psg.floor, psg.dest_floor) + SmartPsg.PSG_FLOOR_TIMEOUT  + 2
                self.floors[floor].addPsg(PotentialPassenger(time + self.tick_number, -20 if psg.type == Strategy.FIRST_PLAYER else 20, floor, psg.id, psg, psg.type)) 
                self.psg_floor_count[psg.id - 1] += 2
                refreshed_floors[floor] = True
 
        states = [SmartPsg.PSG_STATE_EXITING]
        
        for psg in self.passengers :
            floor = psg.floor
            if psg.state in states and self.floors[floor].is_have_psg(psg.id) == False :
                time = SmartPsg.getAvailableTime(psg, self)  + 1 + self.tick_number
                self.floors[floor].addPsg(PotentialPassenger(time, -20 if psg.type == Strategy.FIRST_PLAYER else 20, floor, psg.id, psg, psg.type)) 
                self.psg_floor_count[psg.id - 1] += 2
                refreshed_floors[floor] = True
        
        if len(refreshed_floors) > 0 : 
            for floor , value in refreshed_floors.iteritems() :
                self.floors[floor].refresh()
                                
    def logic (self, logic_elevator_id = None) : 
        #### elevators logic
        
        point_to_wt = {}
        points = {}
        wait_times = {}
        dest_times = {}
        elevator_passengers = {}

        for elevator in self.my_elevators : 
            floors_points = [0] * 10
            floors_wait_time = [0] * 10
            floors_dest_time = [0] * 10
            floors_point_to_wt = [0] * 10
            floors_passengers = [[] for i in range(10)]

            visit_floors = []
            min_time_pcombination = []
            source_floor = 0
           
            go_with_el_passengers = []
            for psg in elevator.passengers : 
                if not(psg.dest_floor == elevator.floor and psg.state == SmartPsg.PSG_STATE_EXITING) : 
                    go_with_el_passengers.append(psg)
            
            actual_psg_count = len(go_with_el_passengers)

            if actual_psg_count > 0 : 
                source_floor, min_time_pcombination = SmartElevator.floors_logic(elevator.floor, elevator.passengers, self)     
                visit_floors,_,_ = SmartElevator.floors_to_visit(go_with_el_passengers)

            
            for floor_ , floor in self.floors.iteritems() :
                
                max_wait_time = 0
                psg_min_count = -1

                if (actual_psg_count <= 15 and actual_psg_count > 10 and (floor_ - elevator.floor) <= 2 and floor_ in visit_floors) :
                    max_wait_time = 40
                    psg_min_count = 8

                if (actual_psg_count > 15 and  (floor_ - elevator.floor) <= 2 and floor_ in visit_floors and floor_ < source_floor) :
                    max_wait_time = 40
                    psg_min_count = 10                    

                if (actual_psg_count < 15 and actual_psg_count >= 10 and (floor_ in min_time_pcombination)) : 
                    max_wait_time = 40
                    psg_min_count = 10                    

                if (actual_psg_count <= 10 and floor_ in min_time_pcombination ) : 
                    max_wait_time = 200
                    
                if (actual_psg_count <= 10 and floor_ not in min_time_pcombination ) : 
                    max_wait_time = 150
                    psg_min_count = 5

                if (actual_psg_count <= 5) :
                    max_wait_time = 300
                    psg_min_count = 5

                if (len(go_with_el_passengers) == 0) :
                    max_wait_time = 300
                    psg_min_count = 1

                if (max_wait_time > 0) : 

                    dest_time = SmartElevator.go_to_floor_time(elevator, floor_)
                    time = dest_time + self.tick_number
                    


                    if (floor.is_have_passengers(time)) :
                        is_print = False
                        psg_count, wait_time, call_passengers = floor.points(time, SmartElevator.get_elevator_x(elevator.id), self.enemy_elevators, self.tick_number, max_wait_time)
                        
                        
                        if (psg_count < psg_min_count) : 
                            continue

                        psg_count = psg_count + ( visit_floors[floor_] if floor_ in min_time_pcombination else 0 )
                        wt = wait_time + (0 if floor_ in min_time_pcombination else dest_time) + (SmartElevator.EL_OPEN_DOOR_TIME if elevator.floor != floor_ else 0)
                        p_to_w = (psg_count / float(wt)) if wt > 0 else (1 if psg_count > 0 else 0)

                        floors_point_to_wt[floor_] = p_to_w
                        floors_points[floor_] = psg_count 
                        floors_wait_time[floor_] = wait_time + SmartElevator.EL_OPEN_DOOR_TIME
                        floors_dest_time[floor_] = dest_time
                        floors_passengers[floor_] = call_passengers
                    
            point_to_wt[elevator.id] = floors_point_to_wt
            points[elevator.id] = floors_points
            wait_times[elevator.id] = floors_wait_time
            dest_times[elevator.id] = floors_dest_time
            elevator_passengers[elevator.id] = floors_passengers
       


        max_point_wt = 0
        max_choosen_floors = {}
        max_choosen_floor_wait_time = {}

        for el in self.my_elevators :
            p_wt = max(point_to_wt[el.id]) 
            
            choosen_floors_wait_times = {el.id : wait_times[el.id] [ point_to_wt[el.id].index(p_wt) ] }
            choosen_floors = {el.id : point_to_wt[el.id].index(p_wt) } 
            out_floors = [point_to_wt[el.id].index(p_wt)]
            choosen_els = [el.id]
            
            for elevator_id, el_points in points.iteritems() : 
                
                max_elevator_p_wt = 0
                max_elevator_p_wt_floor = 0
                if (elevator_id not in choosen_els) :  
                    for floor, point in enumerate(el_points) :     
                        if max_elevator_p_wt < point_to_wt[elevator_id][floor] and \
                            floor not in out_floors : 
                            max_elevator_p_wt = point_to_wt[elevator_id][floor]
                            max_elevator_p_wt_floor = floor

                    p_wt += max_elevator_p_wt
                    out_floors.append(max_elevator_p_wt_floor)

                    choosen_floors[elevator_id] = max_elevator_p_wt_floor
                    choosen_floors_wait_times[elevator_id] = wait_times[elevator_id][max_elevator_p_wt_floor]

            if (p_wt > max_point_wt) : 
                max_point_wt = p_wt
                max_choosen_floors = choosen_floors
                max_choosen_floor_wait_time = choosen_floors_wait_times

        for elevator in self.my_elevators : 

            if (((logic_elevator_id == None and elevator.state == SmartElevator.EL_STATE_FILLING) or logic_elevator_id == elevator.id) ) :
                        
                if (elevator.id not in max_choosen_floors or max_choosen_floors[elevator.id] == 0) :
                    next_floor = SmartElevator.go_next_floor(elevator, self)
                    if (next_floor != None) :
                        self.commands[elevator.id].append(ElGoCommand(next_floor, self))
                        self.commands[elevator.id].append(ElWaitCommand(40, self))
                        self.debug("Elevator {id}  go to floor {floor} to leave psgs".format(id = elevator.id, floor = next_floor))
                    else :
                        self.commands[elevator.id].append(ElWaitCommand(10, self))
                        self.debug("No strategy for {id}".format(id = elevator.id))
                    
                elif (elevator.floor == max_choosen_floors[elevator.id]) : 
                    
                    if (len(elevator.passengers) > 0 and self.tick_number + max_choosen_floor_wait_time[elevator.id] +  SmartElevator.EL_CLOSE_DOOR_TIME + SmartElevator.EL_OPEN_DOOR_TIME + SmartPsg.PSG_EXIT_TIMEOUT > Strategy.MAX_TICK_NUMBER) : 
                        self.commands[elevator.id].append(ElGoCommand(SmartElevator.max_point_floor(elevator, self.type), self))
                        self.commands[elevator.id].append(ElWaitCommand(40, self))
                    else :
                        self.commands[elevator.id].append(ElGetPsgCommand(elevator_passengers[elevator.id][elevator.floor] , self) ) 
                        self.floors[elevator.floor].removePsgList(elevator_passengers[elevator.id][elevator.floor])
                        self.debug("Elevator {id} stay at floor {floor} leave psgs and if exists wait psgs {psgs}".format(id = elevator.id, floor = elevator.floor, psgs = elevator_passengers[elevator.id][elevator.floor]))
                else :
                    
                    wait_time = SmartElevator.EL_CLOSE_DOOR_TIME + max_choosen_floor_wait_time[elevator.id]

                    if (len(elevator.passengers) > 0 and self.tick_number + SmartElevator.go_to_floor_time(elevator, max_choosen_floors[elevator.id]) + wait_time +  SmartElevator.EL_CLOSE_DOOR_TIME + SmartElevator.EL_OPEN_DOOR_TIME + SmartPsg.PSG_EXIT_TIMEOUT > Strategy.MAX_TICK_NUMBER) : 
                        self.commands[elevator.id].append(ElGoCommand(SmartElevator.max_point_floor(elevator, self.type), self))
                        self.commands[elevator.id].append(ElWaitCommand(40, self))
                    else :
                        self.commands[elevator.id].append(ElGoCommand(max_choosen_floors[elevator.id], self))
                        self.commands[elevator.id].append(ElGetPsgCommand(elevator_passengers[elevator.id][max_choosen_floors[elevator.id]] , self)) 
                        self.floors[max_choosen_floors[elevator.id]].removePsgList(elevator_passengers[elevator.id][max_choosen_floors[elevator.id]])
                        self.debug("Elevator {id} go to floor {floor} and wait psgs {psgs}".format(id = elevator.id, floor = max_choosen_floors[elevator.id], psgs = elevator_passengers[elevator.id][max_choosen_floors[elevator.id]]))
                        
    def run_commands(self) :
        for elevator in self.my_elevators : 
                elevator_commands = self.commands[elevator.id]           
                
                if (len(elevator_commands) > 0) : 
                    command = elevator_commands[0]
                    
                    command.run(elevator, self.tick_number)

                    if command.check(elevator) : 
                        elevator_commands.remove(command)
                        
    

    def on_tick(self, my_elevators, my_passengers, enemy_elevators, enemy_passengers) :

        self.my_elevators = my_elevators
        self.enemy_elevators = enemy_elevators
        self.passengers =  enemy_passengers + my_passengers
        
        self.updateFloors()    
        self.run_commands()

        for elevator in self.my_elevators : 
            if elevator.state == SmartElevator.EL_STATE_FILLING and len(self.commands[elevator.id]) == 0 :
                self.logic(elevator.id)
       
        self.run_commands()
        self.tick_number += 1
