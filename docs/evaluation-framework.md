# VRChat Agent Evaluation Framework

## 1. Baseline Setup
- **Agent A (GenieWorksheets VRChat Agent)**
  - Built using GenieWorksheets framework
  - Structured task/knowledge workflow
  - Integrated event database access
  - Type-safe state management

- **Agent B (GPT-4 Function Calling)**
  - Uses GPT-4 with function calling
  - Same KB access capabilities as Agent A
  - Basic state tracking through conversation
  - Uses function definitions for task structure

## 2. Evaluation Metrics

### Task Completion & Accuracy
- **Profile Information Capture Rate**: % of required fields correctly captured
- **Information Accuracy**: Correctness of captured user preferences
- **Recommendation Relevance**: Match between user preferences and recommended events

### Conversation Quality
- **Context Retention**: Maintaining correct user preferences through conversation
- **State Consistency**: Accuracy in maintaining user profile state

### System Robustness
- **Input Variation Handling**: Response to different ways of expressing preferences
- **Error Recovery**: Handling of unclear or contradictory inputs

## 3. Test Scenarios

### Basic Profile Creation
1. Direct path with all information provided clearly
2. Fragmented information provided across multiple turns
3. Correction of previously provided information

### Preference Elicitation
1. Explicit preference statements
2. Implicit preferences in conversation
3. Contradictory preferences

### Event Recommendations
1. Simple matching (direct preference match)
2. Complex matching (multiple preference factors)
3. Preference refinement based on feedback

## 4. Evaluation Methodology

### Scenario Testing
1. **Test Set Structure**
   - 30 scripted conversations covering all scenarios
   - Each conversation includes 5-10 turns
   - Varied user input patterns

2. **Testing Process**
   - Run identical scenarios through both agents
   - Record all interactions
   - Measure metrics for each turn

3. **Data Collection**
   - Agent responses
   - State tracking accuracy
   - Task completion success
   - Error recovery instances
