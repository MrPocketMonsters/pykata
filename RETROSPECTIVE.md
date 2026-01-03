# Sprint 1 Retrospective: The Rollercoaster of Foundation & Backend

**Date:** January 2, 2026
**Project:** PyKata CI/CD Showcase
**Sprint Duration:** Dec 20, 2025 – Jan 2, 2026

## 🎯 Executive Summary

Sprint 1 was a journey of high expectations, humbling challenges, and ultimate triumph. I set out to build a serverless-friendly Python application with a "quality-first" mindset. What started as a seemingly easy sprint quickly evolved into a deep dive into the intricacies of Terraform, CI/CD pipelines, and the absolute necessity of automated testing. I closed the sprint with a fully functional backend, a ~95% test coverage, and a local deployment that actually works.

## 📈 Sprint Metrics

- **Testing Coverage:** ~95% (A hard-won victory over the 85% threshold)
- **Test Suite:** 116 Unit, 18 Integration, 8 E2E tests (The "safety net" that saved my sanity)
- **Documentation:** 12 Markdown files (A "rewarding and horrible" labor of love)
- **Infrastructure:** 2 Core Terraform modules + 1 Dev Environment (Built on a binge of tutorials)
- **API:** 4 Functional endpoints (`/health`, `/katas`, `/katas/{id}`, `/katas/run`)

## 🗓️ Timeline & The "Breeze" That Wasn't

The sprint was originally due to end on Jan 1, but life had other plans. Between the holiday season and a new project I hadn't planned for, I found myself struggling to keep up, especially during that first week.

The sprint started with a deceptive burst of speed. I closed the first three tasks almost simultaneously by Dec 22. I honestly thought, "This is going to be a breeze!"

**Not the case. Not the case at all.**

- **Dec 20:** First commit. The excitement begins.
- **Dec 22:** Tasks 1.1, 1.2, 1.3 closed. Feeling like a pro.
- **Dec 25:** Task 1.4 (Terraform). Spent Christmas binging more tutorials than I'm comfortable sharing.
- **Dec 28:** Task 1.5 (Models & Services).
- **Dec 31:** Tasks 1.6, 1.7, 1.8. New Year's Eve spent wrestling with FastAPI and seed data.
- **Jan 1:** Reopened Task 1.4. Realized I needed to fix the architecture for Lambda support. Missed the original deadline, but the push was worth it.
- **Jan 2:** Tasks 1.9 (CI/CD) and 1.10 (Documentation). Sprint finish!

## 🟢 The Wins: Achievements & Revelations

### The Unit Testing Epiphany

I’ll be honest: I never actually put effort into unit testing before. I only did it when I was forced to. But this sprint changed everything. Especially when I started touching Terraform, which I did *a whole lot*. I just couldn't imagine running E2E tests manually every single time. Pytest was my mentor, catching errors in logic and exception handling that would have blown up the API later.

### The Power of the Backlog

Before writing a single line of code, I locked down the architecture and philosophy in a full backlog. This was a lifesaver. It kept me from going in never-ending circles and avoided implementation dead ends. Every time I checked off an issue, I knew exactly where I was and felt that rush of excitement for the next step. **Checklists are the best thing ever.**

### Mocking & Scripting Fun

Learning to mock responses with `Monkeypatch` and `MockMagic` was surprisingly fun. While `MockMagic` is great for complex integrations, a quick `Monkeypatch` was perfect for churning out unit tests. Implementing the helper scripts also felt like "back to basics" programminl: very rewarding to see a set of steps execute perfectly.

## 🟡 The Struggles: Troubles & "Cringe" Moments

### The Tooling Tug-of-War

There was a moment where I couldn't even commit to my own repo! I had conflicting Black and MyPy configurations. One would reformat the line width, then the other would do it again, and pre-commit would just block me. It was a puzzling nightmare to solve, but it made me truly understand the difference between `pyproject.toml` and `.pre-commit-config.yaml`.

### The Coverage Confusion

I created a `.coveragerc` file and suddenly my coverage percentages were blowing up, but without any missing lines or decimals. I had completely forgotten that I’d already configured coverage in `pyproject.toml` the week before. There were just so many new files in those first three days!

### The PR History Cringe

Setting up CI/CD was simpler to program than I thought, but testing it was another story. I cringe when I look at the PR request and see that count of "push commits" and spawning branches just to test the remote runner. However, attempting to clean that up actually gave me a much deeper understanding of Git pointers, branches, and the `|REBASE` state.

### The Windows vs. Lambda Trap

I spent a long session reading logs and failing GET queries to my Lambda instance, only to realize I couldn't just install dependencies on Windows and expect them to work on a Linux Lambda. Moving to WSL fixed it, but I took the hit and made sure to update the documentation so no one else has to suffer through that.

## 🛠️ Technical Decisions & Debt

### The "Quick Ugly" Lambda

I couldn't help myself. Task 1.9 was supposed to be just the deployment, but I had to see if it worked. So I built a "quick and ugly" Lambda function in the main Terraform module. I’ll have to pay that tech debt in Sprint 2 by modularizing it properly.

### The Execution Service Sandbox

I tried implementing a sandbox with `Restricted Python`, but it was a nightmare, even just getting the logging to work was impossible. Since virtualizing was too complex and risked delays, I settled for a simple `exec()` call in a subprocess. It’s dangerous, I know. But for the scope of this project (admin-provided code, isolated network), it works. I want to move this to a separate, network-isolated Lambda in the future.

### Documentation: The Necessary Evil

I did **A LOT** of documentation. It’s a weird feeling: rewarding and horrible at the same time. I find myself checking my own docs constantly, so I know it’s valuable. I hope someone else finds those long hours of reading and rewriting useful.

## 🚀 Looking Ahead: Sprint 2 Success

The hard part is done. For the next sprint, I’m tackling the React client, modularizing the Lambda, and adding API Gateway. The "creepy" part will be the actual AWS deployment, but I’m ready. I’ll try to tone down the documentation a bit, think of testing *before* implementing, and dive deep into the AWS ecosystem.

---

> *“You can't foresee everything, but you can certainly binge enough tutorials to try.”*
