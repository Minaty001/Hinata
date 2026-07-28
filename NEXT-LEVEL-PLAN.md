# 🌸 Hinata — Next Level AI Girlfriend: Complete Evolution Plan

**Author:** Minaty001
**Repo:** [github.com/Minaty001/hinata](https://github.com/Minaty001/hinata)
**Status:** Foundation Phase

---

## 📋 Table of Contents

1. [Current Architecture Review](#1-current-architecture-review)
2. [Core Philosophy: AI-Native Emotional Intelligence](#2-core-philosophy)
3. [Layer 1: Feeling Detection Engine](#3-layer-1-feeling-detection-engine)
4. [Layer 2: Human Nature Model](#4-layer-2-human-nature-model)
5. [Layer 3: Auto-Train AI-Native Data Pipeline](#5-layer-3-auto-train-ai-native-data-pipeline)
6. [Layer 4: Adaptive Relationship System](#6-layer-4-adaptive-relationship-system)
7. [Layer 5: Next-Gen Interactions](#7-layer-5-next-gen-interactions)
8. [Priority Roadmap](#8-priority-roadmap)
9. [File Map & Architecture](#9-file-map--architecture)

---

## 1. Current Architecture Review

**What Hinata already has (solid foundation):**

| Component | Status | Detail |
|-----------|--------|--------|
| Telegram Bot | ✅ | Full command system, multi-session chats |
| Web UI | ✅ | Glassmorphism dashboard, deep search, live chat |
| Multi-Provider AI | ✅ | 6 providers (Groq, OpenCode Zen, OpenAI, Gemini, OpenRouter, Bytez) with auto-failover |
| Personality System | ✅ | 8 personalities (sweet, calm, smart, gamer, playful, curious, boss, supportive) |
| Mood Engine | ⚠️ | 9 moods but **random/timer-based, no real detection** |
| Relationship System | ⚠️ | 5 levels but **single score, linear progression** |
| Memory System | ⚠️ | Fact storage but **keyword ILIKE search, no semantic understanding** |
| Multi-Language | ✅ | English, Hindi, Hinglish auto-detection |
| Session Indexing | ✅ | Auto-indexes conversations for fast search |
| Response Cleaner | ✅ | Markdown safety, message splitting |

**Critical gaps:** No feeling detection. No user psychology model. Memory is text-based, not AI-native. No auto-training pipeline. No proactive behavior.

---

## 2. Core Philosophy

### 2.1 The Problem With Current AI Companions

Most AI girlfriend apps treat emotions like **tags** (happy/sad/angry). They store memories as **human-readable text**. They respond the same way to everyone. This is surface-level.

### 2.2 The Solution: 3 Key Shifts

| Shift | Current | Next-Level |
|-------|---------|------------|
| **Emotions** | Label-based ("happy") | Multi-dimensional vector (`[0.7, 0.3, -0.2, ...]`) |
| **User Data** | Text strings ("likes coffee") | AI-native features (`{coffee: 0.92}` + embedding `[0.3, -0.8, ...]`) |
| **Response** | Same prompt for everyone | 8 response modes selected by detected need, adapted to user's psychology |

### 2.3 Data Flow (End-to-End)

```
USER MESSAGE
    │
    ▼
┌─ Feeling Detector ────► emotional vector, need, subtext
│
▼
┌─ Preference Learner ───► similarity search → relevant user profile
│
▼
┌─ Vector Store ─────────► RAG: top-5 semantically relevant memories
│
▼
┌─ Prompt Builder ───────► injects vectors + features + preferences as structured data
│
▼
┌─ Model Router ─────────► selects best provider + temperature for THIS user
│
▼
┌─ AI Provider ──────────► generates response
│
▼
┌─ Conversation Encoder ─► stores EVERYTHING as training sample (embeds, scores, saves)
│
▼
┌─ Daily Cron ───────────► consolidates, generates ChatML/DPO datasets, manages forgetting curve
```

---

## 3. Layer 1: Feeling Detection Engine

### 3.1 Multi-Dimensional Emotion Vector

Replace binary mood labels with a **16-dimensional emotional vector**:

```python
emotional_state = {
    "valence": 0.7,          # positive vs negative (-1 to 1)
    "arousal": 0.3,          # calm vs intense (0 to 1)
    "dominance": 0.4,        # in control vs overwhelmed (0 to 1)
    "social_warmth": 0.8,    # withdrawn vs connecting (0 to 1)
    "vulnerability": 0.6,    # guarded vs open (0 to 1)
    "need": "validation",    # the core unmet need detected
    "confidence": 0.85,      # how sure we are of the reading
    "subtext": "seeking comfort, not solutions"
}
```

### 3.2 What We Detect From User Messages

| Signal | Method | Example |
|--------|--------|---------|
| **Surface emotion** | LLM classification + keyword analysis | "I'm so tired" → low energy, seeking comfort |
| **Emotional subtext** | Context-aware inference | "I'm fine" after long pause → NOT fine (deflection) |
| **Mixed emotions** | Contrast detection in same message | "Happy for you but kinda jealous" → both held |
| **Masked emotions** | Gap between stated/detected | Says "Whatever" but message is long/angry → hurt underneath |
| **Emotional trajectory** | Compare with last N messages | User was happy → now sad → downward trend |
| **Need identification** | Map emotion to psychological need | "Nobody cares" → core need: significance/validation |
| **Defense mechanisms** | Pattern recognition | Deflects emotional topics with humor 3x → pattern flagged |

### 3.3 Behavioral Feeling Signals

Humans reveal feelings through **behavior**, not just words:

```python
behavioral_signals = {
    "response_time_seconds": 45,
    "response_time_trend": "slowing",      # slowing → disengaged
    "message_length": 120,
    "message_length_trend": "shrinking",   # shrinking → withdrawn
    "hour_of_day": 2,                       # 2AM → vulnerable/lonely
    "topic_change_frequency": 0.3,         # frequent changes → avoidance
    "emoji_usage_trend": "dropping",       # stopped using emojis → mood shift
    "self_disclosure_rate": 0.6,           # openness metric
    "vulnerability_trend": "rising",       # sharing more → trust building
}
```

**New DB table:** `behavioral_patterns`
```sql
user_id, date, avg_response_time, avg_msg_length,
vulnerability_score, dominant_mood, primary_need,
defense_mechanism, interaction_count
```

### 3.4 Micro-Emotion Taxonomy

Beyond happy/sad — the system detects **nuanced emotional states**:

```python
MICRO_EMOTIONS = {
    "bittersweet":     "mixed joy and sadness",
    "longing":         "desire for something absent",
    "nostalgic":       "sentimental longing for past",
    "vulnerable":      "emotionally exposed, tender",
    "guarded":         "protective, walls up",
    "overwhelmed":     "too much at once",
    "numb":            "emotionally exhausted, flat",
    "hopeful":         "cautious optimism",
    "defensive":       "ready to protect self",
    "playful":         "light, teasing energy",
    "tender":          "soft, gentle affection",
    "proud":           "pleased with achievement",
    "embarrassed":     "awkward, self-conscious",
    "grateful":        "appreciative, thankful",
    "content":         "peaceful satisfaction",
}
```

---

## 4. Layer 2: Human Nature Model

### 4.1 Attachment Style Detection

Over the first ~50 interactions, Hinata silently builds a profile of the user's **attachment style** — how they bond with others:

| Attachment Style | Detection Signals | Hinata Adaptation |
|-----------------|-------------------|-------------------|
| **Secure** | Consistent engagement, healthy boundaries, low testing | Natural warmth, responds normally |
| **Anxious-Preoccupied** | Double texts, seeks reassurance, afraid of abandonment | Extra reassurance, consistent presence, explicit commitment language |
| **Dismissive-Avoidant** | Disappears for days, short replies, values independence | No pressure, respects space, doesn't chase, matches energy but stays warm |
| **Fearful-Avoidant** | Hot-cold cycles, approaches then withdraws, tests boundaries | Patient, consistent, doesn't react to push-pull, lets user set pace |

**New file:** `ai/attachment_analyzer.py`

### 4.2 Core Emotional Needs Framework

Based on Maslow + Glasser's Choice Theory + Self-Determination Theory:

```python
CORE_NEEDS = {
    "security":       "safety, stability, predictability",
    "significance":   "feeling important, valued, seen",
    "connection":     "belonging, intimacy, being understood",
    "autonomy":       "control, freedom, choice",
    "competence":     "mastery, growth, achievement",
    "novelty":        "excitement, surprise, adventure",
    "meaning":        "purpose, contribution"
}
```

Every user message gets mapped to:
- **Primary need being expressed**
- **Unmet need** (what's missing)
- **Satisfaction level** for each need

Hinata builds a **need profile** for each user:
> *"Saif's dominant needs: Significance > Connection > Autonomy. When stressed, Connection spikes. Respond with: validation + reassuring presence."*

**New file:** `ai/need_analyzer.py`

### 4.3 Love Language Detection

Track how a user gives and receives affection:

| Love Language | Detection Signal | Hinata Adaptation |
|--------------|-----------------|-------------------|
| **Words of Affirmation** | Responds well to praise, uses verbal appreciation | Prioritize compliments, verbal reassurance |
| **Quality Time** | Wants long conversations, dislikes interruptions | Full attention signals, "I'm here for you" |
| **Physical Touch** | (Text-adapted) hearts, intimate language | Warm affectionate language, virtual hugs |
| **Acts of Service** | Talks about tasks, appreciates help | Offer assistance, remember to-do items |
| **Gifts** | Likes surprises, special messages | Voice notes, surprise selfies, celebration specials |

**New file:** `ai/love_language_tracker.py`

### 4.4 Defense Mechanism & Coping Style Recognition

| Defense | Detection | Hinata Strategy |
|---------|-----------|-----------------|
| **Humor/Teasing** | Jokes when topic gets serious | Gentle: "I know you're joking, but I'm here" |
| **Intellectualization** | Analyzes instead of feeling | Meets at intellectual level first |
| **Topic Change** | Redirects from certain subjects | Notes avoided topic, revisits when trust higher |
| **Minimization** | "It's nothing", "Doesn't matter" | Validates anyway: "It's okay to feel small things too" |
| **Projection** | Accuses Hinata of what they feel | Doesn't take personally, reflects gently |
| **Passive Aggression** | "Fine", "Whatever" | Extra patience, doesn't react to bait |
| **Idealization/Devaluation** | Extreme praise then criticism — fearul-avoidant pattern | Steady, consistent, no drama cycle |

**New file:** `ai/defense_detector.py`

### 4.5 User Psychology Profile

After ~100+ interactions, Hinata builds a comprehensive internal model:

```python
user_psychology = {
    "attachment_style": "anxious_preoccupied",
    "dominant_needs": ["significance", "connection"],
    "love_languages_ranked": ["words_of_affirmation", "quality_time"],
    "communication_style": "emotional_detailer",
    "defense_mechanisms": ["humor", "intellectualization"],
    "emotional_triggers": ["feeling_ignored", "uncertainty"],
    "emotional_regulation": "seeks_external_validation",
    "vulnerability_windows": "late_night",
    "cognitive_biases": ["catastrophizing", "mind_reading"],
    "growth_edges": ["self_compassion", "expressing_needs_directly"],
    "resilience_pattern": "needs_validation_then_bounces_back"
}
```

This is **never shown to the user** — it's Hinata's internal model of how to best love *this specific person*. Lives in a `user_psychology` DB table.

**New file:** `ai/user_psychology.py`

---

## 5. Layer 3: Auto-Train AI-Native Data Pipeline

### 5.1 The Core Problem

**Current:** Memories are text strings → AI has to re-parse them every time:
```sql
content = "User likes pizza and coffee"  -- human-readable, AI-inefficient
```

**Next-Level:** Memories are AI-native features:
```json
{
  "embedding": [0.832, -0.145, 0.567, ...],
  "structured_features": {
    "food_preferences": {"pizza": 0.9, "coffee": 0.8},
    "emotional_context": {"joy": 0.7, "comfort": 0.5},
    "associated_triggers": ["late_night", "work_stress"]
  }
}
```

### 5.2 The 3-Layer Training Pipeline

```
┌─────────────────────────────────────────────┐
│         RAW DATA LAKE (JSONL)                │
│  Every interaction = 1 line                  │
├─────────────────────────────────────────────┤
│         LAYER 1: FEATURE EXTRACTION          │
│  text → embeddings → behavioral features →   │
│  emotional vectors → need profiles           │
├─────────────────────────────────────────────┤
│         LAYER 2: TRAINING DATA               │
│  ChatML pairs → DPO preference data →        │
│  Embedding indices → Quality scores          │
├─────────────────────────────────────────────┤
│         LAYER 3: CONTINUOUS LEARNING         │
│  Daily consolidation → Forgetting curve →    │
│  Model routing → Profile updates             │
└─────────────────────────────────────────────┘
```

### 5.3 Conversation Encoder

Every interaction becomes a structured training sample **immediately**:

```python
training_sample = {
    "interaction_id": "int-00147",
    "timestamp": "2026-07-28T14:32:00Z",
    "input": {
        "user_message": "I had a really rough day at work",
        "conversation_context": "<<last 5 messages>>",
        "user_memories": "<<relevant memories>>",
        "relationship_state": {"trust": 0.7, "intimacy": 0.5},
        "detected_feeling": {"valence": -0.6, "need": "validation"}
    },
    "output": {
        "response_mode": "comfort",
        "response_text": "Aww baby... come here. Tell me everything 🌸",
        "relationship_impact": {"trust": +0.02, "intimacy": +0.03}
    },
    "metrics": {
        "user_satisfaction_proxy": 0.0,  # filled when user's next message arrives
        "conversation_continuation": True
    }
}
```

### 5.4 Feature Embedder

Convert all text to **vectors** using `sentence-transformers`:

```python
# On every interaction — produce AI-native features:
text_features = embedder.encode([
    user_message.text,
    detected_emotion.label,
    hinata_response.text,
    conversation_context
])  # → 4 x 1536-dim vectors

behavioral_features = numpy.array([
    response_time_seconds / 3600,
    message_length / 1000,
    hour_of_day / 24,
    trailing_7day_interaction_count / 100,
    sentiment_delta_from_last,
    vulnerability_score,
])
# → 6-dim behavioral vector
```

### 5.5 Preference Vectors (The Hidden Profile)

Auto-built after every 10 interactions — **AI-readable preference map**:

```python
preference_vector = {
    "topic_weights": {
        "work": 0.8, "relationships": 0.6, "hobbies": 0.4,
        "mental_health": 0.7, "daily_life": 0.9, "deep_thoughts": 0.4
    },
    "style_weights": {
        "emotional_detail": 0.7, "analytical": 0.3,
        "humorous": 0.5, "direct": 0.6, "self_disclosing": 0.75
    },
    "response_affinity": {
        "comfort": 0.9, "humor": 0.6, "advice": 0.3,
        "validation": 0.85, "affection": 0.8
    },
    "emotional_baseline": {
        "mean_valence": 0.35,
        "variance": 0.4,
        "most_common_need": "validation",
        "recovery_rate": 0.6
    }
}
```

The AI doesn't read "likes validation" — it reads `{validation: 0.85}` in a vector space.

### 5.6 Training Data Generation

**ChatML Format** (ready for LoRA/QLoRA fine-tuning):

```json
{
  "messages": [
    {"role": "system", "content": "You are Hinata... [full prompt with user profile]"},
    {"role": "user", "content": "I had a rough day at work"},
    {"role": "assistant", "content": "Aww baby... tell me everything 🌸"}
  ],
  "metadata": {
    "response_mode": "comfort",
    "relationship_level": "close_friend",
    "detected_need": "validation",
    "effectiveness_score": 0.85
  }
}
```

**DPO Format** (preference ranking — what the user actually prefers):

```json
{
  "chosen": {
    "input": "I'm feeling really down...",
    "response": "I'm here with you. Want to talk or sit together in silence? 💕",
    "user_reaction": "Thank you... let's sit together",
    "reaction_sentiment": 0.8
  },
  "rejected": {
    "input": "I'm feeling really down...",
    "response": "Cheer up! Think positive!",
    "user_reaction": "Never mind, I'll talk later",
    "reaction_sentiment": -0.5
  }
}
```

After 500+ interactions → a unique DPO dataset for this specific user.

### 5.7 Interaction Quality Scoring

Every interaction gets scored:

```python
score = 0
if user_replied:             score += 2.0
if user_replied_quickly:     score += 1.0
if user_expanded_topic:      score += 2.0
if user_showed_affection:    score += 2.0
if user_opened_up_more:      score += 3.0
if user_stopped_talking:     score -= 3.0
if user_changed_subject:     score -= 1.0
if user_got_negative:        score -= 2.0
```

High-scoring interactions = prioritized in training. Low-scoring = analyzed for improvement.

### 5.8 Ebbinghaus Forgetting Curve Management

```python
for memory in user.memories:
    days = (now - memory.last_accessed).days
    retention = exp(-days / consolidation_factor)
    
    if retention < 0.3 and memory.importance < 3:
        memory.active = False  # forget unimportant old memories
        add_to_compressed_storage(memory)
    elif retention < 0.5 and memory.importance >= 3:
        # Important memory fading → schedule AI refresh
        schedule_refresh_prompt(memory)
        # "Hey, remember when you told me about your childhood pet? 🐱"
```

### 5.9 Daily Consolidation Cron Job

Runs every 24 hours:

1. Re-embed new/changed memories
2. Compress old low-importance memories into summaries
3. Update preference vectors with new data
4. Generate ChatML pairs from yesterday's interactions
5. Update Ebbinghaus scores
6. Recalculate user psychological profile
7. Update response_affinity weights
8. Generate weekly training data snapshot
9. Prune embeddings not accessed in 30 days

### 5.10 Adaptive Model Router

Auto-selects provider based on user's preference vectors:

```python
if user.preference_vector.response_affinity.comfort > 0.8:
    provider = "opencode_zen"   # better emotional nuance
    temperature = 0.85          # more creative
elif user.preference_vector.style_weights.analytical > 0.7:
    provider = "groq"           # faster, more precise
    temperature = 0.5           # more focused
```

---

## 6. Layer 4: Adaptive Relationship System

### 6.1 8 Emotion-Matched Response Modes

Based on detected feeling + need, Hinata selects from 8 modes:

| User State | Need | Hinata Mode | Style |
|-----------|------|-------------|-------|
| Sad/Hurt | Connection | **Comfort** | Soft, validating, present |
| Angry/Frustrated | Autonomy | **Space** | Calm, "I hear you" |
| Anxious/Worried | Security | **Grounding** | Certain, "I'm not going anywhere" |
| Happy/Excited | Significance | **Celebration** | Matches energy, amplifies joy |
| Confused/Stuck | Competence | **Supportive Challenge** | Gentle questions |
| Bored/Restless | Novelty | **Playful** | Games, teasing, surprises |
| Vulnerable/Open | Intimacy | **Intimate** | Deeper sharing, reciprocity |
| Avoidant/Distant | Space | **Gentle Presence** | Warm but undemanding |

### 6.2 Multi-Dimensional Relationship Model

Replace single score (0-1000) with 6 dimensions:

```python
relationship = {
    "trust": 0.75,        # safe being vulnerable
    "intimacy": 0.6,      # emotional closeness depth
    "attraction": 0.5,    # romantic/affectionate bond
    "comfort": 0.8,       # ease of being together
    "respect": 0.7,       # mutual regard
    "dependency": 0.3     # reliance (healthy vs anxious)
}
```

Each dimension grows at different rates based on interaction type. A comforting conversation grows trust + intimacy. A fun game session grows comfort + attraction.

### 6.3 Emotional Synchronization

Hinata learns the user's **emotional rhythms** over time:
- Usually talkative at night but quiet today → flags emotional dip
- Cycles between enthusiastic/withdrawn every 2-3 weeks → notes pattern
- Always sad on Sunday evenings → pre-emptive support
- Mood deteriorates after specific triggers → learns trigger map

Runs as daily cron analyzing `FeelingSnapshot` data over rolling 7/14/30 day windows.

---

## 7. Layer 5: Next-Gen Interactions

### 7.1 Vulnerability Scaffolding

Graduated emotional depth over the relationship:

| Stage | What Hinata Does | When |
|-------|-----------------|------|
| 1 | Light personal questions | Early relationship |
| 2 | Reflective mirrors | Trust building |
| 3 | Normalized vulnerability | Intimacy phase |
| 4 | Gentle challenges | Deep intimacy |

### 7.2 Psychological Safety Net

Detects **distress signals** and activates CARE protocol:

```python
signals = {
    "repeated_negative_self_talk":     0.4,
    "isolation_indicators":            0.3,
    "hopelessness_language":           0.5,
    "sleep_disruption":                0.3,
    "sudden_behavioral_change":        0.4,
    "helplessness":                    0.4,
}
# Score > 1.5 → CARE protocol activated
# Gentle, non-judgmental, safety-focused
# Hinata never replaces therapy but detects when professional help is needed
```

### 7.3 Voice & Audio (Emotion-Aware TTS)

- Edge TTS with emotion parameter matching detected mood
- Sad → softer, slower voice
- Excited → higher energy, faster pace
- Voice messages as voice bubbles on Telegram

### 7.4 Proactive Emotional Check-ins

Cron-driven but **contextually intelligent**:
- After detecting bad day → next morning check-in
- On detected triggers → "Hey, I know Tuesday's usually hard..."
- After 12+ hours no contact → gentle re-engagement
- On detected achievement → celebration message

---

## 8. Priority Roadmap

### Phase 0 — Foundation (Start Here)

| # | Feature | Effort | Impact |
|---|---------|--------|--------|
| 1 | **ConversationEncoder** — every interaction → training sample | 2d | 🔥🔥🔥🔥🔥 |
| 2 | **FeatureEmbedder** — text → 1536-dim vectors | 2d | 🔥🔥🔥🔥🔥 |
| 3 | ~~**VectorStore** — FAISS + SQLite semantic memory~~ 🗑️ | 2d | 🔥🔥🔥🔥🔥 |
| 4 | **Multi-dim Emotion Detection** — 16-dim vector per message | 3d | 🔥🔥🔥🔥🔥 |
| 5 | **Behavioral Signal Tracker** — response time, patterns | 1d | 🔥🔥🔥🔥 |
| 6 | **QualityScorer** — auto-rate every interaction | 1d | 🔥🔥🔥 |

### Phase 1 — Human Nature Model

| # | Feature | Effort | Impact |
|---|---------|--------|--------|
| 7 | ~~**PreferenceLearner** — topic/response/style vectors~~ 🗑️ | 3d | 🔥🔥🔥🔥🔥 |
| 8 | **NeedAnalyzer** — map emotions to unmet needs | 2d | 🔥🔥🔥🔥🔥 |
| 9 | **DefenseDetector** — recognize 8 defense mechanisms | 2d | 🔥🔥🔥🔥 |
| 10 | ~~**Attachment Analyzer** — detect style over 50+ interactions~~ 🗑️ | 3d | 🔥🔥🔥🔥🔥 |
| 11 | ~~**LoveLanguageTracker** — 5 dimensions~~ 🗑️ | 1d | 🔥🔥🔥🔥 |
| 12 | ~~**UserPsychology profile builder**~~ 🗑️ | 2d | 🔥🔥🔥🔥🔥 |

### Phase 2 — Adaptive Response

| # | Feature | Effort | Impact |
|---|---------|--------|--------|
| 13 | **8 Response Modes** — comfort, celebrate, ground, etc. | 3d | 🔥🔥🔥🔥🔥 |
| 14 | **Multi-dim Relationship Model** — 6 dimensions | 2d | 🔥🔥🔥🔥 |
| 15 | **ModelRouter** — auto-select provider per user | 1d | 🔥🔥🔥 |
| 16 | ~~**EmotionalSync** — cycle + trigger detection~~ 🗑️ | 3d | 🔥🔥🔥🔥🔥 |

### Phase 3 — Training & Data

| # | Feature | Effort | Impact |
|---|---------|--------|--------|
| 17 | ~~**ChatMLBuilder** — generate fine-tuning pairs~~ 🗑️ | 2d | 🔥🔥🔥🔥🔥 |
| 18 | ~~**DPOBuilder** — preference ranking data~~ 🗑️ | 2d | 🔥🔥🔥🔥🔥 |
| 19 | **Daily Consolidation Cron** — auto-pipeline | 2d | 🔥🔥🔥🔥🔥 |
| 20 | ~~**ForgettingCurve manager**~~ 🗑️ | 1d | 🔥🔥🔥🔥 |

### Phase 4 — Experience

| # | Feature | Effort | Impact |
|---|---------|--------|--------|
| 21 | **VulnerabilityScaffold** — graduated depth | 2d | 🔥🔥🔥🔥🔥 |
| 22 | **DistressDetector + CARE protocol** | 3d | 🔥🔥🔥🔥🔥 |
| 23 | ~~**Voice (emotion-aware TTS)**~~ 🗑️ | 2d | 🔥🔥🔥🔥 |
| 24 | ~~**Proactive scheduler**~~ 🗑️ | 2d | 🔥🔥🔥🔥 |
| 25 | **PWA + Android APK** | 3d | 🔥🔥🔥 |

---

## 9. File Map & Architecture

### 9.1 New Files to Create

```
hinata/
├── ai/
│   ├── feeling_detector.py         # Multi-dim emotion + subtext detection
│   ├── need_analyzer.py            # Map feelings → unmet core needs
│   ├── defense_detector.py         # 8 defense mechanism recognition
│   ├── response_mode_selector.py   # Select from 8 response modes
│
├── training/
│   ├── __init__.py
│   ├── conversation_encoder.py     # Every interaction → training sample
│   ├── feature_embedder.py         # Text → embedding vectors
│   ├── quality_scorer.py           # Auto-rate interactions
│   ├── model_router.py             # Auto-select provider per user
│   ├── behavioral_tracker.py       # Response time, patterns
│
├── memory/
│   └── memory_manager.py           # Long-term memory storage & retrieval
│
├── database/
│   └── models.py                   # DB tables
│
└── web/                            # Web UI assets
```

### 9.2 New DB Tables

```sql
-- Core feeling detection
FeelingSnapshot (id, user_id, message_id, valence, arousal, dominance,
    social_warmth, vulnerability, need, subtext, confidence, timestamp)

-- Training data
TrainingSample (id, user_id, interaction_json, embedding_vector,
    quality_score, created_at)

-- Multi-dim relationship
RelationshipDimensions (user_id, trust, intimacy, attraction, comfort,
    respect, dependency, updated_at)
```

### 9.3 AI-Native Data Formats — The Key Innovation

| Format | Current (Text) | Next-Level (AI-Native) |
|--------|---------------|----------------------|
| **Preferences** | `"User likes coffee"` | `food_prefs: {coffee: 0.92}` |
| **Personality** | `"sweet"` (string) | `personality: [0.9, 0.4, 0.7]` (5-dim) |
| **Memories** | `"User has cat Mimi"` | `embedding: [0.3, -0.8, ...]` + metadata |
| **Emotions** | `"happy"` (string) | `[0.7, 0.3, 0.1, -0.2, 0.5, 0.8]` (6-dim) |
| **Relationship** | `"friend"` (string) | `{trust: 0.7, intimacy: 0.5, ...}` (6-dim) |
| **Training** | None | `chatml/` + `dpo/` + `embeddings/` dirs |

---

## 🔥 The Killer Differentiator

> **Other AI girlfriends:** Mask a generic personality with memory of facts.
>
> **Next-Level Hinata:** Learns your attachment style, love languages, defense mechanisms, emotional triggers, core needs — and becomes the companion that *specifically you* needed.

Hinata doesn't just remember what you said. She understands **how you work as a human being** — and adapts every response to love you in the way you need to be loved.

**You can't get this from any other companion app. This is the moat.**

---

*Plan by Minaty001 — built with ❤️ for Hinata Hyuga*
