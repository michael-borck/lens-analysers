---
title: "What we can notice about student work"
subtitle: "Signal-based assessment for conversation, not delegation"
---

# What we can notice about student work

*A plain-language guide to signal-based assessment*

## The idea in a sentence

When a student submits work — an essay, a video, some code, a spreadsheet —
there's a lot we *could* notice about it, beyond just reading or watching it.
A "signal" is one such observation: a single, concrete thing we can measure
automatically. This is a catalogue of the signals we can pick up today, sorted
by the kind of work a student hands in.

## What we're actually looking for

This sits inside a simple idea: **conversation, not delegation.** Using AI is
fine — encouraged, even. The question isn't *whether* a student used AI, but
whether AI **amplified their thinking** or **replaced it**. Did they treat it as
a thinking partner and stay in charge of the ideas, or hand the task over?

So these signals are mostly about **evidence of a student's own thinking and
engagement** — not about catching AI use. (We *can* take a weak guess at whether
some text reads like AI wrote it, but it's easily fooled, it isn't proof, and —
since using AI is allowed — it isn't really the point.) None of them is a verdict
on its own; they're prompts that help a marker look in the right place. Think of
them as a smart highlighter, not an examiner.

---

## Written work — essays, reports, reflections

**An essay or report.** We can notice:

- How easy the writing is to read, and roughly what reading level it's pitched at.
- The writing style — how formal or academic it sounds, and habits like overusing the passive voice or vague "hedging" language.
- Whether passages have been reused from elsewhere in the same piece.
- Whether the references are real, correctly cited, and actually appear in the text (and whether any links are dead).
- The overall emotional tone, and the people, places and organisations mentioned.
- Sentences that seem out of place — as if pasted in from somewhere else.
- A *weak* hint about whether the writing reads like AI produced it — worth a closer look at most, never proof, and (since using AI is fine) not the main event.

**A reflective journal.** We can notice how *deep* the reflection goes — whether
the student is just describing what happened, or genuinely making sense of it:
signs of self-awareness, critical thinking, use of evidence, honest emotion, and
plans for what they'll do differently next time. It sorts the reflection onto a
simple scale, from "just describing" up to "genuinely transformative."

**A transcript of a student chatting with an AI.** This is the clearest window
into "conversation, not delegation": we can notice *how* they used it — did they
question, push back, and build on the answers (AI amplifying their thinking), or
simply hand the task over (delegation)? It produces a "critical thinking" picture
of the exchange.

---

## Things they record — audio and video

**A spoken recording (e.g. an oral presentation or podcast).** We can notice the
pace of speaking, how many "um/uh" filler words crept in, how much was pauses or
silence, and an overall sense of how clearly it was delivered. For group work, it
can even tell who spoke and for how long. (It writes out a full transcript too —
but on its own the audio tool looks at *how* something was said, not *what* was
said.)

**A video — for example a recorded presentation or viva.** Everything from the
audio above, plus the structure of the video (where the scenes change), the
picture quality, and any text on screen — handy for slides and captions.
**And, if you give it a marking rubric, it can go further and mark the content:**
an AI reads the spoken words *and* what's on screen together and judges things
like whether the talk stayed on-topic and relevant, then writes feedback (for the
student or the marker). Because it sees the words and the visuals side by side, it
can also point out when the slides don't match what's being said — which is
exactly the kind of thing that matters for a recorded viva.

**An image or photo.** We can notice the picture quality, the hidden camera/phone
details (and when and where it was taken), whether it's a copy of another image,
any text in the picture — and, if the file carries one, a built-in "made with AI"
label (surfaced for information, not as a red flag in itself).

**A diagram or flowchart.** We can notice whether it's well-formed: stray boxes
that connect to nothing, accidental loops, and boxes left unlabelled.

---

## Technical work — code, spreadsheets, websites, data

**Code.** We can notice whether it actually runs, how tidy and well-organised it
is, whether it's documented, common beginner mistakes, and a rough sense of the
skill level on display. For notebooks, we can even tell whether the student
actually ran their code.

**A code project's history (its "version control").** A lovely one for the
"did it happen over time?" question: we can see whether the work was built up
steadily, or dumped in one big last-minute upload.

**A spreadsheet.** We can notice whether they used real formulas or just typed the
answers in by hand, how sophisticated the formulas are, and whether there are
errors or broken references hiding in the cells.

**A website.** We can notice whether it's accessible to people with disabilities,
soundly built, free of broken links, and a few standard quality checks.

**A dataset (a table of data).** We get a plain summary — how big it is, what's in
each column, where values are missing, and the typical ranges.

**A document's hidden history.** Most Office and PDF files quietly record their own
backstory: what software made them, who the author is, how long they were actually
edited, and how many times they were saved. This can flag, for instance, a
"finished" essay that was apparently edited for only two minutes.

**An editing trail (tracked changes in Word).** We can see how the document evolved —
including large blocks pasted in at once, which can be worth a second look.

---

## The three questions these signals help answer

Most of the signals above speak to one of three questions. The first is the
heart of "conversation, not delegation"; a well-rounded assessment usually draws
on more than one:

1. **Did the student's own thinking happen — and did AI amplify it?** — the
   back-and-forth with an AI (did they question, push back, and build on it, or
   delegate?), the depth of their reflection, and the trail of how the work
   evolved. This is the signal that matters most, and the hardest to fake.
2. **Was the work built up over time?** — the editing trail, the project
   history, how long a document was actually worked on. Steady effort tells a
   very different story from a fully-formed, last-minute drop.
3. **How good is it?** — the quality and depth measures: writing depth,
   reflection depth, presentation clarity, code skill level.

(There are also weaker "does this look AI-written?" style hints — AI-ish
phrasing, big paste-ins, broken references. We treat those as gentle nudges to
look closer, never as proof, and never as the point. Using AI *well* is the
goal, not avoiding it.)

## Putting signals together

The real power isn't any single signal — it's **combining a few**. For example,
to gauge whether an essay is genuinely the student's own work, we might look at
the essay itself, its hidden history, its editing trail, *and* a short reflection
alongside it — and see whether the story they tell is consistent. We have a few
of these ready-made combinations for common assessment types.

## From signals to a marked submission

On their own, the signals above are just *observations* — they don't yet know
anything about *your* assignment. The next piece brings the assignment into the
picture: a small app (working name **assessment-lens**) that a lecturer points at

- the **assignment brief** — what you asked students to do,
- the **marking rubric** — how you'll judge it (this can live inside the brief), and
- a **folder of submissions** — say, one folder per student.

It then:

1. reads the brief and works out what each student was *meant* to hand in;
2. sees what they *actually* submitted;
3. runs each piece through the relevant signal tools above; and
4. checks how the evidence lines up against your brief and rubric — showing,
   criterion by criterion, where the work meets it and where it's thin.

You stay the marker. The app gathers and organises the evidence — and, true to
*conversation, not delegation*, it tries to show **where the student's own
thinking maps to each rubric point** — so you can mark faster and more
consistently, with the evidence laid out in front of you. The signal tools stay
general-purpose; the app is where they get pointed at a specific assignment.

## It grows

This is a living list — these are simply the signals we can pick up **today**.
The toolkit is built so we can add new signals, or whole new kinds of submission,
whenever a useful one comes up. If there's something you wish we could notice
about student work, that's exactly the kind of thing we can add.

---

*This sits within the **Conversation, not Delegation** approach to assessment in
the age of AI — the goal isn't to detect or avoid AI, but to see whether it
amplified a student's thinking. More at conversationnotdelegation.com and
bigpicture.borck.dev.*
