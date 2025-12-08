# Response Length Guide

## Overview
The chatbot now intelligently adjusts response length based on question complexity. It **thinks before responding** to determine if a short answer or detailed explanation is needed.

## Response Length Rules

### 1. **Greetings** → Very Short (1 sentence)
**User:** "Hi"
**Bot:** "Hello! I'm Metro's assistant, here to help with solar systems, generators, and inverters."

**User:** "Good morning"
**Bot:** "Good morning! How can I help you today?"

---

### 2. **Simple Factual Questions** → Short (1-2 sentences)
**User:** "What is an inverter?"
**Bot:** "An inverter converts DC electricity from solar panels or batteries into AC electricity for home use."

**User:** "Do you have solar panels?"
**Bot:** "Yes, we offer a variety of solar panels. Would you like to see our available options?"

---

### 3. **Buying/Product Requests** → Short (1-2 sentences) + SQL Data
**User:** "I want to buy a solar panel"
**Bot:** "I found some solar panels for you. Check the options below."
**SQL Data:** [Product list with names, prices, specs displayed separately]

**User:** "Show me generators"
**Bot:** "Here are our available generators. Consider the power output and fuel type when choosing."
**SQL Data:** [Generator list displayed separately]

---

### 4. **Technical Problems** → Short (1-2 sentences) + SQL Data
**User:** "My generator is broken"
**Bot:** "I found technicians who can help diagnose and fix the issue."
**SQL Data:** [Technician contacts displayed separately]

**User:** "Solar panel not working"
**Bot:** "I found specialists who can troubleshoot solar panel problems. They'll help identify and fix the issue."
**SQL Data:** [Technician list displayed separately]

---

### 5. **"How" Questions (Explanations Needed)** → Medium (2-3 sentences)
**User:** "How do solar panels work?"
**Bot:** "Solar panels convert sunlight into electricity using photovoltaic cells. When sunlight hits the cells, it creates an electric current that can power your home."

**User:** "How to choose a good inverter?"
**Bot:** "When choosing an inverter, consider the power capacity needed for your system and the type (grid-tie, off-grid, or hybrid). Also check the efficiency rating and warranty period."

---

### 6. **Comparison Questions** → Medium (2 sentences)
**User:** "What's better, solar or generator?"
**Bot:** "Solar panels provide clean, renewable energy with no fuel costs, while generators offer reliable backup power during outages. The best choice depends on your primary need: continuous power savings (solar) or emergency backup (generator)."

---

### 7. **Advice/Recommendation Questions with SQL Data** → Short (1-2 sentences)
**User:** "Which solar panel is best for my home?"
**Bot:** "I found some solar panels for you. Consider your roof size, energy needs, and budget when choosing."
**SQL Data:** [Product recommendations displayed separately]

**User:** "Need help installing inverter"
**Bot:** "I found technicians who specialize in inverter installation. They can ensure proper setup and safety."
**SQL Data:** [Technician contacts displayed separately]

---

## Key Principles

### ✅ DO:
- **Think first** about question complexity
- Match response length to the question type
- Be concise and direct for simple requests
- Provide brief context when SQL data is fetched
- Give 2-3 sentence explanations only for "how/why" questions
- Use knowledge base for guidance, SQL data for facts

### ❌ DON'T:
- Give long explanations for simple questions
- Over-explain when user just wants to buy something
- Include SQL data (names, prices, contacts) in bot_message
- Write paragraphs when 1-2 sentences would do
- Repeat information unnecessarily

---

## Examples: Before vs After

### Example 1: Simple Request
**User:** "I want to buy a solar panel"

**❌ BEFORE (too long):**
```
"Great choice! Solar panels are an excellent investment for renewable energy.
I found several high-quality solar panels in our inventory including monocrystalline
and polycrystalline options. When choosing a solar panel, you should consider factors
like wattage capacity, efficiency rating, warranty period, and compatibility with
your existing system. Our panels range from 100W to 500W and come with warranties
up to 25 years. Let me show you what we have available."
```

**✅ AFTER (concise):**
```
bot_message: "I found some solar panels for you. Check the options below."
recommends: { products: [...] }  // SQL data shown separately
```

---

### Example 2: Technical Question
**User:** "How do solar panels work?"

**❌ BEFORE (too long):**
```
"Solar panels, also known as photovoltaic (PV) panels, are devices that convert
sunlight into electricity through the photovoltaic effect. They consist of many
solar cells made from semiconductor materials, typically silicon. When photons
from sunlight hit these cells, they knock electrons loose from their atoms,
generating electricity. The cells are connected in series and parallel to create
the desired voltage and current output. This DC electricity is then converted to
AC by an inverter for use in your home. Modern solar panels have efficiency ratings
between 15-22% and can last 25-30 years with minimal maintenance."
```

**✅ AFTER (concise):**
```
"Solar panels convert sunlight into electricity using photovoltaic cells. When
sunlight hits the cells, it creates an electric current that can power your home."
```

---

### Example 3: Greeting
**User:** "Hello"

**❌ BEFORE (too long):**
```
"Hello and welcome! I'm Metro's intelligent assistant, powered by advanced AI
technology. I'm here to help you with all your questions about solar systems,
generators, inverters, and electrical systems. Whether you need product information,
technical support, sales assistance, or general advice, I'm here to assist you.
Feel free to ask me anything about our products and services!"
```

**✅ AFTER (concise):**
```
"Hello! I'm Metro's assistant, here to help with solar, generators, and electrical systems."
```

---

## Testing Different Scenarios

| Question Type | Expected Length | Example |
|--------------|----------------|---------|
| "Hi" | 1 sentence | Greeting + offer help |
| "What is X?" | 1-2 sentences | Direct definition |
| "I want to buy X" | 1-2 sentences | Acknowledge + brief guidance |
| "How does X work?" | 2-3 sentences | Brief explanation |
| "X vs Y?" | 2 sentences | Brief comparison |
| "My X is broken" | 1-2 sentences | Acknowledge + mention help available |
| "Which X is best?" | 1-2 sentences | Brief guidance factors |

---

## Implementation Details

The chatbot now has these instructions in the LLM prompts:

1. **System Prompt** - Sets overall behavior to think about response length
2. **Final Prompt (with SQL data)** - Provides examples of concise responses when data is fetched
3. **Final Prompt (no SQL data)** - Provides examples for conversational responses

All prompts emphasize:
- Analyze question complexity first
- Match response length to question type
- Don't over-explain simple things
- Be helpful but concise
