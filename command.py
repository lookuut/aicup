from SmartElevator import SmartElevator

from SmartPsg import SmartPsg
from SmartElevator import SmartElevator
class ElCommand :
    
    
    COMMAND_STATE_COMPLETE = 1
    COMMAND_STATE_WAIT = 2
    COMMAND_STATE_RUN = 3

    COMMAND_WAIT = "wait"
    COMMAND_GO = "go"

    def __init__(self, purpose_value, strategy) : 
        self.state = ElCommand.COMMAND_STATE_WAIT
        self.current_value = 0
        self.purpose_value = purpose_value
        self.runnable_tick = 0
        self.type = ""
        self.strategy = strategy

    def _print(self, elevator_id) : 
        print("Command log elevator id : {elevator_id} {type} purpose value {value}".format(elevator_id = elevator_id, type = self.type , value = self.purpose_value))


class ElWaitCommand(ElCommand) :
    def __init__ (self, purpose_value, strategy) :
        ElCommand.__init__(self, purpose_value, strategy)
        self.type = "wait"


    def run(self, elevator, tick) :         
        if (tick == self.runnable_tick or self.state == ElCommand.COMMAND_STATE_COMPLETE) :#tick already was run or command complete
            return 

        self.current_value += 1
        self.runnable_tick = tick
        self.state = ElCommand.COMMAND_STATE_RUN

    def check(self, elevator) :
        if (self.state == ElCommand.COMMAND_STATE_COMPLETE) : 
            return True
        
        if (self.current_value > self.purpose_value) :
            self.state = ElCommand.COMMAND_STATE_COMPLETE
            return True
        return False


class ElFillCommand(ElCommand) : 

    def __init__ (self, purpose_value, strategy) :
        ElCommand.__init__(self, purpose_value, strategy)
        self.type = "fill"


    def run(self, elevator, tick) :         
        if (tick == self.runnable_tick or self.state == ElCommand.COMMAND_STATE_COMPLETE) :#tick already was run 
            return 

        ready_psg_count = 0
        for psg in self.strategy.passengers : 
            if ((psg.state == SmartPsg.PSG_STATE_WAIT_EL or psg.state == SmartPsg.PSG_STATE_RETURNING) and psg.has_elevator() == False and \
                psg.dest_floor in self.strategy.elevator_floors[elevator.id - 1]) :
                psg.set_elevator(elevator)
                ready_psg_count += 1

        #wait going passengers
        elevator_wait_times = []
        for psg in self.strategy.passengers :
            if psg.elevator > 0 and psg.elevator == elevator.id :
                if psg.state == SmartPsg.PSG_STATE_MOVING_TO_EL :
                    elevator_wait_times.append(SmartPsg.go_to_coordinate_time(psg.x, SmartElevator.get_elevator_x(elevator.id)))

        if len(elevator.passengers) >= self.purpose_value or (self.strategy.tick_number > 2000 and len(elevator_wait_times) == 0) :
            self.state = ElCommand.COMMAND_STATE_COMPLETE

            floor, floor_combination = SmartElevator.floors_logic(elevator.floor, elevator.passengers, self.strategy)
            for floor in floor_combination : 
                self.strategy.commands[elevator.id].append(ElGoCommand(floor, self.strategy))
                self.strategy.commands[elevator.id].append(ElWaitCommand(40, self.strategy))
        else :
            self.state = ElCommand.COMMAND_STATE_RUN
        
        self.runnable_tick = tick

    def check(self, elevator) :
        if (self.state == ElCommand.COMMAND_STATE_COMPLETE) : 
            return True
        
        if (elevator.floor == self.purpose_value) :
            self.state = ElCommand.COMMAND_STATE_COMPLETE
            return True
        return False



class ElGetPsgCommand (ElCommand) :

    def __init__ (self, purpose_value, strategy) :
        ElCommand.__init__(self, purpose_value, strategy)
        self.type = "get"
        
        self.failed_psgs = []
        self.ignored_psgs = []
        self.called_psgs = []
        self.must_exit_guys = []
        self.printed = False

    def run(self, elevator, tick) :
        
        if (tick == self.runnable_tick or self.state == ElCommand.COMMAND_STATE_COMPLETE) :#tick already was run 
            return 

        if (elevator.state == SmartElevator.EL_STATE_FILLING) :
            
            command_complete = True
            
            #first of all we need to wait when passengers go out
            stay_at_elevator_passengers = []
            for psg in elevator.passengers :
                if psg.dest_floor == elevator.floor and psg.state == SmartPsg.PSG_STATE_EXITING :
                    command_complete = False
                else : 
                    stay_at_elevator_passengers.append(psg)
            
            goto_elevator_passengers = [psg for psg in self.strategy.passengers if psg.state == SmartPsg.PSG_STATE_MOVING_TO_EL and psg.elevator == elevator.id]            
            psg_count = len(goto_elevator_passengers) + len(stay_at_elevator_passengers)

            visit_floors, max_floor, min_floor = SmartElevator.visit_floors(elevator, goto_elevator_passengers)
            
            candidates = []
            for psg in self.strategy.passengers :
                if (psg.id in self.purpose_value) : 
                    
                    if (psg.state in [SmartPsg.PSG_STATE_WAIT_EL , SmartPsg.PSG_STATE_RETURNING]) :
                        candidates.append(psg)
                        
                        if psg.id in self.failed_psgs : 
                            self.failed_psgs.remove(psg.id)
                    
                    if (psg.state in [SmartPsg.PSG_STATE_MOVING_TO_EL, SmartPsg.PSG_STATE_USING_EL, SmartPsg.PSG_STATE_MOVING_TO_FLOOR] and psg.elevator != elevator.id and psg.id not in self.failed_psgs) :
                        self.failed_psgs.append(psg.id)

            called_psgs, ignored_psgs = SmartElevator.call_passengers(elevator, psg_count, candidates, self.called_psgs, visit_floors, self.strategy.type)
            self.ignored_psgs = list(set(self.ignored_psgs + ignored_psgs))
            self.called_psgs = list(set(self.called_psgs + called_psgs))

            for psg_id in self.purpose_value :
                if (not(psg_id in self.ignored_psgs or psg_id in self.failed_psgs) and len([ p for p in elevator.passengers if p.id == psg_id]) == 0 ) :
                    command_complete = False
                    break

            if (command_complete or len(elevator.passengers) >= SmartElevator.MAX_PASSENGERS_COUNT) : 
                self.state = ElCommand.COMMAND_STATE_COMPLETE
                self.runnable_tick = tick
                return 


        self.state = ElCommand.COMMAND_STATE_RUN
        self.runnable_tick = tick

    def check(self, elevator) :
        if (self.state == ElCommand.COMMAND_STATE_COMPLETE) : 
            return True
        return False


class ElGoCommand(ElCommand) :

    def __init__ (self, purpose_value, strategy) :
        ElCommand.__init__(self, purpose_value, strategy)
        self.type = "go"

    def run(self, elevator, tick) :         
        if (tick == self.runnable_tick or self.state == ElCommand.COMMAND_STATE_COMPLETE) :#tick already was run 
            return 

        if (elevator.state == SmartElevator.EL_STATE_FILLING) :

            if (self.purpose_value == None) : 
                self.purpose_value = SmartElevator.go_next_floor(elevator, self.strategy) 
                if self.purpose_value == None :
                    raise Exception('spam', 'go command get None and go next floor is none too')
                if (self.purpose_value == None) : 
                    self.state = ElCommand.COMMAND_STATE_COMPLETE
                    self.runnable_tick = tick
                    print("Go to complete go command")
                    return
            
            elevator.go_to_floor(self.purpose_value)

        self.state = ElCommand.COMMAND_STATE_RUN
        self.runnable_tick = tick

    def check(self, elevator) :
        if (self.state == ElCommand.COMMAND_STATE_COMPLETE) : 
            return True
        
        if (elevator.floor == self.purpose_value) :
            self.state = ElCommand.COMMAND_STATE_COMPLETE
            return True
        return False
