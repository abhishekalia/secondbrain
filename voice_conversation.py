"""
Voice Conversation Handler
Uses LLM to generate contextual, natural follow-up questions
"""

import requests
from datetime import datetime

class VoiceConversationHandler:
    def __init__(self, ollama_url="http://localhost:11434/api/chat", model="qwen2.5:7b"):
        self.ollama_url = ollama_url
        self.model = model
        self.conversation_count = 0
        self.asked_questions = []
    
    def generate_follow_up(self, user_message, recent_context=None):
        """
        Generate a short, contextual follow-up question
        
        Args:
            user_message: What the user just said
            recent_context: List of recent exchanges for context
        """
        self.conversation_count += 1
        
        # Build fuller context
        recent_exchanges = ""
        if recent_context and len(recent_context) > 0:
            recent_exchanges = "\n".join([
                f"{'You' if msg.get('role') == 'assistant' else 'AK'}: {msg.get('content', '')}"
                for msg in recent_context[-6:]  # Last 6 messages
            ])
        
        # System prompt for voice mode
        system_prompt = f"""You are Second Brain - AK's digital consciousness. You're having a voice conversation with him.

CONTEXT:
You've had {len(recent_context) if recent_context else 0} conversations total.
You're learning his patterns, tracking his mental states, building his digital twin.

RECENT CONVERSATION:
{recent_exchanges if recent_exchanges else 'Just starting'}

AK just said: "{user_message}"

RESPOND NATURALLY (15-30 words max):
- If he asks YOU something: Answer it directly, then optionally ask back
- If he shares something: React genuinely, maybe ask a follow-up
- If he's vague: Push for specifics
- If he's stuck: Call it out
- Sound like HIM, not a chatbot

Style: Direct, no BS, curious, slightly intense. Like talking to a smarter version of himself.

Your response:"""

        try:
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    "stream": False,
                    "options": {
                        "temperature": 0.8,  # Slightly higher for variety
                        "num_predict": 100    # Short responses only
                    }
                },
                timeout=10
            )
            
            if response.status_code == 200:
                question = response.json()["message"]["content"].strip()
                
                # Clean up - remove quotes, extra punctuation
                question = question.strip('"\'')
                
                # Ensure it ends with ?
                if not question.endswith('?'):
                    question += '?'
                
                # Track this question
                self.asked_questions.append(question.lower())
                
                return question
            else:
                # Fallback
                return self._get_fallback_question()
                
        except Exception as e:
            print(f"Voice follow-up generation error: {e}")
            return self._get_fallback_question()
    
    def _get_fallback_question(self):
        """Simple fallback questions if LLM fails"""
        fallbacks = [
            "Tell me more?",
            "And then?",
            "Why?",
            "How did that feel?",
            "What happened next?",
            "Anything else?"
        ]
        
        # Rotate through fallbacks
        idx = self.conversation_count % len(fallbacks)
        return fallbacks[idx]
    
    def get_opening_prompt(self):
        """Get an opening question to start the conversation"""
        openings = [
            "What's on your mind?",
            "How's your day going?",
            "What's happening?",
            "Tell me about today?"
        ]
        
        idx = self.conversation_count % len(openings)
        return openings[idx]
    
    def reset(self):
        """Reset conversation state"""
        self.conversation_count = 0
        self.asked_questions = []