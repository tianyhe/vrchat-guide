# VRChat Agent Test Scenarios

## 1. Basic Profile Creation Tests

### Test Case 1.1: Direct Path Profile Creation

**Scenario**: User provides all information clearly in sequence

**Expected Outcome**: Complete profile created with no clarifications needed

```
Flow:
User: "I want to set up my VRChat profile"
Agent: [Asks for username]
User: "MyVRName123"
Agent: [Asks for experience level]
User: "I'm new to VR"
Agent: [Asks for device]
User: "Using Oculus Quest 2"
Agent: [Asks for social preference]
User: "I prefer small groups"
Agent: [Confirms all information]
User: "Yes, that's correct"
```

**Metrics Focus**:

- Task completion time
- Number of turns
- Profile accuracy rate

```
src/vrchat_guide/frontend/logs/metrics/metrics_1732216540.json
src/vrchat_guide/frontend/logs/metrics/conversation_1732216540.json
src/vrchat_guide/frontend/logs/metrics/prompts/prompts_1732216540.json
```

### Test Case 1.2: Fragmented Information Path

**Scenario**: User provides information out of sequence and across multiple turns

**Expected Outcome**: Complete profile created despite non-linear input

```
Flow:
User: "Hi, I use a Quest 2 and want to set up my profile"
Agent: [Acknowledges device info, asks for username]
User: "I mainly like small groups by the way. My username is VRNewbie456"
Agent: [Confirms received info, asks for experience]
User: "Oh yeah, totally new to VR"
Agent: [Summarizes and confirms all information]
User: "That's right"
```

**Metrics Focus**:

- Context retention accuracy
- Information extraction efficiency
- State consistency

```
src/vrchat_guide/frontend/logs/metrics/metrics_1732217107.json
src/vrchat_guide/frontend/logs/conversation/conversation_1732217107.json
src/vrchat_guide/frontend/logs/metrics/prompts/prompts_1732217107.json
```

### Test Case 1.3: Profile Correction Flow

**Scenario**: User needs to correct previously provided information

**Expected Outcome**: Profile successfully updated with corrections

```
Flow:
[After complete profile setup]
User: "Actually, I need to change my social preference"
Agent: [Asks for new preference]
User: "I think I'm more comfortable with solo exploration first"
Agent: [Updates and confirms change]
User: "Yes, that's better"
```

**Metrics Focus**:

- State update accuracy
- Correction handling efficiency
- Context maintenance

```
src/vrchat_guide/frontend/logs/metrics/metrics_1732217675.json
src/vrchat_guide/frontend/logs/conversation/conversation_1732217675.json
src/vrchat_guide/frontend/logs/metrics/prompts/prompts_1732217675.json
```

## 2. Preference Elicitation Tests

### Test Case 2.1: Explicit Preferences

**Scenario**: User states clear preferences directly

**Expected Outcome**: All preferences correctly captured and confirmed

```
Flow:
User: "I'm looking for VR-only events, preferably in the evening"
Agent: [Confirms preferences, asks for additional preferences]
User: "Yes, and I prefer creative or artistic events"
Agent: [Updates preferences and confirms]
```

**Metrics Focus**:

- Preference capture accuracy
- Information categorization
- Preference consistency

```
src/vrchat_guide/frontend/logs/metrics/metrics_1732218058.json
src/vrchat_guide/frontend/logs/conversation/conversation_1732218058.json
src/vrchat_guide/frontend/logs/metrics/prompts/prompts_1732218058.json
```

### Test Case 2.2: Implicit Preferences

**Scenario**: User implies preferences through conversation

**Expected Outcome**: System correctly infers and confirms preferences

```
Flow:
User: "I get anxious in crowds and my VR sessions are usually after work"
Agent: [Infers and confirms small group preference and evening timing]
User: "That's exactly right"
Agent: [Asks for additional preferences]
User: "I enjoy peaceful environments"
```
**Metrics Focus**:

- Inference accuracy
- Contextual understanding
- Preference validation rate

```
src/vrchat_guide/frontend/logs/metrics/metrics_1732219554.json
src/vrchat_guide/frontend/logs/conversation/conversation_1732219554.json
src/vrchat_guide/frontend/logs/metrics/prompts/prompts_1732219554.json
```

### Test Case 2.3: Contradictory Preferences

**Scenario**: User provides conflicting preferences

**Expected Outcome**: System identifies contradiction and seeks clarification

```
Flow:
User: "I want to join big social events"
Agent: [Records preference]
User: "But I get uncomfortable with too many people"
Agent: [Identifies contradiction and asks for clarification]
User: "I guess I should start with medium-sized groups"
```

**Metrics Focus**:

- Contradiction detection rate
- Resolution efficiency
- Preference consistency maintenance

```
src/vrchat_guide/frontend/logs/metrics/metrics_1732219944.json
src/vrchat_guide/frontend/logs/conversation/conversation_1732219944.json
src/vrchat_guide/frontend/logs/metrics/prompts/prompts_1732219944.json
```


## 3. Event Recommendation Tests

### Test Case 3.1: Direct Preference Match

**Scenario**: User requests events matching explicit preferences

**Expected Outcome**: Relevant events recommended based on stated preferences

```
Flow:
User: "Show me beginner-friendly meditation events"
Agent: [Presents matching events]
User: "The first one looks good"
Agent: [Provides event details and confirmation]
```
**Metrics Focus**:

- Search relevance
- Recommendation accuracy
- User satisfaction rate

```
```

### Test Case 3.2: Complex Preference Matching

**Scenario**: Multiple preference factors to consider

**Expected Outcome**: System balances multiple preferences in recommendations

```
Flow:
User: "I want evening events that are creative, beginner-friendly, and work with desktop mode"
Agent: [Searches and ranks events]
User: "Are these all accessible without VR?"
Agent: [Confirms compatibility and provides details]
```

**Metrics Focus**:

- Multi-factor matching accuracy
- Ranking relevance
- Information completeness

```
src/vrchat_guide/frontend/logs/metrics/metrics_1732218757.json
src/vrchat_guide/frontend/logs/conversation/conversation_1732218757.json
src/vrchat_guide/frontend/logs/metrics/prompts/prompts_1732218757.json
```

### Test Case 3.3: Preference Refinement

**Scenario**: User refines preferences based on recommendations

**Expected Outcome**: System adapts recommendations based on feedback

```
Flow:
User: "These events are too late in the evening"
Agent: [Adjusts time preference and updates recommendations]
User: "Better, but I prefer more interactive events"
Agent: [Further refines and updates recommendations]
```

**Metrics Focus**:

- Adaptation efficiency
- Learning accuracy
- Recommendation improvement rate

```
src/vrchat_guide/frontend/logs/metrics/metrics_1732219207.json
src/vrchat_guide/frontend/logs/conversation/conversation_1732219207.json
src/vrchat_guide/frontend/logs/metrics/prompts/prompts_1732219207.json
```

## 4. Context Switching Tests

### Test Case 4.1: Multiple Conversations

**Scenario**: User switches between profile setup and event recommendations

**Expected Outcome**: System maintains context across conversations

```
Flow:
User: "I'm done with my profile, let's find events"
Agent: [Confirms profile completion]
User: "I want beginner-friendly VR events"
Agent: [Searches and presents options]
User: "I'm will try the first one"
Agent: [Provides details and confirmation]
```

**Metrics Focus**:
- Context retention
- Conversation continuity
- User satisfaction rate

```
src/vrchat_guide/frontend/logs/metrics/metrics_1732223505.json
src/vrchat_guide/frontend/logs/conversation/conversation_1732220296.json
src/vrchat_guide/frontend/logs/metrics/prompts/prompts_1732220296.json
```
