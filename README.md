# llmGitOps_v1

Niraj's repo


What we built

A robot checker that automatically tests your AI chatbot every time you update your code, and stops bad changes from getting merged.

The pieces

agent.py — this is your actual chatbot. It's a tiny script that takes a question ("What is 2+2?"), sends it to GPT, and returns whatever GPT says back. That's it — it's just a messenger to GPT.

prep_eval.py — the "are we ready?" check. Before spending money calling GPT, this checks two boring things: did you forget to set your API key, and is your test file (the list of questions/answers) formatted correctly. If either is broken, it stops immediately instead of wasting time.

version_eval.py — the actual test. This reads your list of test questions, asks your chatbot (agent.py) each one, and checks if the answer was right. At the end it writes a report card: how many it got right, how many wrong, how long it took.

regression_eval.py — the "did we make it worse?" check. This compares today's report card to yesterday's (the "baseline"). If a question that used to be answered correctly is now answered wrong, or the overall score dropped too much, it flags a problem and blocks the change.

agent-eval.yml — the automation that runs all of this. Every time you push code to GitHub, this file tells GitHub: run prep check → run the test → compare to before → save the results. No manual work needed.

Why 3 separate checks instead of just one?

Think of it like a car inspection:

Prep eval = does the car have gas and are the tires inflated? (basic setup)
Version eval = how does the car actually drive right now? (the real test)
Regression eval = does it drive worse than it did last week? (comparing to before)

Each one catches a different kind of problem, and doing them in order saves time — no point test-driving a car with no gas.

One thing to know

Your "yesterday's report card" (baseline.json) right now was created by an older, fake version of the agent (before we switched to real GPT calls). Once you push the real GPT version, that comparison won't make sense anymore — you'll want to delete that old baseline file so it creates a fresh, accurate one from the real GPT results.
