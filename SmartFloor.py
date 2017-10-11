

import math
import operator

from SmartPsg import SmartPsg
from SmartElevator import SmartElevator

class SmartFloor :

	def __init__ (self, floor, strategy) : 
		self.floor = floor
		self.passengers = {}
		
		self.sorted_passengers = []
		self.strategy = strategy

	def refresh (self) :
		self.sorted_passengers = sorted(self.passengers.values(), key = operator.attrgetter('time'))

	def addPsg (self, psg) :
		self.passengers.update({psg.id : psg})
	
	def removePsg(self, psg_id) :
		self.passengers.pop(psg_id, None)

	def removePsgList(self, passengers) :
		for psg_id in passengers :
			self.removePsg(psg_id)
		
		self.refresh()

	def is_have_psg (self, id) :
		return id in self.passengers

	def is_have_passengers (self, time) :
		if len(self.passengers) == 0 : 
			return False

		return True if time < self.sorted_passengers[len(self.sorted_passengers) - 1].time + SmartPsg.PSG_FLOOR_TIMEOUT else False

	def points (self, time, x, enemy_elevators, tick_number, max_wt) : 

		floors_passengers = []
		psg_count = 0
		wait_time = 0
		max_wait_time = 0
		for psg in self.sorted_passengers : 

			psg_go_to_elevator_time = math.ceil((math.fabs(x - psg.x))/ float(2)) 

			if (time + psg_go_to_elevator_time < psg.time + SmartPsg.PSG_FLOOR_TIMEOUT and (psg.time - time) <= max_wt and (tick_number > 2000 and self.floor > 1 or tick_number < 2000) ) :
				is_my_psg = True
				
				wait_time = 0 if (psg.time - time) < 0 else (psg.time - time)
				
				for elevator in enemy_elevators :

					next_floor = elevator.floor if elevator.next_floor == -1 and elevator.state in [SmartElevator.EL_STATE_FILLING, SmartElevator.EL_STATE_WAITING]  else elevator.next_floor

					if next_floor != self.floor : 
						continue
	
					if math.fabs(x - psg.x) > math.fabs(SmartElevator.get_elevator_x(elevator.id) - psg.x) and \
						time > SmartElevator.go_to_floor_time(elevator, self.floor) + tick_number :
						is_my_psg = False

					if time > SmartElevator.go_to_floor_time(elevator, self.floor) + tick_number and \
						time > psg.time : 
						is_my_psg = False
				
				if (is_my_psg) :
					floors_passengers.append(psg.id)
					psg_count += (1 if psg.type == self.strategy.type else 2)

					if psg.type != self.strategy.type and  wait_time < SmartPsg.PSG_ENEMY_CAPTURE_TIMEOUT :
						wait_time += SmartPsg.PSG_ENEMY_CAPTURE_TIMEOUT - wait_time 
					
					if max_wait_time < wait_time : 
						max_wait_time = wait_time
		
		return psg_count , max_wait_time, floors_passengers

	def _print(self) : 
		print("floor {floor}".format(floor = self.floor))
		for psg in self.sorted_passengers : 
			print("time {time} x {x} and id {id} ".format(time = psg.time, x = psg.x, id = psg.id))
		print("end floor")
