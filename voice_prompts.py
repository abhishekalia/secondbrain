"""
Voice Mode Prompt System
Short, simple questions for natural conversation
"""

import random

class VoicePrompts:
    """Generates short, conversational prompts for voice mode"""
    
    # Opening prompts - start the conversation
    OPENINGS = [
        "What's happening?",
        "What's on your mind?",
        "How are you feeling?",
        "What's going on?",
        "Tell me about your day.",
    ]
    
    # Follow-up prompts based on context
    FOLLOW_UPS = {
        "explore": [
            "Tell me more.",
            "Why?",
            "What happened?",
            "And then?",
            "How so?",
        ],
        "feeling": [
            "How did that feel?",
            "What did you feel?",
            "How are you feeling now?",
            "What emotion came up?",
        ],
        "decision": [
            "What did you decide?",
            "What did you do?",
            "What's your move?",
            "What would you do differently?",
        ],
        "why": [
            "Why do you think that?",
            "What makes you say that?",
            "What's behind that?",
            "Why does that matter?",
        ],
        "pattern": [
            "Have you noticed this before?",
            "Does this happen often?",
            "What's the pattern?",
            "Sound familiar?",
        ]
    }
    
    # Closing prompts
    CLOSINGS = [
        "Anything else?",
        "What else?",
        "Keep going?",
        "More to say?",
    ]
    
    @staticmethod
    def get_opening():
        """Get a random opening prompt"""
        return random.choice(VoicePrompts.OPENINGS)
    
    @staticmethod
    def get_follow_up(user_text, conversation_length=0):
        """
        Get an appropriate follow-up question based on what user said
        
        Args:
            user_text: What the user just said
            conversation_length: How many exchanges so far
        """
        text_lower = user_text.lower()
        
        # After 5+ exchanges, offer to wrap up
        if conversation_length > 5:
            if random.random() < 0.3:  # 30% chance
                return random.choice(VoicePrompts.CLOSINGS)
        
        # Detect context and choose appropriate follow-up
        
        # If they mentioned a decision/action
        if any(word in text_lower for word in ['decided', 'did', 'went', 'made', 'chose']):
            return random.choice(VoicePrompts.FOLLOW_UPS["decision"])
        
        # If they mentioned a feeling
        if any(word in text_lower for word in ['feel', 'felt', 'emotion', 'angry', 'sad', 'happy', 'frustrated']):
            return random.choice(VoicePrompts.FOLLOW_UPS["feeling"])
        
        # If they asked why or expressed confusion
        if any(word in text_lower for word in ['why', 'wonder', 'confused', 'not sure', "don't know"]):
            return random.choice(VoicePrompts.FOLLOW_UPS["why"])
        
        # If they mentioned repetition/patterns
        if any(word in text_lower for word in ['again', 'always', 'never', 'keeps', 'pattern', 'loop']):
            return random.choice(VoicePrompts.FOLLOW_UPS["pattern"])
        
        # Default: explore more
        return random.choice(VoicePrompts.FOLLOW_UPS["explore"])
    
    @staticmethod
    def generate_voice_response(user_text, conversation_history, is_opening=False):
        """
        Generate a complete response for voice mode
        Returns a short prompt (max 10 words)
        """
        if is_opening:
            return VoicePrompts.get_opening()
        
        # Get follow-up based on context
        prompt = VoicePrompts.get_follow_up(user_text, len(conversation_history))
        
        return prompt