# <Feature id> — <what breaks>

## Symptom

What the reporter or the alert actually says, in their words. Include the alert name and the metric
or log line that fires it.

## Confirm it

The exact commands or queries that distinguish this from something that looks like it. Each step
states what output means "yes, this" and what output means "no, look elsewhere".

```text
<command>
```

## Blast radius

What is already broken while this is happening, and who notices. Whether data is at risk or only
availability. Whether it is getting worse on its own.

## Fix

Numbered steps. Each names its reversal, or says plainly that it has none. Where a step is
destructive, say what evidence to capture first.

1.
2.

## Do not

The plausible actions that make it worse — the retry that duplicates writes, the restart that loses
the in-flight batch, the flag flip that hides the symptom while the cause continues.

## Escalate

Who, with what attached: correlation ids, the run or delivery id, the tenant, the time window.

## After

The follow-up ticket to file, and the check that proves it is actually over rather than quiet.
