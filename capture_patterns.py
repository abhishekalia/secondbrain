import json
import os
from datetime import datetime

def capture_real_pattern():
    """Capture your actual thinking patterns, including struggles"""
    
    print("🌀 PATTERN CAPTURE - Be Real, Not Perfect")
    print("=" * 50)
    print("\nShow your digital twin your ACTUAL patterns:")
    print("- How you really think when stuck")
    print("- Your procrastination patterns")
    print("- Your loops and spirals")
    print("- Your breakthrough moments\n")
    
    patterns = []
    
    # Load mental states if they exist
    states = {}
    if os.path.exists("my_data/mental_states.json"):
        with open("my_data/mental_states.json") as f:
            states = json.load(f)
            print("Your mental states:", " ".join(states.keys()))
    
    while True:
        print("\n" + "-"*40)
        print("Capture a pattern (or 'done' to finish):")
        
        # Get current state
        state = input("Current mental state (emoji or describe): ")
        if state.lower() == 'done':
            break
        
        # Get the actual pattern
        print("\nDescribe what's happening in your mind RIGHT NOW:")
        print("(Be honest - show the loops, the struggles, the real thinking)")
        
        pattern = input("> ")
        
        # Get context
        trigger = input("What triggered this state? ")
        
        # How you typically handle it
        typical_response = input("How do you usually handle this? ")
        
        # What you wish you could do
        ideal_response = input("How would your best self handle this? ")
        
        patterns.append({
            "timestamp": datetime.now().isoformat(),
            "state": state,
            "pattern": pattern,
            "trigger": trigger,
            "typical_response": typical_response,
            "ideal_response": ideal_response
        })
        
        print("✅ Pattern captured!")
    
    # Save patterns
    os.makedirs("my_data/patterns", exist_ok=True)
    filename = f"my_data/patterns/patterns_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(filename, 'w') as f:
        json.dump(patterns, f, indent=2)
    
    print(f"\n📊 Captured {len(patterns)} real patterns")
    print("Your digital twin is learning your actual thinking structure")

if __name__ == "__main__":
    capture_real_pattern()
