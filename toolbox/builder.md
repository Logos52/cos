# Autonomous Builder

Reads a brief or PRD dropped in builds/, plans and stages the project inside builds/<name>/, then stops for sign-off.

## Trigger

Wedge drops a brief or PRD file into ~/cos/builds/ and invokes this skill.

## Instructions

See cos-skill-builder scheduled task for the full prompt.

## Sign-off gate

The builder ALWAYS stops after staging. It never ships, deploys, or writes outside builds/<name>/ without explicit confirmation. This gate is non-negotiable.
