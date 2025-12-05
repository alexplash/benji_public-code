
import time
import random
import threading


movement_options = ["forward", "left", "right"]
long_duration_range = (2.0, 6.0)
lat_duration_range = (1.0, 2.0)
MAX_DIST_MM = 200.00

ACTION_MAP = {
    "forward": lambda motors: motors.forward(),
    "left": lambda motors: motors.turnLeft(),
    "right": lambda motors: motors.turnRight(),
}



class Movement:
    
    def __init__(self, motors, sonar):
        self.motors = motors
        self.sonar = sonar
        self.human_detected = False
        self.th = None
    
    def start(self):
        self.th = threading.Thread(target = self.movement_loop, daemon = True)
        self.th.start()
    
    def human_detected_trigger(self):
        self.human_detected = True
        self.th = None
    
    def movement_loop(self):
        prevented_action = None
        
        while not self.human_detected:
            
            allowed_actions = [action for action in movement_options if action != prevented_action]
            prevented_action = None
            
            action = random.choice(allowed_actions)
            if action == "forward":
                duration = random.uniform(long_duration_range[0], long_duration_range[1])
            else:
                duration = random.uniform(lat_duration_range[0], lat_duration_range[1])
            
            print(f"[Patrol] Moving {action} for {duration:.1f}s")
            
            ACTION_MAP[action](self.motors)
            
            start_time = time.time()
            while time.time() - start_time < duration:
                if self.human_detected:
                    break
                
                dist_mm = self.sonar.getDistance()
                if (0 <= dist_mm <= MAX_DIST_MM) and (action == "forward"):
                    prevented_action = action
                    break
                
                time.sleep(0.05)
            
            self.motors.stop()
            time.sleep(0.1)
            
            
        print("[Patrol] Movement thread stopped.")
    
