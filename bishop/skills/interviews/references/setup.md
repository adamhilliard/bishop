# Interviews setup

**The front door (`skills/start/SKILL.md`) runs this,** after job search when they picked both. It builds the core deck. About 5 minutes, plus the time they choose to spend writing answers.

**Every rule in "How to run this" in `skills/job-search/references/setup-interview.md` applies:** one question at a time, pickers for small sets, `Say:` lines close to verbatim, plain words. Read the profile job search wrote and never re-ask what it holds.

## I0. About you (only when they skipped job search)

**Ask job search's shared basics in its exact words,** from sections A and B of `setup-interview.md`: the background (resume, LinkedIn PDF or free text), the one review line, the Team and Level pickers when needed, the Target level picker, and the titles confirm. Then run its Permissions picker. Save the answers in the profile's shared sections, the way job search's setup does.

- **The titles line changes for interviews.** **Say:** "Here are the roles I'll prep you for: {{list}}. Any changes?"
- **The resume copy** is section A's Keep a copy picker, same words and options.

## I1. What this is

**Say:**

> Now your interview practice. I'll build you a core deck of common interview questions, plus a few about your background. You write each answer as if you were in an interview, and practice it from there. When an interview comes up, I'll build that company's deck combining your core deck with potential questions based on the job description (as long as you share it).
>
> I encourage you to write the answers to this deck, yourself. This practice will pay off when you interview.

## I2. What I read (silent)

- **From the profile:** level, current role, career history, target roles.
- **The resume:** the file job search saved, or one in `Interview_Prep/`.
- **No resume:** resume questions come from the career history. **Never ask for a resume again;** they already said they don't have one.
- **The level they're interviewing for:** the higher of their current rung and their target roles, as `SKILL.md` says.

## I3. Confirm the level

**Free text. Say:**

> I'm building this for {{level}}-level interviews in {{field}}. Does that sound right?

**If they say no, Say:**

> Got it. Which level are the interviews for?

**Then job search's Level picker,** header `Level`:

- **Manages people:** First-line manager · Senior manager · Director · Executive.
- **Individual contributor:** Entry level professional · Mid level professional · Senior professional · Functional or technical lead.

## I4. How much practice

**Picker,** single-select, header `Interviews`. **Say:**

> How many interviews do you expect with each company? I'll size your practice to match.

| Option | Description |
|---|---|
| **1 to 2** | About 15 questions, the ones nearly every interview asks |
| **3 to 4** (Recommended) | About 30 to 40 questions |
| **5 or more** | About 50 to 70 questions |

- **Listed in number order,** the one picker where the recommended option isn't first.
- **Save it as `"rigor"`** in the core deck's settings: 1 to 2 is `light`, 3 to 4 is `medium`, 5 or more is `heavy`.

## I5. Record your answers?

**Picker,** single-select, header `Recording`. **Say:**

> Would you like the ability to record your answers, so you can play them back later?

| Option | Description |
|---|---|
| **Yes** (Recommended) | A record button when you practice |
| **No** | No record button. You still practice out loud with the answer hidden |

**On Yes, picker,** single-select, header `Browser`. **Say:**

> Which browser will you practice in?

Options: *Chrome* · *Edge* · *Safari* · *Firefox*. Anything typed in Other is handled like Firefox.

**Chrome, Edge or Safari: picker,** single-select, header `Transcript`, no recommended option. **Say** that browser's line, then the question:

> - **Chrome:** Chrome makes transcripts with Google's speech service, so your recordings go to Google.
> - **Edge:** Edge makes transcripts with Microsoft's speech service, so your recordings go to Microsoft.
> - **Safari:** Safari makes transcripts with Apple's speech recognition, which may send your recordings to Apple.
>
> Want a transcript each time you record?

| Option | Description |
|---|---|
| **Yes, add transcripts** | Read back what you said after each recording |
| **No, audio only** | Your recordings stay on your computer |

**Firefox or anything else: no question. Say:**

> Firefox can't make transcripts, so you'll get audio only, and your recordings stay on your computer.

- **Save it as `"record"`** in the core deck's settings: `transcript`, `audio` or `off`. Every company deck copies it.
- **Speaking an answer in Study uses the same speech service as transcripts,** so the deck offers it only with `transcript`.
- **They can change it any time** ("turn off recording"); rebuild every deck with the new setting.

## I6. Build the core deck

**Build it as `SKILL.md`'s Job 1 says,** with the practice level and recording choice in the deck's settings, then `--check`.

**Print while it builds:**

```
> reading your background .... ok
> picking your questions ..... ok
> building your core deck .... ok
```

**If the build fails and you can't fix it, Say:**

> Something went wrong building your deck. Say "build my core deck" and I'll try again.

## I7. Open it and show them around

**Open `core.html` in their browser. Say:**

> Here's your core deck. It's saved at {{full path to core.html}} and opens in any browser, with no account. Bookmark it so you can come back. If it didn't open, double-click core.html in {{folder}}.
>
> At the top you'll see a toggle.
> - "Study" is where you draft your answers. Click a question and type your answer the way you'd say it. {{If transcripts:}} Or click "Speak" and say it, and it types as you talk. "Add STAR" splits a story into Situation, Task, Action and Result. STAR is a very common interviewing technique. Learn more about it here: https://en.wikipedia.org/wiki/Situation,_task,_action,_result
> - Lock In marks an answer done. The "Readiness" page shows what's left to write and to lock in.
> - "Test" hides your prior answers. Record yourself out loud, or type it from memory, then reveal your prior answers to check how you did. {{If recording:}} The red dot records you{{, with a transcript}}. The first time, your browser asks to use your microphone.

- **No recording:** the Test line starts "Say it out loud" in place of "Record yourself out loud," and the red-dot and microphone sentences are left out.
- **Audio only:** the red-dot sentence ends at "records you."

## I8. Done

**If they skipped job search,** ask job search's Name question first (section D of `setup-interview.md`, same words and options). It's always the last question of the first module.

**If they picked outreach, picker,** single-select, header `Next`. **Say:**

> Interview practice has been set up. Do you want to set up the outreach module now? It takes about 10 minutes.

Options: *Yes, set it up now* (Recommended) · *Later*, as the front door's step 8.

**Otherwise,** hand back to the front door for its closing note.
