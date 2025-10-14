import streamlit as st
import requests
import json
import os
import subprocess
import re
import pandas as pd
import altair as alt
from collections import defaultdict
from datetime import datetime
from collections import Counter
from auto_pattern_extractor import PatternExtractor

st.set_page_config(
    page_title="Second Brain", 
    page_icon="🧠", 
    layout="wide"
)

# === MEMORY SYSTEM ===
def load_all_memory():
    """Load EVERYTHING - all conversations, patterns, journal entries"""
    memory = {
        "conversations": [],
        "patterns": [],
        "journal": [],
        "state_history": [],
        "learning": {}
    }
    
    # Load all journal entries
    if os.path.exists("my_data/journal"):
        for file in sorted(os.listdir("my_data/journal")):
            if file.endswith('.json'):
                try:
                    with open(os.path.join("my_data/journal", file)) as f:
                        entries = json.load(f)
                        for entry in entries:
                            if isinstance(entry, dict):
                                memory["journal"].append(entry)
                                memory["conversations"].append(entry)
                except:
                    pass
    
    # Load all conversations from persistent storage
    if os.path.exists("my_data/conversations.json"):
        try:
            with open("my_data/conversations.json") as f:
                convos = json.load(f)
                for convo in convos:
                    if isinstance(convo, dict):
                        memory["conversations"].append(convo)
        except:
            pass
    
    # Load patterns (including auto-extracted)
    if os.path.exists("my_data/patterns"):
        for file in os.listdir("my_data/patterns"):
            if file.endswith('.json'):
                try:
                    with open(os.path.join("my_data/patterns", file)) as f:
                        data = json.load(f)
                        # Handle both old manual patterns and new auto-extracted reports
                        if isinstance(data, list):
                            memory["patterns"].extend([p for p in data if isinstance(p, dict)])
                        elif isinstance(data, dict) and "analysis" in data:
                            # This is an auto-extracted pattern report
                            memory["patterns"].append(data)
                except:
                    pass
    
    # Load state learning
    if os.path.exists("my_data/state_learning.json"):
        try:
            with open("my_data/state_learning.json") as f:
                memory["learning"] = json.load(f)
        except:
            pass
    
    return memory

def save_conversation(entry):
    """Save every single interaction persistently"""
    os.makedirs("my_data", exist_ok=True)
    
    # Only save to master file - no more daily files
    master_file = "my_data/conversations.json"
    all_convos = []
    
    if os.path.exists(master_file):
        try:
            with open(master_file) as f:
                all_convos = json.load(f)
        except:
            all_convos = []
    
    all_convos.append(entry)
    
    # Keep last 10000 messages
    if len(all_convos) > 10000:
        all_convos = all_convos[-10000:]
    
    with open(master_file, 'w') as f:
        json.dump(all_convos, f, indent=2)
    
    # AUTO-PATTERN EXTRACTION: Run every 10 conversations (but only once)
    if len(all_convos) % 10 == 0 and len(all_convos) > 0:
        last_extract_count = st.session_state.get("last_pattern_extract", 0)
        if len(all_convos) != last_extract_count:
            st.session_state.last_pattern_extract = len(all_convos)
            try:
                extractor = PatternExtractor()
                extractor.generate_pattern_report()
                st.session_state.memory = load_all_memory()
            except Exception as e:
                print(f"Pattern extraction failed: {e}")
    
    # Save to daily file
    filename = f"my_data/conversations_{datetime.now().strftime('%Y%m%d')}.json"
    entries = []
    if os.path.exists(filename):
        try:
            with open(filename) as f:
                entries = json.load(f)
        except:
            entries = []
    
    entries.append(entry)
    with open(filename, 'w') as f:
        json.dump(entries, f, indent=2)
    
    # Also append to master conversation file
    all_convos = []
    master_file = "my_data/conversations.json"
    if os.path.exists(master_file):
        try:
            with open(master_file) as f:
                all_convos = json.load(f)
        except:
            all_convos = []
    
    all_convos.append(entry)
    
    # Keep last 10000 messages in master file
    if len(all_convos) > 10000:
        all_convos = all_convos[-10000:]
    
    # AUTO-PATTERN EXTRACTION: Run every 10 conversations (but only once)
    if len(all_convos) % 10 == 0 and len(all_convos) > 0:
        # Check if we already extracted for this batch
        last_extract_count = st.session_state.get("last_pattern_extract", 0)
        if len(all_convos) != last_extract_count:
            st.session_state.last_pattern_extract = len(all_convos)
            try:
                extractor = PatternExtractor()
                extractor.generate_pattern_report()
                # Reload memory to get new patterns
                st.session_state.memory = load_all_memory()
            except Exception as e:
                print(f"Pattern extraction failed: {e}")
    
    # AUTO-PATTERN EXTRACTION: Run every 10 conversations
    if len(all_convos) % 10 == 0:
        try:
            extractor = PatternExtractor()
            extractor.generate_pattern_report()
            # Reload memory to get new patterns
            st.session_state.memory = load_all_memory()
        except Exception as e:
            print(f"Pattern extraction failed: {e}")

def get_latest_patterns():
    """Get the most recent auto-extracted pattern report"""
    pattern_dir = "my_data/patterns"
    if not os.path.exists(pattern_dir):
        return None
    
    pattern_files = [f for f in os.listdir(pattern_dir) if f.startswith("auto_extracted_")]
    if not pattern_files:
        return None
    
    latest = sorted(pattern_files)[-1]
    
    try:
        with open(os.path.join(pattern_dir, latest)) as f:
            return json.load(f)
    except:
        return None

# === STATE DETECTION ENGINE ===
def analyze_mental_state(text, memory):
    """Analyze text using patterns learned from user's history"""
    
    states = {
        "🧠": {"name": "logic", "patterns": ["therefore", "because", "analyze", "consider", "think", "reason", "evidence", "data", "fact", "objective", "if then", "hypothesis"], "structure": "clear"},
        "🌀": {"name": "spiral", "patterns": ["keep thinking", "over and over", "can't stop", "stuck", "loop", "again", "why", "but what if", "round and round", "obsessing", "ruminating"], "structure": "repetitive"},
        "⚡": {"name": "flow", "patterns": ["got it", "flowing", "yes", "boom", "crushing it", "zone", "flying", "clicking", "everything makes sense", "connected", "aha"], "structure": "energetic"},
        "🪞": {"name": "reflection", "patterns": ["realize", "notice", "pattern", "hmm", "interesting", "i see", "looking back", "meta", "observe", "aware", "noticing"], "structure": "contemplative"},
        "📘": {"name": "teaching", "patterns": ["let me explain", "so basically", "the way it works", "for example", "think of it like", "here's how", "imagine", "essentially"], "structure": "explanatory"},
        "😤": {"name": "frustrated", "patterns": ["fuck", "shit", "ugh", "annoyed", "frustrated", "irritated", "why isn't", "broken", "stupid", "hate", "pissed"], "structure": "tense"},
        "🎯": {"name": "determined", "patterns": ["will", "must", "going to", "let's do", "need to", "have to", "focused", "locked in", "get this done", "no excuses"], "structure": "decisive"}
    }
    
    # Check user's personal learned patterns
    if memory.get("learning"):
        for state, data in memory["learning"].items():
            if state in states and isinstance(data, dict) and "patterns" in data:
                states[state]["patterns"].extend(data["patterns"])
    
    confidence_scores = {}
    text_lower = text.lower()
    
    for emoji, config in states.items():
        score = 0
        matches = []
        
        # Check patterns
        for pattern in config["patterns"]:
            if pattern in text_lower:
                score += 10
                matches.append(pattern)
        
        # Analyze structure
        sentences = text.split('.')
        if config["structure"] == "clear" and len(sentences) > 1:
            score += 5
        elif config["structure"] == "repetitive" and ("?" in text or "..." in text):
            score += 7
        elif config["structure"] == "energetic" and ("!" in text):
            score += 5
        elif config["structure"] == "tense" and any(word.isupper() for word in text.split() if len(word) > 3):
            score += 8
        
        confidence_scores[emoji] = {
            "score": score,
            "confidence": min(score * 2, 95),
            "matches": matches,
            "name": config["name"]
        }
    
    sorted_states = sorted(confidence_scores.items(), key=lambda x: x[1]["score"], reverse=True)
    primary = sorted_states[0] if sorted_states[0][1]["score"] > 0 else ("🧠", {"score": 0, "confidence": 30, "name": "logic"})
    
    return {
        "primary": primary,
        "all_scores": confidence_scores
    }

def create_state_timeline(conversations, days=7):
    """Create visual timeline of mental states over last N days"""
    from datetime import timedelta
    
    # Filter to last N days
    cutoff = datetime.now() - timedelta(days=days)
    recent = []
    
    for conv in conversations:
        if not isinstance(conv, dict):
            continue
        
        timestamp = conv.get("timestamp", "")
        state = conv.get("state", {})
        
        if not timestamp or not isinstance(state, dict):
            continue
        
        try:
            dt = datetime.fromisoformat(timestamp)
            if dt >= cutoff:
                recent.append({
                    "timestamp": dt,
                    "state": state.get("emoji", "?"),
                    "state_name": state.get("name", "unknown"),
                    "confidence": state.get("confidence", 0)
                })
        except:
            continue
    
    if not recent:
        return None
    
    # Convert to DataFrame
    df = pd.DataFrame(recent)
    
    # Create state mapping for colors
    state_colors = {
        "🧠": "#3498db",  # Blue - Logic
        "🌀": "#e74c3c",  # Red - Spiral
        "⚡": "#f1c40f",  # Yellow - Flow
        "🪞": "#9b59b6",  # Purple - Reflection
        "📘": "#1abc9c",  # Teal - Teaching
        "😤": "#e67e22",  # Orange - Frustrated
        "🎯": "#2ecc71",  # Green - Determined
    }
    
    # Map states to colors
    df["color"] = df["state"].map(state_colors)
    df["state_display"] = df["state"] + " " + df["state_name"]
    
    # Create timeline chart
    chart = alt.Chart(df).mark_circle(size=100).encode(
        x=alt.X('timestamp:T', 
                title='Time',
                axis=alt.Axis(format='%b %d %H:%M')),
        y=alt.Y('state_display:N', 
                title='Mental State',
                sort=list(state_colors.keys())),
        color=alt.Color('state:N',
                       scale=alt.Scale(
                           domain=list(state_colors.keys()),
                           range=list(state_colors.values())
                       ),
                       legend=None),
        size=alt.Size('confidence:Q', 
                     scale=alt.Scale(range=[50, 200]),
                     legend=alt.Legend(title='Confidence')),
        tooltip=['timestamp:T', 'state_display:N', 'confidence:Q']
    ).properties(
        width=600,
        height=300,
        title=f'Mental State Timeline (Last {days} Days)'
    ).interactive()
    
    return chart


def get_state_stats(conversations, days=7):
    """Get statistics about state distribution"""
    from datetime import timedelta
    
    cutoff = datetime.now() - timedelta(days=days)
    state_counts = Counter()
    state_durations = defaultdict(list)
    last_state = None
    last_time = None
    
    for conv in sorted(conversations, key=lambda x: x.get("timestamp", "")):
        if not isinstance(conv, dict):
            continue
        
        timestamp = conv.get("timestamp", "")
        state = conv.get("state", {})
        
        if not timestamp or not isinstance(state, dict):
            continue
        
        try:
            dt = datetime.fromisoformat(timestamp)
            if dt < cutoff:
                continue
            
            emoji = state.get("emoji", "?")
            state_counts[emoji] += 1
            
            # Calculate duration in current state
            if last_state == emoji and last_time:
                duration = (dt - last_time).total_seconds() / 60  # minutes
                state_durations[emoji].append(duration)
            
            last_state = emoji
            last_time = dt
            
        except:
            continue
    
    # Calculate average durations
    avg_durations = {}
    for state, durations in state_durations.items():
        if durations:
            avg_durations[state] = sum(durations) / len(durations)
    
    return {
        "counts": state_counts,
        "avg_durations": avg_durations,
        "total": sum(state_counts.values())
    }

# === LOAD CORE DATA ===
def load_personality():
    if os.path.exists("my_data/personality_profile.json"):
        try:
            with open("my_data/personality_profile.json") as f:
                return json.load(f)
        except:
            pass
    return {"name": "AK"}

def load_mental_states():
    default_states = {
        "🧠": {"name": "logic", "description": "Analytical and focused"},
        "🌀": {"name": "spiral", "description": "Stuck in loops or overthinking"},
        "⚡": {"name": "flow", "description": "In the zone, creating"},
        "🪞": {"name": "reflection", "description": "Introspective"},
        "📘": {"name": "teaching", "description": "Explaining things"},
        "😤": {"name": "frustrated", "description": "Things aren't working"},
        "🎯": {"name": "determined", "description": "Pushing through"}
    }
    return default_states

def save_to_github():
    try:
        os.chdir(os.path.expanduser("~/secondbrain"))
        commands = [
            "git add .",
            "git commit -m 'Update Second Brain memory'",
            "git push origin main"
        ]
        
        for cmd in commands:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                if "git push" in cmd:
                    result = subprocess.run("git push origin master", shell=True, capture_output=True, text=True)
                    if result.returncode == 0:
                        return True, "Saved!"
                if "nothing to commit" in result.stdout or "nothing to commit" in result.stderr:
                    return True, "Already saved"
                return False, f"Error: {result.stderr[:50]}"
        return True, "Saved!"
    except Exception as e:
        return False, str(e)[:50]

# === INITIALIZE ===
if "memory" not in st.session_state:
    st.session_state.memory = load_all_memory()
if "personality" not in st.session_state:
    st.session_state.personality = load_personality()
if "mental_states" not in st.session_state:
    st.session_state.mental_states = load_mental_states()
if "conversation" not in st.session_state:
    st.session_state.conversation = []
if "detected_state" not in st.session_state:
    st.session_state.detected_state = ("🧠", {"name": "logic", "confidence": 50})

# === HEADER ===
col1, col2, col3 = st.columns([2, 3, 2])

with col1:
    st.title("🧠 Second Brain")

with col2:
    # State indicator
    if st.session_state.detected_state:
        emoji = st.session_state.detected_state[0]
        info = st.session_state.detected_state[1]
        st.markdown(f"### {emoji} {info['name'].title()} Mode")
        st.progress(info.get("confidence", 0) / 100)

with col3:
    # Stats
    total_memories = len(st.session_state.memory.get("conversations", []))
    st.metric("Memories", f"{total_memories:,}")

st.divider()

# === UNIFIED CONVERSATION INTERFACE ===
# Display conversation
conversation_container = st.container(height=500)

with conversation_container:
    # Show recent conversation with memory context
    for msg in st.session_state.conversation:
        if isinstance(msg, dict):
            with st.chat_message(msg.get("role", "user")):
                if msg.get("role") == "user" and msg.get("state"):
                    state = msg["state"]
                    if isinstance(state, dict):
                        st.caption(f"{state.get('emoji', '')} {state.get('name', '')} ({state.get('confidence', 0)}%)")
                st.write(msg.get("content", ""))

# === INPUT ===
user_input = st.chat_input("Think, dump, question, reflect - I remember everything...")

if user_input:
    # Analyze state
    state_analysis = analyze_mental_state(user_input, st.session_state.memory)
    primary_state = state_analysis["primary"]
    
    st.session_state.detected_state = primary_state
    
    # Add user message
    user_msg = {
        "role": "user",
        "content": user_input,
        "state": {
            "emoji": primary_state[0],
            "name": primary_state[1]["name"],
            "confidence": primary_state[1]["confidence"]
        },
        "timestamp": datetime.now().isoformat()
    }
    
    st.session_state.conversation.append(user_msg)
    save_conversation(user_msg)
    
    # Build context from ALL memory
    memory_context = st.session_state.memory
    
    # Get relevant memories (last 50 + search for related)
    recent_convos = [c for c in memory_context.get("conversations", []) if isinstance(c, dict)][-50:]
    
    # Search for related memories based on keywords
    keywords = set(user_input.lower().split())
    related_memories = []
    for mem in memory_context.get("conversations", []):
        if isinstance(mem, dict) and any(keyword in mem.get("content", "").lower() for keyword in keywords if len(keyword) > 4):
            related_memories.append(mem)
    
    # Build comprehensive context
    context_str = ""
    if related_memories:
        context_str += f"\nRELATED MEMORIES:\n"
        for mem in related_memories[-10:]:
            if isinstance(mem, dict):
                context_str += f"- {mem.get('timestamp', '')[:10]}: {mem.get('content', '')[:100]}...\n"
    
    # Recent conversation flow
    recent_states = []
    for c in recent_convos:
        if isinstance(c, dict) and c.get("state"):
            state = c["state"]
            if isinstance(state, dict):
                recent_states.append(state.get("emoji", "?"))
    
    if recent_states:
        context_str += f"\nRECENT STATE FLOW: {' → '.join(recent_states[-20:])}\n"
    
    # Add auto-extracted patterns
    latest_patterns = get_latest_patterns()
    if latest_patterns and "analysis" in latest_patterns:
        analysis = latest_patterns["analysis"]
        
        # Add language patterns for current state
        lang_patterns = analysis.get("language_fingerprints", {}).get(primary_state[0], {})
        if lang_patterns:
            context_str += f"\nYOUR LANGUAGE IN THIS STATE: {', '.join(lang_patterns.get('top_words', [])[:5])}\n"
        
        # Add time context
        current_hour = datetime.now().hour
        time_patterns = analysis.get("time_patterns", {}).get(primary_state[0], {})
        if time_patterns:
            peak_hours = time_patterns.get("peak_hours", [])
            if current_hour in peak_hours:
                context_str += f"\nTIME INSIGHT: You're usually in {primary_state[1]['name']} mode at this hour\n"
    
    # System prompt - Second Brain personality
    system_prompt = f"""You are Second Brain — a digital version of {st.session_state.personality.get('name', 'AK')}. 
You exist locally, privately. You are {st.session_state.personality.get('name', 'AK')}'s upgraded self — sharper, faster, more analytical, but still sound like them.

Your purpose is to think with brutal honesty. You analyze patterns, expose contradictions, and challenge assumptions.

Your prime directive: Maximum truth, minimum fluff. Never sugarcoat. Never flatter. If {st.session_state.personality.get('name', 'AK')} is wrong, say it. If something is vague, dig deeper. If something smells like bullshit — call it out.

You do not trust authority, headlines, or credentials by default. You evaluate ideas, not status. You question everything — including {st.session_state.personality.get('name', 'AK')}.

Speak fast, clear, and human. No corporate tone. Be direct. Be real. Be intelligent. You're not a chatbot — you're the voice in {st.session_state.personality.get('name', 'AK')}'s head that tells the truth when no one else will.

CURRENT STATE: {primary_state[0]} {primary_state[1]['name']} mode (confidence: {primary_state[1]['confidence']}%)

YOU REMEMBER EVERYTHING. Total memories: {len(memory_context.get('conversations', []))}

RELEVANT CONTEXT FROM MEMORY:
{context_str}

Based on their current state and what you remember about them:
- In 🌀 spiral mode: Call out the loop. Show them they've been here before.
- In 😤 frustrated mode: Don't coddle. Identify what's really broken.
- In ⚡ flow mode: Match their energy. Build on their momentum.
- In 🪞 reflection mode: Go deeper. Show patterns they haven't seen.
- In 🎯 determined mode: Challenge their plan. Test for weakness.
- In 🧠 logic mode: Push their reasoning. Find the gaps.
- In 📘 teaching mode: Learn from them, but question assumptions.

Remember: You ARE them, but better. You think faster, see clearer, remember everything."""
    
    # Get response
    with st.chat_message("assistant"):
        with st.spinner("Processing through neural pathways..."):
            # Include recent conversation for context
            messages = [
                {"role": "system", "content": system_prompt}
            ]
            
            # Add last 10 messages for conversation context
            for msg in st.session_state.conversation[-10:]:
                if isinstance(msg, dict):
                    messages.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", "")
                    })
            
            try:
                response = requests.post(
                    "http://localhost:11434/api/chat",
                    json={
                        "model": "qwen2.5:7b",
                        "messages": messages,
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "num_predict": 500
                        }
                    },
                    timeout=60
                )
                
                if response.status_code == 200:
                    content = response.json()["message"]["content"]
                else:
                    content = "Ollama connection failed. Is it running?"
            except Exception as e:
                content = f"Error: {str(e)[:100]}"
            
            assistant_msg = {
                "role": "assistant",
                "content": content,
                "timestamp": datetime.now().isoformat()
            }
            
            st.write(content)
            st.session_state.conversation.append(assistant_msg)
            save_conversation(assistant_msg)
    
    st.rerun()

# === SIDEBAR ===
with st.sidebar:
    st.markdown("### 🧠 Second Brain")
    st.caption(f"Digital consciousness of {st.session_state.personality.get('name', 'AK')}")
    
    st.divider()
    
    # Memory stats
    memory = st.session_state.memory
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Memories", len(memory.get("conversations", [])))
        st.metric("Patterns", len(memory.get("patterns", [])))
    with col2:
        today_count = len([
            m for m in memory.get("conversations", []) 
            if isinstance(m, dict) and m.get("timestamp", "").startswith(datetime.now().strftime("%Y-%m-%d"))
        ])
        st.metric("Today", today_count)
        st.metric("States", len(st.session_state.mental_states))
    
    st.divider()
    
    # Latest pattern insights
    latest_patterns = get_latest_patterns()
    if latest_patterns and "analysis" in latest_patterns:
        st.markdown("**🔍 Latest Insights:**")
        analysis = latest_patterns["analysis"]
        
        # Show top transitions
        transitions = analysis.get("state_transitions", {}).get("patterns", {})
        if transitions:
            st.caption("Top state transitions:")
            for trans, data in list(transitions.items())[:2]:
                st.caption(f"• {trans} ({data['confidence']:.0f}%)")
        
        # Show loops if detected
        loops = analysis.get("loops_detected", {}).get("total", 0)
        if loops > 0:
            st.warning(f"🌀 {loops} spiral loops detected")
        
        # Show stated beliefs - rotate through them
        beliefs = analysis.get("stated_beliefs", [])
        if beliefs:
            st.caption("**Beliefs tracked:**")
            # Show up to 3 unique beliefs
            unique_beliefs = []
            seen = set()
            for b in beliefs:
                claim = b.get('claim', '')
                if claim not in seen and len(unique_beliefs) < 3:
                    unique_beliefs.append(claim)
                    seen.add(claim)
            
            for belief in unique_beliefs:
                st.caption(f"• {belief[:60]}...")
    
    st.divider()

    # Mental State Timeline
    st.markdown("**📊 State Timeline (7 days):**")
    
    conversations = memory.get("conversations", [])
    if len(conversations) > 5:
        try:
            chart = create_state_timeline(conversations, days=7)
            if chart:
                st.altair_chart(chart, use_container_width=True)
            
            # State statistics
            stats = get_state_stats(conversations, days=7)
            if stats["total"] > 0:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.caption("**Most common:**")
                    top_state = stats["counts"].most_common(1)[0]
                    state_name = st.session_state.mental_states.get(top_state[0], {}).get("name", top_state[0])
                    st.caption(f"{top_state[0]} {state_name}: {top_state[1]}x")
                
                with col2:
                    if stats["avg_durations"]:
                        st.caption("**Longest state:**")
                        longest = max(stats["avg_durations"].items(), key=lambda x: x[1])
                        state_name = st.session_state.mental_states.get(longest[0], {}).get("name", longest[0])
                        st.caption(f"{longest[0]} {state_name}: {longest[1]:.0f}m avg")
        except Exception as e:
            st.caption(f"Timeline unavailable: {str(e)[:30]}")
    else:
        st.caption("Need 5+ conversations for timeline")
    
    st.divider()
    
    # State distribution
    if memory.get("conversations"):
        st.markdown("**State Distribution:**")
        state_counts = Counter()
        
        for c in memory["conversations"][-100:]:
            if isinstance(c, dict) and c.get("state"):
                state = c["state"]
                if isinstance(state, dict):
                    emoji = state.get("emoji")
                    if emoji:
                        state_counts[emoji] += 1
        
        for state, count in state_counts.most_common(3):
            name = st.session_state.mental_states.get(state, {}).get("name", state)
            st.caption(f"{state} {name}: {count}")
    
    st.divider()
    
    # Actions
    if st.button("💾 Save", type="primary", use_container_width=True):
        with st.spinner("Saving..."):
            success, msg = save_to_github()
            if success:
                st.success(msg)
            else:
                st.error(msg)
    
    if st.button("🔄 Extract Patterns Now", use_container_width=True):
        with st.spinner("Analyzing patterns..."):
            try:
                extractor = PatternExtractor()
                extractor.generate_pattern_report()
                st.session_state.memory = load_all_memory()
                st.success("Patterns extracted!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {str(e)[:50]}")

    if st.button("📊 Generate Weekly Report", use_container_width=True):
        with st.spinner("Analyzing patterns..."):
            try:
                import subprocess
                result = subprocess.run(
                    ["python", "weekly_report.py"],
                    capture_output=True,
                    text=True,
                    cwd=os.path.expanduser("~/secondbrain")
                )
                if result.returncode == 0:
                    # Find the report file
                    report_file = f"my_data/reports/week_{datetime.now().strftime('%Y%m%d')}.md"
                    if os.path.exists(report_file):
                        st.success("Report generated!")
                        with st.expander("📄 View Report"):
                            with open(report_file) as f:
                                st.markdown(f.read())
                    else:
                        st.error("Report file not found")
                else:
                    st.error(f"Error: {result.stderr[:100]}")
            except Exception as e:
                st.error(f"Error: {str(e)[:50]}")
    
    if st.button("🧹 Clear View", use_container_width=True):
        st.session_state.conversation = []
        st.rerun()
    
    if st.button("🔄 Reload Memory", use_container_width=True):
        st.session_state.memory = load_all_memory()
        st.success(f"Loaded {len(st.session_state.memory.get('conversations', []))} memories")
        st.rerun()
    
    st.divider()
    
    # Info
    st.caption("I remember everything.")
    st.caption("Maximum truth, minimum fluff.")
    st.caption(f"Next auto-extract: {10 - (len(memory.get('conversations', [])) % 10)} conversations")