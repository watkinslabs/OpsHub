# Filter vocabulary

One closed predicate vocabulary for the whole product. Views, roll-up rules, exports, workflow
conditions, reports, drill-through, dynamic views and conditional formatting all express "which
records" with the operators below and no others.

This document exists because the same question was answered five different ways: `ne` in one ticket
and `neq` in another, `before`/`after` alongside `lt`/`gt`, `gte` in one operator list and absent
from the next, and a flat conjunction in a third. Those are the same concept spelled differently, and
a product that spells it differently in five places cannot round-trip a saved filter between the
features that read it. F013 owns this file; a change here is an amendment to F013 and to every
consumer whose subset the change touches.

## Operators

```
eq ne lt lte gt gte between contains not_contains starts_with in not_in is_empty is_not_empty is_me is_error
```

That fenced block is the whole vocabulary and the only place `check-filters` reads it from, so a
name mentioned in the prose below can never become an operator by accident.

There is no `neq` — inequality is `ne` everywhere. There is no `before` or `after` — a date compares
with `lt` and `gt` like every other ordered type. There is no `assigned_to_current_user` leaf kind —
that is the operator `is_me` on a `person` column.

## Which column type accepts which operator

`columns.type` is F007's. A `formula` column takes the row of its `result_type`.

| Column type | Operators |
|---|---|
| `text` | `eq`, `ne`, `contains`, `not_contains`, `starts_with`, `in`, `not_in`, `is_empty`, `is_not_empty` |
| `number`, `currency`, `duration` | `eq`, `ne`, `lt`, `lte`, `gt`, `gte`, `between`, `is_empty`, `is_not_empty` |
| `date`, `datetime` | `eq`, `ne`, `lt`, `lte`, `gt`, `gte`, `between`, `is_empty`, `is_not_empty` |
| `boolean` | `eq`, `ne`, `is_empty`, `is_not_empty` |
| `select` | `eq`, `ne`, `in`, `not_in`, `is_empty`, `is_not_empty` |
| `person` | `eq`, `ne`, `in`, `not_in`, `is_me`, `is_empty`, `is_not_empty` |
| `link`, `file` | `is_empty`, `is_not_empty` |
| `formula` | the row for its `result_type`, plus `is_error` |

`starts_with`, `contains` and `not_contains` are text-only: no other type has a stable substring once
normalized. `is_error` is formula-only: it tests F035's evaluation failure state, which no other
column type can hold, and is the one operator that reads something other than the cell's value.

## The value each operator takes

Comparison runs against the cell's `normalized` value, never its `display` string, so a `currency`
predicate compares decimals and a `date` predicate compares instants. The value is never tagged in
the payload — its type comes from the column, the convention F007's `CellValue` already uses.

| Operator | Value |
|---|---|
| `eq`, `ne`, `lt`, `lte`, `gt`, `gte` | one scalar of the column's type: string, decimal string, boolean, `YYYY-MM-DD`, RFC 3339 timestamp, or uuid for `select` and `person` |
| `between` | `{ from, to }`, both scalars of the column's type, `from <= to`, both required |
| `in`, `not_in` | array of 1–100 distinct scalars of the column's type |
| `contains`, `not_contains`, `starts_with` | string, 1–256 characters, case-insensitive |
| `is_empty`, `is_not_empty`, `is_me`, `is_error` | absent; a present value is `400 invalid` |

A scalar whose JSON type does not match the column's type is `400 invalid` under the caller's own
`field_errors` key — the same code a mismatched operator produces.

## Relative dates

On a `date` or `datetime` column a scalar may be a relative token instead of a literal. A token is
resolved at query time in the actor's F049 timezone, never at save time, so a saved filter still
means "this week" next week.

`today` `tomorrow` `yesterday` `start_of_week` `end_of_week` `start_of_month` `end_of_month`
`start_of_quarter` `end_of_quarter` `start_of_year` `end_of_year`, and signed day offsets matching
`^[+-][0-9]{1,4}d$` (`+7d`, `-30d`).

Any other string in a date position is `400 invalid`. `is_me` resolves at query time for the same
reason: a filter saved by one person and read by another must mean "me, the reader".

## How a ticket declares its subset

A feature may accept a subset of these operators — never a member outside them, and never a synonym.
Each filtering ticket carries one line in section 4, which `cargo xtask check-filters` reads:

```
- Filter operators: `docs/filter-vocabulary.md`, subset `eq`, `ne`, `in`, `is_empty`
```

Write `subset all` when the feature accepts the whole vocabulary. The gate fails on an operator that
is not defined above, so a sixth spelling cannot enter the product unnoticed.

## Who accepts what

| Feature | Subset | Why it is narrower |
|---|---|---|
| F013 views | all | the AST every other consumer reuses |
| F009 roll-up rule filters | `eq`, `ne`, `lt`, `lte`, `gt`, `gte`, `contains`, `is_empty`, `is_not_empty` | one flat predicate per rule, no set membership and no `is_me`: a roll-up is evaluated by a background recompute with no calling actor |
| F010 export filters | all | an export filters the same rows a view does |
| F018 workflow conditions | `eq`, `ne`, `lt`, `lte`, `gt`, `gte`, `contains`, `starts_with`, `in`, `between` | a condition tests a value it already has; emptiness is the separate `exists` leaf and actor membership the separate `actor_in` leaf |
| F021 reports | all | a report filters across sources with the same vocabulary |
| F025 drill-through | all | inherited from the F021 definition it drills into |
| F050 dynamic views | `eq`, `ne`, `in`, `contains`, `gt`, `lt`, `is_empty`, `is_me` | the scoped external surface deliberately offers fewer controls |
| F056 pivot | `eq`, `ne`, `lt`, `lte`, `gt`, `gte`, `contains`, `not_contains`, `in`, `between`, `is_empty`, `is_not_empty` | a pivot is computed for everyone who opens it, so it takes no `is_me` |
| F060 conditional formatting | all | a formatting rule is a predicate over one row, and it is the only consumer that reaches `is_error` |
