import os
import json
import re
from datetime import datetime

print("🧠 DIGITAL CONSCIOUSNESS - DATA INGESTION")
print("=" * 50)
print("Let's feed your digital twin your actual data!\n")

# Create directories
os.makedirs("my_data/raw", exist_ok=True)
os.makedirs("my_data/processed", exist_ok=True)
os.makedirs("my_data/memories", exist_ok=True)

def show_menu():
    print("\n📊 What data do you want to add?")
    print("-" * 40)
    print("1. 💬 WhatsApp chat export")
    print("2. 💭 Your thoughts/opinions (manual entry)")
    print("3. 📧 Email samples (copy/paste)")
    print("4. 📝 Your writing samples")
    print("5. 🎯 Your goals and values")
    print("6. 💡 How you solve problems")
    print("7. 📚 View collected data")
    print("8. ✅ Process all data for training")
    print("9. 🚪 Exit")
    return input("\nChoose (1-9): ")

def collect_thoughts():
    thoughts = []
    print("\n💭 THOUGHT COLLECTOR")
    print("Tell me your thoughts on various topics (empty to finish):\n")
    
    prompts = [
        "What do you think about AI?",
        "What's your life philosophy?",
        "How do you approach problems?",
        "What are you passionate about?",
        "Describe your ideal day:",
        "What's your communication style?",
        "What are your core values?",
        "How do you make decisions?",
        "What motivates you?",
        "How do you handle stress?"
    ]
    
    for prompt in prompts:
        response = input(f"\n{prompt}\n> ")
        if response:
            thoughts.append({"prompt": prompt, "response": response})
    
    # Save thoughts
    with open("my_data/raw/thoughts.json", "w") as f:
        json.dump(thoughts, f, indent=2)
    
    print(f"\n✅ Saved {len(thoughts)} thoughts!")
    return thoughts

def collect_writing():
    print("\n📝 WRITING SAMPLE COLLECTOR")
    print("Paste a sample of your writing (end with '###' on new line):\n")
    
    lines = []
    while True:
        line = input()
        if line == "###":
            break
        lines.append(line)
    
    writing = "\n".join(lines)
    
    # Save writing
    with open("my_data/raw/writing_sample.txt", "a") as f:
        f.write(f"\n--- Sample from {datetime.now()} ---\n")
        f.write(writing)
        f.write("\n")
    
    print("✅ Writing sample saved!")
    return writing

def process_whatsapp():
    print("\n💬 WHATSAPP IMPORTER")
    print("-" * 40)
    print("How to export WhatsApp chat:")
    print("1. Open WhatsApp on your phone")
    print("2. Go to the chat you want to export")
    print("3. Tap contact name > Export Chat > Without Media")
    print("4. Email it to yourself and save the .txt file")
    print()
    
    filepath = input("Drag the WhatsApp .txt file here (or type path): ").strip()
    
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Parse messages (basic parser)
        messages = []
        lines = content.split('\n')
        your_name = input("What's your name in this chat? ")
        
        for line in lines:
            if your_name in line and ':' in line:
                try:
                    # Extract your messages
                    msg = line.split(': ', 2)[-1]
                    if msg and len(msg) > 10:  # Skip short messages
                        messages.append(msg)
                except:
                    pass
        
        # Save parsed messages
        with open("my_data/processed/whatsapp_messages.json", "w") as f:
            json.dump(messages, f, indent=2)
        
        print(f"✅ Extracted {len(messages)} of your messages!")
        return messages
    else:
        print("❌ File not found")
        return []

def collect_qa_pairs():
    print("\n🎯 RESPONSE STYLE COLLECTOR")
    print("I'll ask questions, you answer as yourself:\n")
    
    qa_pairs = []
    questions = [
        "How would you introduce yourself at a party?",
        "Someone asks for advice about career change. What do you say?",
        "How do you explain something complex to a beginner?",
        "Someone disagrees with you strongly. How do you respond?",
        "What's your typical greeting in a chat?",
        "How do you end conversations?",
        "Someone asks for your opinion on something controversial. Response?",
        "How do you express excitement?",
        "How do you comfort someone who's sad?",
        "How do you tell a story?"
    ]
    
    for q in questions:
        print(f"\n❓ {q}")
        answer = input("📝 Your response: ")
        if answer:
            qa_pairs.append({"question": q, "answer": answer})
    
    # Save Q&A pairs
    with open("my_data/raw/qa_pairs.json", "w") as f:
        json.dump(qa_pairs, f, indent=2)
    
    print(f"\n✅ Saved {len(qa_pairs)} Q&A pairs!")
    return qa_pairs

def view_data():
    print("\n📚 YOUR COLLECTED DATA")
    print("-" * 40)
    
    for root, dirs, files in os.walk("my_data"):
        for file in files:
            filepath = os.path.join(root, file)
            size = os.path.getsize(filepath) / 1024  # KB
            print(f"📄 {filepath} ({size:.1f} KB)")
    
    print("\nTotal data points collected:")
    try:
        # Count various data
        count = 0
        if os.path.exists("my_data/raw/thoughts.json"):
            with open("my_data/raw/thoughts.json") as f:
                count += len(json.load(f))
        if os.path.exists("my_data/raw/qa_pairs.json"):
            with open("my_data/raw/qa_pairs.json") as f:
                count += len(json.load(f))
        if os.path.exists("my_data/processed/whatsapp_messages.json"):
            with open("my_data/processed/whatsapp_messages.json") as f:
                count += len(json.load(f))
        
        print(f"🎯 Total training samples: {count}")
    except:
        print("No data processed yet")

def process_all_data():
    print("\n⚡ PROCESSING ALL DATA FOR TRAINING")
    print("-" * 40)
    
    all_samples = []
    
    # Load all data files
    data_files = [
        ("my_data/raw/thoughts.json", "thought"),
        ("my_data/raw/qa_pairs.json", "qa"),
        ("my_data/processed/whatsapp_messages.json", "message")
    ]
    
    for filepath, dtype in data_files:
        if os.path.exists(filepath):
            with open(filepath) as f:
                data = json.load(f)
                print(f"✅ Loaded {len(data)} {dtype} samples")
                all_samples.extend(data)
    
    # Create training format
    training_data = {
        "personality_samples": all_samples,
        "metadata": {
            "created": datetime.now().isoformat(),
            "total_samples": len(all_samples)
        }
    }
    
    # Save processed training data
    with open("my_data/training_data.json", "w") as f:
        json.dump(training_data, f, indent=2)
    
    print(f"\n🎉 READY FOR TRAINING!")
    print(f"📊 Total samples: {len(all_samples)}")
    print(f"📄 Saved to: my_data/training_data.json")
    
    return training_data

# Main loop
while True:
    choice = show_menu()
    
    if choice == "1":
        process_whatsapp()
    elif choice == "2":
        collect_thoughts()
    elif choice == "3":
        print("\n📧 Email feature coming soon! Use writing samples for now.")
        collect_writing()
    elif choice == "4":
        collect_writing()
    elif choice == "5":
        print("\n🎯 Goals/values - use thought collector!")
        collect_thoughts()
    elif choice == "6":
        collect_qa_pairs()
    elif choice == "7":
        view_data()
    elif choice == "8":
        process_all_data()
    elif choice == "9":
        print("\n👋 Building your consciousness, one memory at a time!")
        break

print("\n✨ Next: Run the enhanced chat to test your digital twin!")
