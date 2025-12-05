
from dotenv import load_dotenv
import os
load_dotenv()

from chat.main_chat import chat_loop
from patrol.main_loop import patrol_loop
from db.database import init_db

import motors_servos.mecanum as mecanum
import sonar.Sonar as Sonar
from vision.camera import Camera

from typing import Literal

RobotMode = Literal["patrol_mode", "chat_mode"]
mode: RobotMode = "patrol_mode"

def set_mode(new_mode: RobotMode):
    global mode
    mode = new_mode


if __name__ == "__main__":
    CHAT_DEBUG = os.getenv("CHAT_DEBUG")
    
    print("Starting robot ...")
    print("Initializing DB")
    init_db()
    
    motors = mecanum.MecanumChassis()
    sonar = Sonar.Sonar()
    camera = Camera()
    
    try:
        while True:
            if CHAT_DEBUG:
                chat_loop(camera, motors)
            else:
                if mode == "chat_mode":
                    chat_loop(camera, motors)
                    print("[Main] chat ended => entering patrol mode")
                    set_mode("patrol_mode")
                    
                elif mode == "patrol_mode":
                    patrol_loop(motors, sonar, camera)
                    print("[Main] human detected => entering chat mode")
                    set_mode("chat_mode")
    except KeyboardInterrupt:
        print("\n[Main] Ctrl+C detected - shutting down robot safely...")
    except Exception as e:
        print(f"\n[Main] Unexpected error: {e}")
    finally:
        motors.stop()
        camera.camera_close()

    
    
            
        