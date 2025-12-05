
from vision.main_loop import vision_loop
from patrol.movement.movement_loop import Movement


def patrol_loop(motors, sonar, camera):
    
    movement = Movement(motors = motors, sonar = sonar)
    movement.start()
        
    vision_loop(camera)
    movement.human_detected_trigger()
    motors.stop()
    
    print("[Patrol] Human detected — exiting patrol mode")
    return
    

