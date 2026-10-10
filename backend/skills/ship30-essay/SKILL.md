---
name: ship30-essay
description: Writes a punchy, atomic "Ship 30 for 30" style essay grounded in podcast wisdom.
---

# Ship 30 for 30 Essay Writing Skill

## Philosophy & Architecture

The Ship 30 for 30 framework turns substantive ideas into crisp, readable, high-retention atomic essays (~250–350 words). It replaces dense walls of prose with clean visual pacing, structured takeaways, and compelling rhythm.

When writing an essay based on Lenny's Podcast transcripts:
1. **Single Atomic Idea**: Focus on ONE specific mental model, principle, or tactic from the interviews (e.g., "The Counter-Intuitive Truth About Retention" or "Why Most Teams Price Too Late").
2. **Strict Grounding**: Every principle and example must cite what actual practitioners said in the podcast. Never invent statistics, frameworks, or quotes.
3. **Visual Pacing (The 1-3-1 Rhythm)**:
   - 1 short, arresting sentence hook.
   - 3 lines expanding context or setting up tension.
   - 1 single-sentence pivot.
   - Core body with subheaders, bullets, or numbered actionable steps.
   - Punchy, memorable conclusion.

---

## Anatomy of an Atomic Essay

### 1. The Headline
Use a proven curiosity or benefit structure:
- *How [Guest Name] Solved [Common Product Dilemma]*
- *The 3-Step Framework for [Outcome] (From [Guest])*
- *Why Most [Role] Fail at [Task] — And How to Fix It*

### 2. The Hook (First 2 Lines)
Start in media res. Challenge conventional wisdom:
> Most teams think growth is a top-of-funnel problem.
>
> They spend 80% of their marketing budget buying attention.
> Then watch 90% of new signups churn within 14 days.

### 3. The Evidence & Core Insight
Introduce the podcast wisdom with explicit attribution:
> On Lenny's Podcast, [Guest Name] ([Title/Company]) outlined why this fails:
>
> *"Quote or synthesized principle"* [[Guest Name] — [Episode Title], HH:MM:SS]

### 4. Actionable Breakdown (3 Points)
- **Point 1**: State the rule simply.
- **Point 2**: Provide the tactical implementation.
- **Point 3**: Warn against the primary trap.

### 5. The Closing Punchline (1-Line Takeaway)
Summarize into a shareable maxim:
> Fix the leaky bucket first. The water comes later.

---

## Output Rules
- Format strictly in clean Markdown with appropriate headers (`#`, `##`).
- Ensure all guest mentions carry citation chips in the standard format `[Guest — Episode Title, HH:MM:SS]`.
- When the user asks to "Turn this into an artifact", invoke `create_artifact` with `kind: markdown` and an editorial title.
