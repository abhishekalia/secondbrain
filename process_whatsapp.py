import os
import json

print("💬 WHATSAPP PROCESSOR (Hindi/Hinglish/Punjabi supported!)")
print("=" * 50)

filepath = input("\nDrag your WhatsApp .txt file here: ").strip().replace("'", "")
your_name = input("Your name in the chat: ")

if os.path.exists(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    messages = []
    for line in lines:
        if your_name in line and ': ' in line:
            try:
                msg = line.split(': ', 2)[-1].strip()
                if len(msg) > 10:  # Skip short messages
                    messages.append(msg)
            except:
                pass
    
    # Save messages
    os.makedirs("my_data/whatsapp", exist_ok=True)
    output_file = "my_data/whatsapp/messages.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Extracted {len(messages)} messages!")
    print(f"📁 Saved to: {output_file}")
    print("\nYour digital twin will now speak like you in all languages!")
else:
    print("❌ File not found")
