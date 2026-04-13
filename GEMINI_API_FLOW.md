# VitalAI Gemini API Call Flow Analysis

## User Journey: Load → Sign In → Log Workout → Get Insight → Chat

### Step-by-Step Breakdown

#### 1. **Load Dashboard Page**
```
GET / (dashboard.html)
```
- **Gemini API Calls**: ❌ **0**
- **Token Usage**: **0 tokens**
- **Details**: Loads static HTML, CSS, JavaScript. No backend API calls needed yet.

---

#### 2. **Sign In**
```
POST /api/auth/login
```
- **Gemini API Calls**: ❌ **0**
- **Token Usage**: **0 tokens**
- **Details**: 
  - Authenticates user credentials
  - Returns JWT token
  - No AI involved

---

#### 3. **Log Workout**
```
POST /api/logs/workout
Body: {
  "exercise_type": "Running",
  "duration_minutes": 30,
  "intensity": "moderate"
}
```

**Gemini API Call #1**: `ai_service.get_reaction("workout", context, entry)`
- **Model**: Gemini 2.5 Flash
- **Timeout**: 3 seconds
- **Input Tokens**: ~120-150
  - System persona: "You are VitalAI, a concise wellness assistant"
  - Log type instruction
  - Previous workout context (e.g., total workouts this week, avg intensity)
  - Current entry details
  - JSON schema example
- **Output Tokens**: ~40-60
  - JSON response: `{"type": "positive", "message": "Great 30-min run!", "tags": ["consistency"]}`
- **Total Tokens**: ~160-210 per request

**Response to Frontend**:
```json
{
  "exercise_type": "Running",
  "duration_minutes": 30,
  "intensity": "moderate",
  "reaction": {
    "type": "positive",
    "message": "Great 30-min run!",
    "tags": ["consistency"]
  }
}
```

---

#### 4. **Get Weekly Insights**
```
GET /api/insights/weekly
```

**Gemini API Call #2**: `ai_service.get_wellness_insights(user_id, context)`
- **Model**: Gemini 2.5 Flash
- **Timeout**: 15 seconds
- **Input Tokens**: ~350-450
  - System persona
  - Adaptive analysis instruction (based on data count: 0, 1-2, or 3+)
  - 7-day aggregated context:
    - Meals: count, avg calories
    - Workouts: count, total minutes (just updated with 1 new workout)
    - Sleep: count, avg quality
    - Hydration: avg ml, % of goal
    - Mood: count, avg score
  - JSON schema example
- **Output Tokens**: ~100-150
  - JSON response: `{"positives": [...], "concern": "...", "suggestions": [...]}`
- **Total Tokens**: ~450-600 per request

**Response to Frontend**:
```json
{
  "positives": [
    "Great consistency with workouts (just logged a 30-min run!)",
    "Sleep quality improving"
  ],
  "concern": "Haven't logged any meals this week",
  "suggestions": [
    "Start tracking meals to balance your routine",
    "Keep up the workout momentum",
    "Log mood daily to track mental health"
  ],
  "data_logged_categories": 2
}
```

---

#### 5. **Send Chat Message**
```
POST /api/chat
Body: {
  "message": "How can I improve my fitness routine?"
}
```

**Gemini API Call #3**: `ai_service.get_chat_response(message, history, context)`
- **Model**: Gemini 2.5 Flash
- **Timeout**: 10 seconds
- **Input Tokens**: ~250-350
  - System persona
  - Slimmed health context (key aggregates only):
    - Meal avg kcal, days logged
    - Sleep avg hours, avg quality
    - Hydration avg ml, % of goal
    - Workout sessions, avg intensity
    - Mood avg score
  - Chat history (1 user message only, just sent)
  - Instruction: "Reply empathetically in 2-4 sentences. Be supportive and actionable."
- **Output Tokens**: ~80-120
  - Natural language response: 2-4 sentences
  - E.g., "Your recent 30-minute run was excellent! To improve further, try gradually increasing duration or intensity. Keep tracking meals to fuel your workouts properly."
- **Total Tokens**: ~330-470 per request

**Response to Frontend**:
```json
{
  "reply": "Your recent 30-minute run was excellent! To improve, try gradually increasing either duration or intensity each week. Pairing workout logs with meal logs gives more complete insights into your energy and recovery.",
  "session_id": "507f1f77bcf86cd799439011"
}
```

---

## Summary Table

| Step | Endpoint | Gemini Call | Input Tokens | Output Tokens | Total | Notes |
|------|----------|------------|--------------|---------------|-------|-------|
| 1 | Load page | ❌ 0 | 0 | 0 | **0** | Static content only |
| 2 | Sign In | ❌ 0 | 0 | 0 | **0** | Authentication only |
| 3 | Log Workout | ✅ 1 | 120-150 | 40-60 | **160-210** | Quick reaction (3s timeout) |
| 4 | Get Insights | ✅ 1 | 350-450 | 100-150 | **450-600** | Comprehensive 7-day analysis (15s timeout) |
| 5 | Send Chat | ✅ 1 | 250-350 | 80-120 | **330-470** | Contextual conversation (10s timeout) |
| **TOTAL** | | **✅ 3** | **720-950** | **220-330** | **940-1280** | |

---

## API Call Cost Estimation

Using [Gemini 2.5 Flash pricing](https://ai.google.dev/pricing#gemini-flash):
- **Input**: $0.075 per 1M tokens
- **Output**: $0.30 per 1M tokens

**Cost for this scenario**:
```
Input:  (835 avg tokens) × ($0.075 / 1,000,000) = $0.0000626
Output: (275 avg tokens) × ($0.30 / 1,000,000) = $0.0000825
Total per scenario: ~$0.00015 (roughly $0.15 per 1000 scenarios)
```

---

## Key Observations

✅ **Efficient**: Only 3 API calls for a complete workflow
✅ **Context-Aware**: Each call uses minimal but relevant context
✅ **Fast**: 3-second timeouts for reactions, 15-second for insights, 10-second for chat
❌ **Not Cached**: Each request generates fresh API calls (no caching between users/sessions)
✅ **Graceful Degradation**: All endpoints have fallback responses if Gemini fails

---

## Optimization Opportunities

1. **Cache Weekly Insights**: Reuse same insights for 1 hour instead of recalculating per request
2. **Batch React Calls**: If logging 3 items at once, could batch reactions
3. **Reduce Context**: Already using "slim context" – further reduction possible but risky
4. **Rate Limit**: To prevent abuse, implement per-user API call limits

---

## Network Timeline (Rough Estimates)

```
User Action Timeline:
├─ T=0ms:    Load page (instant, static)
├─ T=100ms:  Sign in (auth, fast)
├─ T=500ms:  Log workout
│            └─ Network: 300ms
│            └─ Gemini API: 1-2s (model inference)
│            └─ Response: 800ms total
├─ T=1.5s:   Get insights
│            └─ Network: 300ms
│            └─ Database query: 200ms (7-day aggregation)
│            └─ Gemini API: 2-4s (comprehensive analysis)
│            └─ Response: 2.8s total
└─ T=4.5s:   Send chat
             └─ Network: 300ms
             └─ Gemini API: 1-2s
             └─ Session save: 500ms
             └─ Response: 2.0s total

Total: ~5-6 seconds for full workflow
```
