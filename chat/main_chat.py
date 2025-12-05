
from dotenv import load_dotenv
load_dotenv()

from audio.mic_listener import listen_for_human_turn
from audio.pending_sound import PendingSoundPlayer
from audio.robot_speech import RobotSpeech
from ai.whisper_client import transcribe_audio
from ai.gpt_client import generate_reply
from ai.tts_client import synthesize_speech
from db.conversation_history.conversation_history import add_to_history, get_history_as_string
from db.user_profile.user_profile import get_user_profile, update_user_profile
from chat.intro import intro_loop
from rl.rl_trainer import RLTrainer
import time
import cv2
import base64

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")
    
ACTION_MAP = {
    "forward": lambda motors: motors.forward(),
    "turn_left": lambda motors: motors.turnLeft(),
    "turn_right": lambda motors: motors.turnRight(),
    "backward": lambda motors: motors.backward()
}


def chat_loop(camera, motors):
    
    print("[Chat] Starting chatbot loop...")
    pending_player = PendingSoundPlayer()
    robot_speech = RobotSpeech()
    interrupted_audio_path = None
    
    # determine who is speaking
    user_id, username = intro_loop()
    if not user_id:
        return
    else:
        print(f"[Intro] Confirmed User => (user_id: {user_id}, username: {username})")
    
    rl_trainer = RLTrainer(user_id = user_id)
    selected_traits = rl_trainer.select_traits()
    
    opening_line = f"Hello there {username}! What do you wish to talk about?"
    opening_audio_path = synthesize_speech(opening_line)
    robot_speech.uninterruptible_audio(opening_audio_path)
    
    add_to_history(user_id, "Benji", opening_line)
    
    while True:
        should_end_chat = False
        
        if interrupted_audio_path:
            print("[Chat] Using interrupt audio instead of waiting for next human turn")
            audio_path = interrupted_audio_path
            interrupted_audio_path = None
            is_interrupted_turn = True
        else:
            print("[Chat] Listening for human speech...")
            audio_path = listen_for_human_turn()
            is_interrupted_turn = False
        
        if audio_path is None:
            print("[Chat] No human speech detected. Exiting chat mode.")
            
            ending_line = f"Alright, I'm heading back now {username}. Come talk to me again anytime!"
            ending_audio_path = synthesize_speech(ending_line)
            robot_speech.uninterruptible_audio(ending_audio_path)
            
            break
        
        print("[Chat] Transcribing...")
        pending_player.start()
        text = transcribe_audio(audio_path)
        print("Human said:", text)
        
        rl_trainer.add_user_turn_data(text, is_interrupted_turn)
        
        print("[Chat] Generating reply...")
        history = get_history_as_string(user_id)
        user_profile = get_user_profile(user_id)
        reply_map = generate_reply(username, user_profile['LIKES'], user_profile['DISLIKES'], history, selected_traits, text = text, image = None)
        print("Robot reply:", reply_map)
        
        print("[Chat] Converting to speech...")
        reply_path = synthesize_speech(reply_map['MESSAGE'])
        
        pending_player.stop()
        
        print("[Chat] Speaking reply...")
        interrupted_audio_path = robot_speech.interruptible_audio(reply_path)
        
        add_to_history(user_id, username, text)
        add_to_history(user_id, "Benji", reply_map['MESSAGE'])
        
        # TOOLS
        if reply_map['TOOLS']:
            for tool in reply_map['TOOLS']:
                tool_name = tool.get('name')
                tool_args = tool.get('args', {})
                
                print(f"[Chat] calling tool: {tool_name}, with args: {tool_args}")
                
                # MOVE
                if tool_name == "move":
                    print("[Chat] move tool received.")
                    
                    action = tool_args.get("action")
                    duration = float(tool_args.get("duration"))
                    
                    ACTION_MAP[action](motors)
                    
                    start_time = time.time()
                    while time.time() - start_time < duration:
                        time.sleep(0.05)
                    motors.stop()
                
                # CAPTURE IMAGE
                if tool_name == "capture_image":
                    print("[Chat] capture_image tool received.")
                    
                    camera.camera_open()
                    frame = camera.frame
                    while frame is None:
                        time.sleep(0.02)
                        frame = camera.frame
                    save_path = "capture_image.jpg"
                    cv2.imwrite(save_path, frame)
                    print(f"[Chat] Saved capture to {save_path}")
                    camera.camera_close()
                    
                    pending_player.start()
                    
                    base64_image = encode_image(save_path)
                    print("[Chat] Encoded image length:", len(base64_image))
                    
                    history = get_history_as_string(user_id)
                    user_profile = get_user_profile(user_id)
                    reply_map = generate_reply(username, user_profile['LIKES'], user_profile['DISLIKES'], history, selected_traits, text = text, image = base64_image)
                    print("Robot reply:", reply_map)
                    
                    print("[Chat] Converting to speech...")
                    reply_path = synthesize_speech(reply_map['MESSAGE'])
                    
                    pending_player.stop()
                    
                    interrupted_audio_path = robot_speech.interruptible_audio(reply_path)
                    
                    add_to_history(user_id, "Benji", reply_map['MESSAGE'])
                    
                    
                
                # UPDATE PROFILE
                if tool_name == 'update_profile':
                    print("[Chat] update_profile tool received.")
                    
                    new_likes = tool_args.get("likes", [])
                    new_dislikes = tool_args.get('dislikes', [])
                    
                    update_user_profile(user_id, new_likes, new_dislikes, user_profile['LIKES'], user_profile['DISLIKES'])
                
                # END CHAT
                if tool_name == 'end_chat':
                    print("[Chat] end_chat tool received.")
                    should_end_chat = True
                    break
        
        if should_end_chat:
            break
        
    rl_trainer.train_and_save()      
                
    
    print("[Chat] Chat loop finished.")
    