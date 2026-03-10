\# Task 037 — Persistent Backlog State



\## Goal

Persist task execution state between runs.



\## State file

tasks/state.json





\## Task states



\- pending

\- running

\- completed

\- blocked

\- failed



Runner must load existing state on startup.



Simulation must not modify real state.



Tests verify persistence across runs.

