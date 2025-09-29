import os
import json
import re

print("🌍 MULTILINGUAL WHATSAPP PROCESSOR")
print("=" * 50)
print("Supports: English, Hindi, Hinglish, Punjabi\n")

def process_whatsapp_multilingual(filepath, your_name):
    """Process WhatsApp chats in any language"""
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    messages = []
    message_languages = {"english": 0, "mixed": 0, "hindi": 0}
    
    lines = content.split('\n')
    
    for line in lines:
        if your_name in line and ':' in line:
            try:
                # Extract message
                msg = line.split(': ', 2)[-1]
                
                if msg and len(msg) > 10:
                    # Detect language mix (basic detection)
                    has_english = bool(re.search(r'[a-zA-Z]', msg))
                    has_devanagari = bool(re.search(r'[\u0900-\u097F]', msg))
                    
                    lang_type = "mixed" if (has_english and has_devanagari) else "english" if has_english else "hindi"
                    message_languages[lang_type] += 1
                    
                    messages.append({
                        "text": msg,
                        "language_hint": lang_type
                    })
            except:
                pass
    
    print(f"\n📊 Language Distribution:")
    print(f"  English: {message_languages['english']}")
    print(f"  Mixed/Hinglish: {message_languages['mixed']}")
    print(f"  Hindi/Punjabi: {message_languages['hindi']}")
    
    return messages

# Get file path
filepath = input("Drag your WhatsApp .txt file here: ").strip().replace("'", "").replace('"', '')
your_name = input("Your name in the chat: ")

if os.path.exists(filepath):
    messages = process_whatsapp_multilingual(filepath, your_name)
    
    # Save all messages
    os.makedirs("my_data/multilingual", exist_ok=True)
    with open("my_data/multilingual/whatsapp_all_languages.json", "w", encoding='utf-8') as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Processed {len(messages)} messages in multiple languages!")
    print("These will help your digital twin speak like you in ALL languages!")
else:
    print("❌ File not found")
