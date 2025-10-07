"""
Auto-Pattern Extraction Engine
Learns AK's patterns from behavior, not self-reporting.
Detects contradictions. Tracks outcomes. Builds consciousness foundation.
"""

import json
import os
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import re

class PatternExtractor:
    def __init__(self, data_dir="my_data"):
        self.data_dir = data_dir
        self.min_instances = 5  # Minimum occurrences to declare a pattern
        self.min_confidence = 0.50  # 50% threshold
        
    def load_all_conversations(self):
        """Load every conversation from memory"""
        conversations = []
        
        # Load from master file
        master_file = os.path.join(self.data_dir, "conversations.json")
        if os.path.exists(master_file):
            try:
                with open(master_file) as f:
                    data = json.load(f)
                    conversations.extend([c for c in data if isinstance(c, dict)])
            except:
                pass
        
        # Load from daily files
        for file in os.listdir(self.data_dir):
            if file.startswith("conversations_") and file.endswith(".json"):
                try:
                    with open(os.path.join(self.data_dir, file)) as f:
                        data = json.load(f)
                        conversations.extend([c for c in data if isinstance(c, dict)])
                except:
                    pass
        
        return conversations
    
    def extract_state_transitions(self, conversations):
        """Learn what triggers state changes"""
        transitions = []
        
        for i in range(len(conversations) - 1):
            curr = conversations[i]
            next_conv = conversations[i + 1]
            
            if not isinstance(curr, dict) or not isinstance(next_conv, dict):
                continue
                
            curr_state = curr.get("state", {})
            next_state = next_conv.get("state", {})
            
            if not isinstance(curr_state, dict) or not isinstance(next_state, dict):
                continue
            
            curr_emoji = curr_state.get("emoji")
            next_emoji = next_state.get("emoji")
            
            if curr_emoji and next_emoji and curr_emoji != next_emoji:
                # State changed - what was said?
                trigger_text = next_conv.get("content", "")
                
                transitions.append({
                    "from": curr_emoji,
                    "to": next_emoji,
                    "trigger": trigger_text[:100],
                    "timestamp": next_conv.get("timestamp", "")
                })
        
        return transitions
    
    def detect_loops(self, conversations):
        """Find spiral loops - same state repeating"""
        loops = []
        current_loop = []
        
        for conv in conversations:
            if not isinstance(conv, dict):
                continue
                
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
                if len(current_loop) >= 3:  # 3+ spirals in a row = loop
                    loops.append({
                        "duration": len(current_loop),
                        "start": current_loop[0]["timestamp"],
                        "end": current_loop[-1]["timestamp"],
                        "pattern": "spiral_loop"
                    })
                current_loop = []
        
        return loops
    
    def extract_language_patterns(self, conversations):
        """Learn AK's linguistic fingerprints per state"""
        state_language = defaultdict(lambda: {"words": [], "phrases": []})
        
        for conv in conversations:
            if not isinstance(conv, dict):
                continue
                
            state = conv.get("state", {})
            content = conv.get("content", "")
            
            if not isinstance(state, dict) or not content:
                continue
            
            emoji = state.get("emoji")
            if not emoji:
                continue
            
            # Extract key phrases
            words = content.lower().split()
            state_language[emoji]["words"].extend(words)
            
            # Extract multi-word phrases
            if len(words) >= 2:
                phrases = [" ".join(words[i:i+2]) for i in range(len(words)-1)]
                state_language[emoji]["phrases"].extend(phrases)
        
        # Calculate most common per state
        patterns = {}
        for emoji, data in state_language.items():
            word_freq = Counter(data["words"])
            phrase_freq = Counter(data["phrases"])
            
            patterns[emoji] = {
                "top_words": [w for w, c in word_freq.most_common(10) if len(w) > 3],
                "top_phrases": [p for p, c in phrase_freq.most_common(5)]
            }
        
        return patterns
    
    def detect_time_patterns(self, conversations):
        """When do different states occur? Time-based triggers."""
        time_states = defaultdict(list)
        
        for conv in conversations:
            if not isinstance(conv, dict):
                continue
                
            state = conv.get("state", {})
            timestamp = conv.get("timestamp", "")
            
            if not isinstance(state, dict) or not timestamp:
                continue
            
            emoji = state.get("emoji")
            if not emoji:
                continue
            
            try:
                dt = datetime.fromisoformat(timestamp)
                hour = dt.hour
                time_states[emoji].append(hour)
            except:
                continue
        
        # Find patterns
        patterns = {}
        for emoji, hours in time_states.items():
            if len(hours) < self.min_instances:
                continue
            
            hour_dist = Counter(hours)
            peak_hours = [h for h, c in hour_dist.most_common(3)]
            
            patterns[emoji] = {
                "peak_hours": peak_hours,
                "total_instances": len(hours),
                "distribution": dict(hour_dist)
            }
        
        return patterns
    
    def detect_contradictions(self, conversations):
        """Find when stated beliefs ≠ observed behavior"""
        contradictions = []
        
        # Look for "I always" or "I never" statements
        belief_pattern = r"(i always|i never|i don't|i do) (.+?)(?:\.|$)"
        
        stated_beliefs = []
        for conv in conversations:
            if not isinstance(conv, dict):
                continue
            
            content = conv.get("content", "").lower()
            matches = re.findall(belief_pattern, content)
            
            for prefix, claim in matches:
                stated_beliefs.append({
                    "claim": f"{prefix} {claim}",
                    "timestamp": conv.get("timestamp", ""),
                    "full_text": content
                })
        
        # TODO: Cross-reference with actual behavior
        # This is a placeholder - full implementation would check if behavior matches claims
        
        return stated_beliefs[:10]  # Top 10 for now
    
    def calculate_pattern_confidence(self, instances, total_opportunities):
        """Calculate confidence score for a pattern"""
        if total_opportunities == 0:
            return 0
        
        ratio = instances / total_opportunities
        
        # Boost confidence if many instances
        if instances >= 20:
            ratio = min(ratio * 1.1, 1.0)
        elif instances < self.min_instances:
            ratio *= 0.5  # Penalize low sample size
        
        return round(ratio * 100, 1)
    
    def generate_pattern_report(self):
        """Main extraction - generate full pattern analysis"""
        print("🧠 Auto-Pattern Extraction Engine")
        print("=" * 50)
        
        conversations = self.load_all_conversations()
        print(f"📊 Analyzing {len(conversations)} conversations...\n")
        
        if len(conversations) < self.min_instances:
            print("⚠️  Not enough data yet. Need at least 5 conversations.")
            return None
        
        # Extract all pattern types
        print("🔍 Detecting state transitions...")
        transitions = self.extract_state_transitions(conversations)
        
        print("🌀 Detecting loops...")
        loops = self.detect_loops(conversations)
        
        print("💬 Extracting language patterns...")
        language = self.extract_language_patterns(conversations)
        
        print("⏰ Finding time patterns...")
        time_patterns = self.detect_time_patterns(conversations)
        
        print("⚠️  Checking for contradictions...")
        contradictions = self.detect_contradictions(conversations)
        
        # Build report
        report = {
            "generated": datetime.now().isoformat(),
            "total_conversations": len(conversations),
            "analysis": {
                "state_transitions": {
                    "total": len(transitions),
                    "patterns": self._analyze_transitions(transitions)
                },
                "loops_detected": {
                    "total": len(loops),
                    "details": loops[:5]  # Top 5
                },
                "language_fingerprints": language,
                "time_patterns": time_patterns,
                "stated_beliefs": contradictions,
                "confidence_threshold": self.min_confidence
            }
        }
        
        # Save report
        os.makedirs(os.path.join(self.data_dir, "patterns"), exist_ok=True)
        report_file = os.path.join(
            self.data_dir, 
            "patterns", 
            f"auto_extracted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n✅ Pattern report saved: {report_file}")
        
        # Print summary
        self._print_summary(report)
        
        return report
    
    def _analyze_transitions(self, transitions):
        """Analyze state transition patterns"""
        transition_counts = Counter()
        
        for t in transitions:
            key = f"{t['from']} → {t['to']}"
            transition_counts[key] += 1
        
        # Only show patterns with min instances
        patterns = {}
        for transition, count in transition_counts.items():
            if count >= self.min_instances:
                confidence = self.calculate_pattern_confidence(count, len(transitions))
                if confidence >= self.min_confidence * 100:
                    patterns[transition] = {
                        "count": count,
                        "confidence": confidence
                    }
        
        return patterns
    
    def _print_summary(self, report):
        """Print human-readable summary"""
        print("\n" + "=" * 50)
        print("📋 PATTERN EXTRACTION SUMMARY")
        print("=" * 50)
        
        analysis = report["analysis"]
        
        # Transitions
        transitions = analysis["state_transitions"]["patterns"]
        if transitions:
            print("\n🔄 TOP STATE TRANSITIONS:")
            for trans, data in sorted(transitions.items(), key=lambda x: x[1]["count"], reverse=True)[:5]:
                print(f"  {trans}: {data['count']} times ({data['confidence']}% confidence)")
        
        # Loops
        loops = analysis["loops_detected"]["total"]
        if loops > 0:
            print(f"\n🌀 SPIRAL LOOPS DETECTED: {loops}")
            print("  (Times you got stuck in repetitive thinking)")
        
        # Language patterns
        lang = analysis["language_fingerprints"]
        if lang:
            print("\n💬 LANGUAGE FINGERPRINTS:")
            for emoji, patterns in list(lang.items())[:3]:
                if patterns["top_words"]:
                    print(f"  {emoji}: {', '.join(patterns['top_words'][:5])}")
        
        # Time patterns
        time_p = analysis["time_patterns"]
        if time_p:
            print("\n⏰ TIME PATTERNS:")
            for emoji, data in list(time_p.items())[:3]:
                hours = data["peak_hours"]
                print(f"  {emoji} peaks at: {', '.join(map(str, hours))}:00")
        
        print("\n" + "=" * 50)


if __name__ == "__main__":
    extractor = PatternExtractor()
    extractor.generate_pattern_report()
