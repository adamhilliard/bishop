# The answers file (Master_Answers.json)

Everything a candidate has written in their decks, in one JSON file. The deck's **Export Answers** button writes it; **Import Answers** reads it into another browser; `build_deck.py --master` embeds it so a company deck shows the candidate's master answers. The code is `engine/answers.js`.

```json
{
  "format": "bishop.interviews.answers",
  "version": 1,
  "exported": "2030-03-01T18:20:00.000Z",
  "decks": {
    "core": {
      "answers": {
        "QA1": {"sections": [{"name": "Answer", "text": "I run field service..."}], "locked": true}
      },
      "edits": []
    },
    "acme-robotics": {"answers": {}, "edits": [{"id": "QAx1k2", "field": "__added", "before": "", "after": "{...}"}]}
  }
}
```

| Field | Meaning |
|---|---|
| `format` | Always `"bishop.interviews.answers"` |
| `version` | `1`. A file of another version is refused, never guessed at |
| `exported` | When it was written. A deck carrying an embedded copy uses it only if it's newer than what that browser already holds |
| `decks` | One entry per deck, keyed by its slug |
| `decks.<slug>.answers.<question id>` | `sections` (a list of `{name, text}`, the named parts in order), `text` (an older single-box answer), `locked` (Lock In), and `extra` (anything else saved against the question, such as `own` for the notes from the call) |
| `decks.<slug>.edits` | Changes made in the deck itself: a question added (`__added`), deleted (`__deleted`), or its text edited (any other field), each with the text before and after |

> **The browser is the working copy; the file is how it travels.** Answers save as the candidate types. Exporting, then rebuilding the company decks with `--master`, is how a better master answer reaches every deck.
