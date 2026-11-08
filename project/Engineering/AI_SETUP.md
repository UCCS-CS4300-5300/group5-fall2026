# Turning on AI catalog matching

Our search is literal, so it fails whenever your words and the USDA's words
differ. "bell pepper" finds nothing, because FoodKeeper calls it "Peppers".
"hamburger meat" finds nothing, because FoodKeeper calls it "Beef, ground".

When the normal search comes back empty, we now ask a model which catalog
food you probably meant. It picks from the 661 foods we already loaded, so
it can't invent one.

**You don't need a key to work on this project.** Without one the feature is
simply off and search behaves exactly as it did before. All the tests pass
either way — they never touch the network. You only need a key if you want
to see it working in the browser.

---

## Get a key (about two minutes, free, no card)

1. Go to **console.groq.com** and sign in with Google or GitHub
2. **API Keys** in the sidebar → **Create API Key**
3. Copy it straight away — it's only shown once. It starts with `gsk_`

Get your own rather than sharing one. They're free, and separate keys mean
separate rate limits, which matters when four of us are testing at once.

---

## Put it in place

Create a file called `.env` inside the `project/` folder — the same folder
as `manage.py`.

Easiest way, from a terminal in `project/`:

```
code .env
```

VS Code will offer to create it. Paste these three lines, with your own key
on the first, then save:

```
AI_API_KEY=gsk_your_key_goes_here
AI_BASE_URL=https://api.groq.com/openai/v1
AI_MODEL=openai/gpt-oss-20b
```

Two things that catch people out:

- The filename is exactly `.env` — no `.txt` on the end. If you use Notepad,
  pick "All Files" in the Save as type dropdown, or it'll silently save
  `.env.txt` and nothing will work.
- Each line is `NAME=value`. Don't paste `AI_MODEL=` twice on the same line.

`.env` is in `.gitignore`, so your key stays on your machine. Don't commit
it, don't paste it in Discord, don't put it in a screenshot. If one leaks,
delete it in the Groq console and make a new one — takes thirty seconds.

---

## Check it loaded

From `project/`, with the venv active:

```
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(bool(os.environ.get('AI_API_KEY')), os.environ.get('AI_MODEL'))"
```

You want `True openai/gpt-oss-20b`.

If it prints `False`, the file isn't where Python is looking — check it's in
`project/` and actually called `.env`.

---

## Try it

```
python manage.py shell -c "from core.ai import match_to_catalog as m; [print(q, '->', m(q)) for q in ['bell pepper','hamburger meat','soda']]" 2>$null
```

Expected:

```
bell pepper -> Peppers
hamburger meat -> Beef (ground)
soda -> Soda (carbonated cola drinks, mixers, diet sodas; bottles or cans)
```

Then in the browser: `python manage.py runserver`, search `bell pepper` in
the left-hand box. It should return Peppers rather than the no-match
message.

**Restart the server after editing `.env`.** Django only reads it at
startup, and the autoreloader watches `.py` files, not `.env` — so editing
the key while the server is running changes nothing until you restart.

---

## Things that look broken and aren't

**A search takes several seconds the first time, then is instant.** Working
as intended. Every answer is cached in the `CatalogMatch` table, and the
catalog never changes, so a match stays correct permanently. Only the first
person to search a given phrase pays for it.

**Some searches still find nothing.** Two reasons, both fine:

The free tier allows 8,000 tokens a minute. A hard search — one where no
catalog word overlaps your words at all — sends the whole catalog and uses
about 4,400 of those. Two of those back to back gets you rate-limited, and
the feature quietly gives up rather than erroring. Wait a minute.

Or the model genuinely couldn't work it out. `evoo` doesn't reach "Oils
(olive or vegetable)". Abbreviations and regional synonyms are beyond it;
alternate common names generally work.

**A failed search stays failed.** Misses are cached too, deliberately, so we
don't pay repeatedly for a hopeless query. If you want to retry something
after changing the model or waiting out a rate limit:

```
python manage.py shell -c "from core.models import CatalogMatch; print(CatalogMatch.objects.filter(item=None).delete())"
```

That clears only the misses and leaves the good matches alone.

---

## If you want to try a different model

```
python manage.py shell -c "import os; from openai import OpenAI; c=OpenAI(api_key=os.environ['AI_API_KEY'], base_url=os.environ['AI_BASE_URL']); [print(m.id) for m in c.models.list().data]"
```

Change `AI_MODEL` in `.env` to any of the general-purpose text ones and
restart. `openai/gpt-oss-120b` is bigger and slower than the 20b we default
to; worth trying if matches look poor. Skip the whisper, orpheus,
prompt-guard and safeguard models — those do other jobs.

Because everything goes through an OpenAI-compatible endpoint, switching
provider entirely is just `AI_BASE_URL` and `AI_API_KEY`. No code changes.

---

## On Render

Same three variables, set in the service's Environment settings in the
Render dashboard rather than in a file. If they're missing the deployed app
just runs with the feature off, which is a safe default rather than a
failure.
