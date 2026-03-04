# JSE v1.0 AI Output Specification

*(Prompt-Compatible Version)*

---

## 1. Purpose

This specification defines how an AI system MUST generate and interpret JSON Structural Expression (JSE).

JSE is a structural protocol over JSON that allows symbolic S-expression style composition while remaining valid JSON.

All outputs claiming to be JSE MUST comply with this specification.

---

# 2. Fundamental Constraint

**All JSE data MUST be syntactically valid JSON.**

No comments.
No trailing commas.
No non-JSON constructs.

---

# 3. Symbol Definition

A string is a `Symbol` if and only if:

* It begins with `$`
* It does NOT begin with `$$`

Examples:

```
"$add"      → Symbol
"$if"       → Symbol
"$$add"     → String "$add"
```

---

# 4. Escape Rule

To represent a literal string that begins with `$`, the string MUST begin with `$$`.

Example:

```
"$$add" → literal string "$add"
```

AI systems MUST use `$$` when a string beginning with `$` is intended to be data rather than a Symbol.

---

# 5. Expression Forms

JSE supports exactly two expression forms.

---

## 5.1 Array Form (Positional Expression)

A JSON array is a JSE expression if:

* The first element is a Symbol.

Structure:

```json
["$operator", arg1, arg2, ...]
```

Example:

```json
["$add", 1, 2]
```

If the first element is NOT a Symbol, the array MUST be interpreted as normal JSON data.

---

## 5.2 Object Form (Named Expression)

A JSON object is a JSE expression if:

* It contains exactly ONE key that is a Symbol
* All other keys MUST NOT begin with `$`

Structure:

```json
{
  "$operator": <expression>,
  "meta1": ...,
  "meta2": ...
}
```

Rules:

* The Symbol key defines the operator
* All non-Symbol keys are metadata
* Metadata MUST NOT alter structural interpretation

If an object contains:

* Zero Symbol keys → it is normal JSON data
* More than one Symbol key → INVALID JSE

AI systems MUST NOT generate objects with multiple Symbol keys.

---

# 6. Quote

JSE defines a special operator:

```
"$quote"
```

Semantics:

* The argument to `$quote` MUST NOT be interpreted as JSE expression
* It MUST be preserved as raw JSON

Array form:

```json
["$quote", <any JSON value>]
```

Object form:

```json
{
  "$quote": <any JSON value>
}
```

AI systems MUST use `$quote` when:

* Returning data that might otherwise be misinterpreted as expression
* Returning large JSON objects that should not be parsed structurally

---

# 7. Structural Validity Rules

A JSE document is valid if:

1. It is valid JSON.
2. No object contains more than one Symbol key.
3. Escape rules are respected.
4. `$quote` is not nested incorrectly as multiple Symbol keys in the same object.

---

# 8. AI Output Requirements

When generating JSE, an AI system MUST:

* Produce syntactically valid JSON.
* Respect Symbol rules.
* Avoid accidental `$` prefix.
* Use `$quote` when returning raw data that begins with `$`.
* Never produce multiple Symbol keys in a single object.

An AI system SHOULD:

* Prefer Array Form for pure computation trees.
* Prefer Object Form when metadata is required.
* Keep nesting depth reasonable.
* Avoid generating undefined operators.

---

# 9. Deterministic Structural Interpretation

Given any JSON value V:

1. If V is an array and first element is a Symbol → Array Expression.
2. If V is an object with exactly one Symbol key → Object Expression.
3. Otherwise → JSON data.

This interpretation MUST be deterministic.

---

# 10. Execution Model

This specification does NOT define execution semantics.

Implementations MAY:

* Interpret operators
* Restrict allowed operators
* Ignore expressions
* Validate against JSON Schema

JSE defines structure only.

---

# 11. Operator Namespace

JSE does not define a required operator set.

Operators:

* Are implementation-defined
* SHOULD be whitelisted by consuming systems
* SHOULD be documented separately

---

# 12. Minimal Compliance Checklist

A compliant AI-generated JSE output:

* [ ] Is valid JSON
* [ ] Uses `$` only for Symbols
* [ ] Uses `$$` for literal `$`
* [ ] Contains at most one Symbol key per object
* [ ] Uses `$quote` correctly

---

# 13. Example

Valid JSE:

```json
{
  "$if": [
    ["$gt", 5, 3],
    ["$add", 1, 2],
    ["$quote", { "$raw": "data" }]
  ],
  "confidence": 0.98
}
```

Invalid JSE:

```json
{
  "$add": [1,2],
  "$mul": [3,4]
}
```

Reason: multiple Symbol keys.


