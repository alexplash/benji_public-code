
import cv2
import time
import numpy as np
from ultralytics import YOLO
from motors_servos.ros_robot_controller_sdk import Board

class HumanDetector:
    
    def __init__(
        self,
        camera,
        model_name = "yolov8n.pt",
        conf_threshold = 0.5, # minimum confidence threshold to trigger a human detection
        min_consecutive_frames = 3, # how many frames in a row should show a person
        poll_interval = 0.2, # delay between frame polls (seconds between camera snapshots)
        input_size = 256 # YOLO inference size (e.g., 256 for speed on Pi); 256 x 256 pixel images
    ):
        self.board = Board()
        self.pan = 2
        self.tilt = 1
        self.center_pos = 1500
        self.duration_servo = 0.5
        self.center_interval = 3.0
        
        self.camera = camera
        self.model_name = model_name
        self.conf_threshold = conf_threshold
        self.min_consecutive_frames = min_consecutive_frames
        self.poll_interval = poll_interval
        self.input_size = input_size
        
        self.model = YOLO(self.model_name)
        
        self.person_class_id = 0 # class index for 'person' in YOLO
    
    def detect_human(self, frame: np.ndarray):
        
        # run YOLO on a single frame and return a list of person detections:
        # [(x1, y1, x2, y2, confidence), ...]
        
        if frame is None:
            return []
        
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        results = self.model(
            rgb,
            imgsz = self.input_size,
            verbose = False
        )
        
        detections = []
        if not results:
            return detections
        
        result = results[0]
        if result.boxes is None:
            return detections
        
        # for each image passed into the YOLO model, it detect many different things in the image
        # each "box" represents an item of interest in the image
        # so there may be one box for a tree, one box for a chair, one for a human, etc.
        for box in result.boxes:
            # every box has only one classification id, and it is stored in a tensor 'cls' with one item
            cls_id = int(box.cls[0])
            # every box has only one confidence score, and it is stored in a tensor 'conf' with one item
            conf = float(box.conf[0])
            
            if cls_id == self.person_class_id and conf >= self.conf_threshold:
                # these are basically the "corners" of the box
                # (x1, y1) are the pixel coordinates of the top left corner of the box
                # (x2, y2) are the pixel coordinates of the bottom right corner of the box
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                detections.append((int(x1), int(y1), int(x2), int(y2), conf))
        
        return detections
    
    def _center_camera(self):
        self.board.pwm_servo_set_position(self.duration_servo, [[self.pan, self.center_pos], [self.tilt, self.center_pos]])
        
    
    def wait_for_human(
        self
    ):
        print("[Vision] starting human detection loop...")
        self.camera.camera_open()
        
        consecutive_frames = 0
        
        last_center_time = time.time()
        
        human_detected = False
        
        try:
            self._center_camera()
            
            while not human_detected:
                frame = self.camera.frame
                if frame is None:
                    time.sleep(self.poll_interval)
                    continue
                
                detections = self.detect_human(frame)
                
                if detections:
                    consecutive_frames += 1
                else:
                    consecutive_frames = 0
                
                if consecutive_frames >= self.min_consecutive_frames:
                    print("[Vision] human detection confirmed")
                    human_detected = True
                
                if time.time() - last_center_time >= self.center_interval:
                    self._center_camera()
                    last_center_time = time.time()
                
                time.sleep(self.poll_interval)
        
        finally:
            self._center_camera()
            self.camera.camera_close()
            return human_detected
        
        
        
    