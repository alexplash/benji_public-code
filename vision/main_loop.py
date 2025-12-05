
from vision.human_detector import HumanDetector


def vision_loop(camera):
    detector = HumanDetector(
        camera = camera
    )
    
    print("[Vision] Waiting for human detection")
    
    while True:
        human_detected = detector.wait_for_human()
        if not human_detected:
            continue
        
        
        break
    
    print("[Vision] Human detected. ending loop")
    return
        
        