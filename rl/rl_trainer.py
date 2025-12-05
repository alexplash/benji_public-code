
import pandas as pd
import math
from statistics import mean
import random
import os
from db.rl.rl import get_rl_profile, get_rl_traits, save_rl_profile, save_trait_weights
from ai.sentiment_analysis import SentimentAnalyzer

CURRENT_DIR = os.path.dirname(__file__)
TRAITS_CSV_PATH = os.path.join(CURRENT_DIR, "traits.csv")
TRAITS_DF = pd.read_csv(TRAITS_CSV_PATH)
TRAITS_MAP = {
    int(row['trait_id']): {
        "trait_name": row['trait_name'],
        "description": row['description']
    } for _, row in TRAITS_DF.iterrows()
}

def compute_epsilon(num_sessions):
        epsilon_min = 0.05
        epsilon_start = 1.0
        epsilon_decay = 0.03
        
        epsilon = epsilon_min + (epsilon_start - epsilon_min) * math.exp(-epsilon_decay * num_sessions)
        return epsilon

class RLTrainer:
    
    def __init__(self, user_id):
    
        self.user_id = user_id
        
        rl_profile = get_rl_profile(self.user_id)
        rl_traits = get_rl_traits(self.user_id)
        
        self.baseline_reward = rl_profile['baseline_reward']
        self.num_sessions = rl_profile['num_sessions']
        
        self.traits = []
        for trait in rl_traits:
            trait_desc = TRAITS_MAP[trait['trait_id']]['description']
            self.traits.append({
                "trait_id": trait['trait_id'],
                "trait_name": trait['trait_name'],
                "weight": trait['weight'],
                "description": trait_desc
            })
        self.selected_traits = []
        
        self.epsilon = compute_epsilon(self.num_sessions)
        self.num_turns = 0
        self.num_interruptions = 0
        self.user_responses = []
        
        self.sentiment_analyzer = SentimentAnalyzer()
    
    def select_traits(self, k = 3):
        
        if random.random() < self.epsilon:
            selected_traits = random.sample(self.traits, k)
        else:
            sorted_traits = sorted(self.traits, key = lambda t: t['weight'], reverse = True)
            selected_traits = sorted_traits[:k]
        
        self.selected_traits = selected_traits
        return selected_traits

    def add_user_turn_data(self, user_response: str, interrupted: bool):

        self.num_turns += 1
        if interrupted:
            self.num_interruptions += 1
        
        self.user_responses.append(user_response)
    
    def train_and_save(self, lr = 0.2):
        
        # ASSIGN NEW WEIGHTS
        # --------------------------------------------------------------------------------------------------------------
        
        sentiment_scores = [self.sentiment_analyzer.classify(response)["POSITIVE"] for response in self.user_responses]
        avg_sentiment = mean(sentiment_scores) if sentiment_scores else 0.5
        
        # conversation length component
        conv_len_term = 1 - math.exp(-self.num_turns / 10)
        
        # interruptions component
        if self.num_interruptions == 0:
            inter_rate = 0
        else:
            inter_rate = (self.num_interruptions / self.num_turns)
        inter_term = 1 - inter_rate
        
        reward = (0.4 * conv_len_term) + (0.3 * inter_term) + (0.3 * avg_sentiment)
        advantage = reward - self.baseline_reward
        
        for selected in self.selected_traits:
            old_weight = selected['weight']
            
            new_weight = old_weight + (lr * advantage)
            new_weight = max(0.0, min(1.0, new_weight))
            
            selected['weight'] = new_weight
        
        
        # SAVE DATA
        # -------------------------------------------------------------------------------------------------------------- 
        new_num_sessions = self.num_sessions + 1
        new_baseline = (self.baseline_reward * self.num_sessions + reward) / new_num_sessions
        
        save_trait_weights(self.user_id, self.selected_traits)
        save_rl_profile(self.user_id, new_baseline, new_num_sessions)
        
        print("\n================== RL TRAINING SUMMARY ==================")

        print(f"[RL] Old baseline_reward: {self.baseline_reward:.4f}")
        print(f"[RL] Old num_sessions:    {self.num_sessions}")

        print("\n[RL] Trait Weights Before Update:")
        for t in self.traits:
            print(f"   {t['trait_name']:<20}  {t['weight']:.4f}")

        print("\n[RL] Computed Reward:     {:.4f}".format(reward))
        print("[RL] Advantage:           {:.4f}".format(advantage))

        print("\n[RL] New baseline_reward: {:.4f}".format(new_baseline))
        print("[RL] New num_sessions:    {}".format(new_num_sessions))

        print("\n[RL] Updated Trait Weights (Only Selected Traits Change):")
        for t in self.selected_traits:
            print(f"   {t['trait_name']:<20}  {t['weight']:.4f}")

        print("==========================================================\n")

            
        
        
        
        
        
         