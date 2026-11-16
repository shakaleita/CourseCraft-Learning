# CourseCraft — Engineering Case Study & Quality Roadmap

**Portfolio:** [Digital Solution9](https://github.com/shakaleita/teamforge-saas/blob/main/PORTFOLIO.md) · **Repository:** [Source](https://github.com/shakaleita/CourseCraft-Learning)  
**Stack:** React, FastAPI, SQLite · **Status:** Local portfolio MVP; not certified production software.

## Implemented domain workflow
Course enrolments, completion reporting and reproducible demo completion identifiers.

Descriptions reflect the public project's existing README. They are not a statement that a new deployment or independent penetration test was completed.

## Domain invariants
Enrollment must reference existing students/courses; completion must not exceed valid progress; repeated completion must not fabricate new awards.

## Verification backlog
- Enrollments rejected for invalid course/student IDs
- Repeated completion calls remain idempotent
- Role-aware enrolment and progress browser tests

## High-value engineering upgrades
1. Add learner/instructor roles with server-side checks
2. Add course versions, completion snapshots and realistic learning progress events
3. Run multi-user test scenarios and a controlled staging demo

## Production release gate

A production claim requires repeatable API and browser tests, threat modelling, verified authorization boundaries, database migration and restoration rehearsals, monitored staging deployment, accessibility verification and published performance evidence. Do not introduce real client, patient or other sensitive information into demo data.

**Engineering honesty:** This case study identifies current work and concrete improvements; it does not claim those outstanding checks passed.
