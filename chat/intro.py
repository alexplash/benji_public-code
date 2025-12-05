
from audio.pending_sound import PendingSoundPlayer
from audio.robot_speech import RobotSpeech
from audio.mic_listener import listen_for_human_turn
from ai.tts_client import synthesize_speech
from ai.whisper_client import transcribe_audio
from ai.gpt_client import generate_reply_intro
from db.users.users import get_users, create_user

class IntroConversationHistory:
    def __init__(self):
        self.history = []
    
    def add_to_history(self, speaker, message):
        history_item = {"speaker": speaker, "message": message}
        self.history.append(history_item)
    
    def get_history_as_string(self):
        return "\n".join([f"{item['speaker']}: {item['message']}" for item in self.history])
    

def intro_loop():
    intro_conversation_history = IntroConversationHistory()
    interrupted_audio_path = None
    
    print("[Intro] Starting robot intro...")
    pending_player = PendingSoundPlayer()
    robot_speech = RobotSpeech()
    
    opening_line = "Hello there! Who am I speaking with? What is your full name?"
    opening_audio_path = synthesize_speech(opening_line)
    robot_speech.uninterruptible_audio(opening_audio_path)
    
    intro_conversation_history.add_to_history("Benji", opening_line)
    
    users = get_users()
    print(f"[Intro] All Users: {users}")
    
    while True:
        
        if interrupted_audio_path:
            print("[Intro] Using interrupt audio instead of waiting for next human turn")
            audio_path = interrupted_audio_path
            interrupted_audio_path = None
        else:
            print("[Intro] Listening for human speech...")
            audio_path = listen_for_human_turn()
        
        if audio_path is None:
            print("[Intro] No human speech detected. Exiting chat mode.")
            
            ending_line = "Alright, I'm heading back now. Come talk to me again anytime!"
            ending_audio_path = synthesize_speech(ending_line)
            robot_speech.uninterruptible_audio(ending_audio_path)
            
            return None, None
        
        print("[Intro] Transcribing...")
        pending_player.start()
        text = transcribe_audio(audio_path)
        print("Human said:", text)
        
        print("[Intro] Generating reply...")
        history_text = intro_conversation_history.get_history_as_string()
        reply_map = generate_reply_intro(text, history_text, users)
        print("Robot reply:", reply_map)
        
        if reply_map['MESSAGE'].strip().startswith("CONFIRM_USER:"):
            confirmed_name = reply_map['MESSAGE'].replace("CONFIRM_USER:", "").strip()
            print(f"[Intro] Confirmed User: {confirmed_name}")
            pending_player.stop()
            
            existing = next((u for u in users if u['name'].lower() == confirmed_name.lower()), None)
            
            if existing:
                return int(existing['id']), existing['name']
            
            new_id = create_user(confirmed_name)
            print(f"[Intro] Generating new user => (user_id: {new_id}, username: {confirmed_name})")
            return new_id, confirmed_name
        
        print("[Intro] Converting to speech...")
        reply_path = synthesize_speech(reply_map['MESSAGE'])
        
        pending_player.stop()
        
        print("[Intro] Speaking reply...")
        interrupted_audio_path = robot_speech.interruptible_audio(reply_path)
        
        intro_conversation_history.add_to_history("User", text)
        intro_conversation_history.add_to_history("Benji", reply_map['MESSAGE'])
        
        # TOOLS
        if reply_map['TOOLS']:
            for tool in reply_map['TOOLS']:
                tool_name = tool.get('name')
                tool_args = tool.get('args', {})
                
                print(f"[Intro] calling tool: {tool_name}, with args: {tool_args}")
                
                # END CHAT
                if tool_name == 'end_chat':
                    print("[Intro] end_chat tool received.")
                    return None, None
                
                
                

        
        