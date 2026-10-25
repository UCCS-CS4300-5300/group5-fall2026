Where AI fits in Shelf-Life

Decision for the AI Chef feature. Written for Sprint 3 planning.

Three uses were considered. The recommendation is to start with catalog matching, not recipes, and the reasoning is below.

What we looked at
1. Recipe suggestions from what's in the pantry

The one everybody pictures, and the one the menu already promises with "Ai assisted Chef". You have someone's pantry contents and their expiration dates, so you can suggest something that uses the food about to go off. That's a genuinely good feature and it's the reason this project is interesting.

The problem is that a language model inventing a recipe is a language model inventing cooking times and temperatures for chicken. We're already a food safety app — we ship USDA storage data precisely because we didn't want to make up shelf lives — so making up cooking instructions would be strange.

The way around it is to not let the model write recipes at all. A recipe API finds real recipes that match the pantry; the model's job is to pick among them and explain what to substitute. Nothing invented reaches the user.

That works, but it means integrating a recipe API as well, and that's a second vendor, a second key, a second thing that can be down during the demo. It roughly doubles the work.

2. Freeform item entry

The user types "2 gal milk, chicken, a bag of spinach" and the model turns it into catalog items with quantities. Nice to use, and it fits the catalog we already load.

It's a small call and the failure mode is mild — a wrong quantity, an item matched to the wrong entry. The user sees the result immediately and can fix it.

The honest problem is it isn't solving much. Adding an item takes one search and one click today. Saving a few seconds on a thing that already works isn't where the demo lands.

3. Matching messy names to the catalog

FoodKeeper's names are not what people type. We've hit this repeatedly:

"bell pepper" returns nothing — FoodKeeper has "Peppers" and "Hot peppers"
"spinach" returns an item called Lettuce, because it lives inside "Lettuce, leaf, spinach"
"chicken" puts deli lunch meat above the whole bird, because both are named exactly "Chicken" and the subtitle sorts first alphabetically

These aren't bugs in the search code. The ranking already does word-splitting and puts name matches above keyword matches. The problem is that 661 USDA entries use USDA's vocabulary and users don't.

A model is good at exactly this. Give it the user's words and a shortlist of catalog candidates, ask which one they meant. It never invents a food — it picks from the 661 we loaded, so a wrong answer is a bad search result, not a fabricated one.

What we recommend

Start with catalog matching. Three reasons.

It fixes something that's actually broken. The other two add features; this one repairs a gap we keep running into, and a demo where searching "bell pepper" works is better than one where it doesn't.

It can't produce anything false. The model chooses from a fixed list. The worst case is it picks the wrong one of 661 real foods, and the user searches again.

It fails safely. If the API is down or out of credit, search falls back to what it does today. The catalog is already offline-only by design — it's loaded by a data migration, not an API call — and the AI layer should degrade the same way. Nothing about the app stops working.

Recipes stay on the roadmap. They're the better story and the thing the team pitched, but they need a recipe API alongside the model, and that's a Sprint 4 conversation once we know this plumbing works.

Not recommended: diet or nutrition advice. Different product, real liability, and nobody wants to defend it in a demo.

The practical details
Cost

Catalog matching is a short call. Roughly 400 input tokens (the query plus a shortlist of candidate names) and about 10 output tokens (an id).

At Claude Haiku 5.5 rates — $0.10 per million input tokens, $0.50 per million output, checked 14 October 2026 — that's about $0.000045 per search, or somewhere around 20,000 searches per dollar.

For comparison, the recipe version would carry a pantry list plus several retrieved recipes, so maybe 2,000 input and 400 output tokens: around $0.0004 per suggestion, still roughly 2,500 for a dollar.

Neither is a real cost at our scale. Pricing moves, so whoever implements this should re-check the provider's own page and note the date.

Latency

Not measured yet, and we shouldn't guess. A short structured call to a small model is usually under a second, but that needs timing before we put it in the search path — a four-second wait is fine for a recipe suggestion and unacceptable for a search box.

Action for whoever picks this up: time ten real calls and record the median before wiring it into search. If it's slow, the fallback is to run it only when the normal search returns nothing, which is the case that's broken anyway.

Where the key lives

An environment variable. Never in the repo.

python
# settings.py
AI_API_KEY = os.environ.get("AI_API_KEY", "")

Locally that means a .env file with .env in .gitignore. Wherever we deploy, it's that host's environment settings.

A key committed to git stays in the history even after you delete it, the repo is public, and GitHub's secret scanning will flag it — to the provider and to anyone watching. Keys have been pulled from public repos and run up bills.

Two rules for the implementation:

AI_API_KEY is read from the environment, with "" as the default
If it's empty, the feature turns itself off and search works as it does today — no crash, no error page

The second rule means a teammate who hasn't set a key can still run the app, which is the same reason the catalog loads from CSVs instead of an API.

Open questions for Sprint 3 planning
Do we want matching on every search, or only when the normal search finds nothing? The second is cheaper and faster.
Do we cache results? "bell pepper" will be asked more than once, and the answer doesn't change.
Who owns the API account, and what's the spending cap on it?
