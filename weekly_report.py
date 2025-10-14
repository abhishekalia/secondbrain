"""
Weekly Pattern Report Generator
Automated digest of patterns, loops, triggers, breakthroughs
Runs every Sunday or on-demand
"""

import json
import os
from datetime import datetime, timedelta
from collections import Counter, defaultdict

class WeeklyReportGenerator:
    def __init__(self, data_dir="my_data"):
        self.data_dir = data_dir
        
    def load_conversations(self, days=7):
        """Load conversations from last N days"""
        cutoff = datetime.now() - timedelta(days=days)
        conversations = []
        
        # Load from master file
        master_file = os.path.join(self.data_dir, "conversations.json")
        if os.path.exists(master_file):
            try:
                with open(master_file) as f:
                    all_convos = json.load(f)
                    for conv in all_convos:
                        if isinstance(conv, dict):
                            timestamp = conv.get("timestamp", "")
                            try:
                                dt = datetime.fromisoformat(timestamp)
                                if dt >= cutoff:
                                    conversations.append(conv)
                            except:
                                continue
            except:
                pass
        
        return conversations
    
    def get_state_distribution(self, conversations):
        """Calculate state distribution"""
        state_counts = Counter()
        total_time = defaultdict(float)
        last_time = None
        last_state = None
        
        for conv in sorted(conversations, key=lambda x: x.get("timestamp", "")):
            state = conv.get("state", {})
            timestamp = conv.get("timestamp", "")
            
            if not isinstance(state, dict) or not timestamp:
                continue
            
            emoji = state.get("emoji")
            if not emoji:
                continue
            
            try:
                dt = datetime.fromisoformat(timestamp)
                
                # Calculate time spent in previous state
                if last_state and last_time:
                    duration = (dt - last_time).total_seconds() / 3600  # hours
                    total_time[last_state] += duration
                
                state_counts[emoji] += 1
                last_state = emoji
                last_time = dt
            except:
                continue
        
        return state_counts, total_time
    
    def detect_loops(self, conversations):
        """Find spiral loops and stuck patterns"""
        loops = []
        current_loop = []
        
        for conv in conversations:
            state = conv.get("state", {})
            if not isinstance(state, dict):
                continue
            
            emoji = state.get("emoji")
            
            # Spiral detection
            if emoji == "🌀":
                current_loop.append({
                    "timestamp": conv.get("timestamp", ""),
                    "content": conv.get("content", "")[:100]
                })
            else:
                # Loop ended
                if len(current_loop) >= 3:
                    loops.append({
                        "duration": len(current_loop),
                        "start": current_loop[0]["timestamp"],
                        "end": current_loop[-1]["timestamp"],
                        "trigger": current_loop[0]["content"]
                    })
                current_loop = []
        
        return loops
    
    def find_breakthroughs(self, conversations):
        """Identify breakthrough moments (spiral → flow or reflection)"""
        breakthroughs = []
        
        for i in range(len(conversations) - 1):
            curr = conversations[i]
            next_conv = conversations[i + 1]
            
            curr_state = curr.get("state", {})
            next_state = next_conv.get("state", {})
            
            if not isinstance(curr_state, dict) or not isinstance(next_state, dict):
                continue
            
            curr_emoji = curr_state.get("emoji")
            next_emoji = next_state.get("emoji")
            
            # Breakthrough: spiral → flow/reflection
            if curr_emoji == "🌀" and next_emoji in ["⚡", "🪞"]:
                breakthroughs.append({
                    "timestamp": next_conv.get("timestamp", ""),
                    "from": "spiral",
                    "to": next_state.get("name", ""),
                    "trigger": next_conv.get("content", "")[:150]
                })
        
        return breakthroughs
    
    def get_top_triggers(self, conversations):
        """Find common triggers for different states"""
        triggers = defaultdict(list)
        
        for i in range(1, len(conversations)):
            prev = conversations[i-1]
            curr = conversations[i]
            
            prev_state = prev.get("state", {})
            curr_state = curr.get("state", {})
            
            if not isinstance(prev_state, dict) or not isinstance(curr_state, dict):
                continue
            
            prev_emoji = prev_state.get("emoji")
            curr_emoji = curr_state.get("emoji")
            
            # State changed
            if prev_emoji != curr_emoji:
                content = curr.get("content", "").lower()
                # Extract keywords (simple version)
                words = [w for w in content.split() if len(w) > 4]
                if words:
                    triggers[curr_emoji].extend(words[:3])
        
        # Get most common triggers per state
        top_triggers = {}
        for state, words in triggers.items():
            counter = Counter(words)
            top_triggers[state] = [w for w, c in counter.most_common(3)]
        
        return top_triggers
    
    def load_latest_patterns(self):
        """Load latest auto-extracted patterns"""
        pattern_dir = os.path.join(self.data_dir, "patterns")
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
    
    def generate_report(self, days=7):
        """Generate comprehensive weekly report"""
        print(f"📊 Generating {days}-day pattern report...")
        
        conversations = self.load_conversations(days)
        
        if len(conversations) < 5:
            print(f"⚠️  Not enough data. Only {len(conversations)} conversations in last {days} days.")
            return None
        
        print(f"Analyzing {len(conversations)} conversations...")
        
        # Gather all data
        state_counts, time_in_state = self.get_state_distribution(conversations)
        loops = self.detect_loops(conversations)
        breakthroughs = self.find_breakthroughs(conversations)
        triggers = self.get_top_triggers(conversations)
        patterns = self.load_latest_patterns()
        
        # Build markdown report
        report = self._build_markdown_report(
            days, conversations, state_counts, time_in_state,
            loops, breakthroughs, triggers, patterns
        )
        
        # Save report
        os.makedirs(os.path.join(self.data_dir, "reports"), exist_ok=True)
        filename = os.path.join(
            self.data_dir,
            "reports",
            f"week_{datetime.now().strftime('%Y%m%d')}.md"
        )
        
        with open(filename, 'w') as f:
            f.write(report)
        
        print(f"✅ Report saved: {filename}")
        return filename
    
    def _build_markdown_report(self, days, conversations, state_counts, 
                                time_in_state, loops, breakthroughs, 
                                triggers, patterns):
        """Build the markdown report"""
        
        report = f"""# Second Brain Weekly Report
**Period:** {datetime.now().strftime('%B %d, %Y')} (Last {days} days)
**Total Conversations:** {len(conversations)}

---

## 📊 State Distribution

"""
        
        # State counts
        state_names = {
            "🧠": "Logic", "🌀": "Spiral", "⚡": "Flow",
            "🪞": "Reflection", "📘": "Teaching", "😤": "Frustrated", "🎯": "Determined"
        }
        
        total_convos = sum(state_counts.values())
        for emoji, count in state_counts.most_common():
            name = state_names.get(emoji, emoji)
            percentage = (count / total_convos * 100) if total_convos > 0 else 0
            time_spent = time_in_state.get(emoji, 0)
            report += f"- **{emoji} {name}**: {count} times ({percentage:.1f}%) • ~{time_spent:.1f}h\n"
        
        # Dominant state
        if state_counts:
            dominant = state_counts.most_common(1)[0]
            report += f"\n**Dominant State:** {dominant[0]} {state_names.get(dominant[0], '')} ({dominant[1]} times)\n"
        
        report += "\n---\n\n"
        
        # Loops
        if loops:
            report += f"## 🌀 Spiral Loops Detected: {len(loops)}\n\n"
            report += "Times you got stuck in repetitive thinking:\n\n"
            for loop in loops[:5]:
                report += f"- **{loop['duration']} spirals** starting {loop['start'][:10]}\n"
                report += f"  - Trigger: *{loop['trigger']}*\n\n"
        else:
            report += "## 🌀 Spiral Loops: None\n\n**Great week!** No prolonged spiral loops detected.\n\n"
        
        report += "---\n\n"
        
        # Breakthroughs
        if breakthroughs:
            report += f"## ⚡ Breakthroughs: {len(breakthroughs)}\n\n"
            report += "Times you broke out of spirals:\n\n"
            for bt in breakthroughs[:5]:
                report += f"- **{bt['timestamp'][:16]}** → {bt['to']}\n"
                report += f"  - What helped: *{bt['trigger']}*\n\n"
        else:
            report += "## ⚡ Breakthroughs: None\n\nNo major state shifts from spiral to flow this week.\n\n"
        
        report += "---\n\n"
        
        # Triggers
        if triggers:
            report += "## 🎯 Top Triggers\n\n"
            report += "Keywords that led to different states:\n\n"
            for emoji, words in triggers.items():
                if words:
                    name = state_names.get(emoji, emoji)
                    report += f"- **{emoji} {name}**: {', '.join(words)}\n"
        
        report += "\n---\n\n"
        
        # Pattern insights
        if patterns and "analysis" in patterns:
            analysis = patterns["analysis"]
            beliefs = analysis.get("stated_beliefs", [])
            
            if beliefs:
                report += "## 🧠 Beliefs Tracked\n\n"
                unique_beliefs = []
                seen = set()
                for b in beliefs:
                    claim = b.get("claim", "")
                    if claim not in seen:
                        unique_beliefs.append(claim)
                        seen.add(claim)
                
                for belief in unique_beliefs[:5]:
                    report += f"- *\"{belief}\"*\n"
        
        report += "\n---\n\n"
        
        # Bottom line
        report += "## 💡 Bottom Line\n\n"
        
        if loops:
            report += f"You spiraled {len(loops)} times this week. "
        else:
            report += "Strong mental week - no spiral loops. "
        
        if breakthroughs:
            report += f"But you broke out {len(breakthroughs)} times. "
        
        if state_counts:
            dominant = state_counts.most_common(1)[0]
            name = state_names.get(dominant[0], "")
            report += f"You spent most time in {dominant[0]} {name} mode."
        
        report += "\n\n"
        report += "**Keep building. The data remembers everything.**\n"
        
        return report


if __name__ == "__main__":
    generator = WeeklyReportGenerator()
    report_file = generator.generate_report(days=7)
    
    if report_file:
        print(f"\n📄 View report: cat {report_file}")