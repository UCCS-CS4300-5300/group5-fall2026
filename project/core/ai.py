"""Match a user's words to the USDA catalog using a language model.

Our search is literal. It matches what the user typed against the names and
keywords FoodKeeper ships, which works right up until the user's words and
the USDA's words differ -- and they differ constantly:

    "bell pepper"   finds nothing; FoodKeeper has "Peppers" and "Hot peppers"
    "spinach"       returns an item called Lettuce, because spinach lives
                    inside "Lettuce, leaf, spinach"
    "hamburger meat" finds nothing; FoodKeeper has "Beef, ground"

This module is the fallback for those cases. The model picks from foods we
already loaded -- it never invents one -- so the worst case is a real food
that happens to be wrong, not a fabricated one.

Asking happens in two stages, so the common case stays cheap:

1. A shortlist first. Ordinary search requires EVERY word to match, which
   is why "bell pepper" fails. Here we match ANY word, which finds Peppers
   via "pepper", and send the model those few candidates -- about 200
   tokens. That answers most queries.

2. The whole catalog, only if the model says none of the shortlist fits.
   Word overlap cannot surface a food whose words differ entirely:
   "hamburger meat" should find id 41, "Beef | ground", whose keywords are
   just "Beef,ground" -- no "hamburger", no "meat". The shortlist can never
   contain it, so the model has to see everything.

   That prompt is expensive: Groq measures it at about 6,600 tokens against
   a free-tier budget of 8,000 a minute. One of them nearly exhausts the
   minute, so a cold hard query is roughly a once-a-minute operation. The
   cache is what makes that acceptable -- only the first person to search a
   phrase pays, and the catalog never changes.

   Sending less does not work. Ten foods are named simply "Beef", separated
   only by their subtitles -- ground, steaks, short ribs, chuck roast. Drop
   the subtitles to save tokens and the model answers confidently with the
   wrong Beef, which is worse than a rate limit because nobody notices.
   Truncating them saves nothing either: they are already a word or two.

   So prompts are measured and sent whole, or not sent at all. A prompt
   over budget is refused rather than spending the minute on a request the
   API will reject -- and that refusal raises BudgetExceeded rather than
   returning None, because "we declined to ask" must not be cached as "no
   such food". Rate limits are already excluded from the cache for the same
   reason: a shortage of tokens is not a fact about groceries.

   The expense is structural, not a tuning problem: 661 rows is simply a
   lot to put in a prompt. The cheaper design is to invert it -- ask the
   model what the shopper meant in plain words ("hamburger meat" -> "ground
   beef", ~50 tokens) and let the database do the matching. That is the
   next change, not this one.

3. Every answer is cached in CatalogMatch, misses included. The catalog is
   frozen (loaded by a data migration), so a match stays correct forever and
   the second person to search "bell pepper" costs nothing.

The feature switches itself off when AI_API_KEY is absent: search falls back
to exactly what it did before, with no error and no crash. That matters for
teammates without a key, for CI, and for a demo where the API is down.
"""

import logging
import os
import re

from django.db.models import Q

from .models import CatalogMatch, GlobalCatalogItem

logger = logging.getLogger(__name__)


class BudgetExceeded(Exception):
    """The prompt is too large to send.

    Its own exception so that match_to_catalog can tell it apart from the
    model answering NONE. A refusal to spend tokens is a resource limit,
    not a verdict about the food, and caching it would make a temporary
    constraint permanent.
    """

# How many candidates to put in front of the model. Enough to contain the
# right answer, small enough to stay well inside a per-minute token budget.
SHORTLIST_SIZE = 40

# Reasoning models emit their thinking before the answer, so a tight cap
# truncates them mid-thought and we get nothing usable back.
MAX_OUTPUT_TOKENS = 512

# Groq's free tier allows 8,000 tokens a minute. The whole-catalog prompt
# estimates at ~4,550 here and Groq counts it at ~6,600 -- this estimator
# reads low on short pipe-delimited lines -- so 5,000 admits that prompt and
# refuses anything materially bigger.
MAX_PROMPT_TOKENS = 5000

PROMPT = """You match a shopper's words to a food in a fixed list.

The shopper typed: "{query}"

Candidate foods, one per line, as `id|name|description`:

{catalog}

Which one did they mean? Reply with that food's id as a number.
If none of them is a reasonable match, reply with: NONE

Prefer the plain, raw form of a food over a prepared or canned version
unless the shopper's words say otherwise. End your reply with the id
alone."""


def _shortlist(query):
    """Candidate foods for the model to choose between.

    Ordinary search ANDs the words together, which is why "bell pepper"
    returns nothing -- no food contains both words. Here we OR them, so
    "pepper" alone surfaces Peppers and Hot peppers. Loose on purpose: the
    model does the actual choosing, this just narrows the field.
    """
    words = [w for w in query.split() if len(w) > 2]
    if not words:
        return GlobalCatalogItem.objects.none()

    matches = Q()
    for word in words:
        matches |= (Q(name__icontains=word)
                    | Q(name_subtitle__icontains=word)
                    | Q(keywords__icontains=word))

    return GlobalCatalogItem.objects.filter(matches)[:SHORTLIST_SIZE]


def _catalog_lines(items):
    """The candidate list as the prompt shows it.

    The subtitle is not decoration. Ten foods are named simply "Beef" and
    the subtitle is the only thing separating ground from brisket, so a
    name-only list makes the model pick confidently and wrongly.
    """
    return "\n".join(f"{i.id}|{i.name}|{i.name_subtitle}" for i in items)


def _estimate_tokens(text):
    """Rough token count -- English runs about four characters per token.

    This only needs to separate "comfortably inside the budget" from "the
    API will reject this", so an approximation beats taking on a tokenizer
    dependency for one decision.
    """
    return len(text) // 4


def _call_model(prompt):
    from openai import OpenAI
    client = OpenAI(
        api_key=os.environ["AI_API_KEY"],
        base_url=os.environ.get("AI_BASE_URL", "https://api.groq.com/openai/v1"),
        # The SDK retries rate limits by default, sleeping 45s between attempts,
        # so a 429 became a 90-second page hang. Fail fast instead -- a missed
        # match degrades to the normal "no results" message, which is fine.
        max_retries=0,
        timeout=10.0,
    )
    response = client.chat.completions.create(
        model=os.environ.get("AI_MODEL", ""),
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=MAX_OUTPUT_TOKENS,
    )
    return response.choices[0].message.content


def match_to_catalog(query):
    """Which catalog food did the user mean? None when we can't tell.

    Safe to call on any query. Never raises: a missing key, a dead API, a
    rate limit, a nonsense answer and an unknown id all come back as None,
    and the caller falls through to ordinary search.
    """
    if not query or not query.strip():
        return None

    normalized = CatalogMatch.normalize(query)

    cached = CatalogMatch.objects.filter(query=normalized).first()
    if cached:
        # May be None -- that's a cached miss, and returning it is the point.
        # Without it we would pay for "asdfgh" every time someone typed it.
        return cached.item

    if not os.environ.get("AI_API_KEY"):
        # Feature off. Don't cache this: the key may exist next time, and a
        # cached miss would outlive the reason for it.
        return None

    try:
        item = _ask(query, list(_shortlist(query)))

        if item is None:
            # The shortlist is built from word overlap, so it cannot contain
            # a food whose words differ entirely from the query. Show the
            # model everything before giving up.
            item = _ask(query, list(GlobalCatalogItem.objects.all()))
    except BudgetExceeded as exc:
        # We declined to ask. Not an answer, so it is not cached -- raise
        # the budget or shrink the catalog and the same query can succeed.
        logger.info("Catalog match skipped for %r: %s", query, exc)
        return None
    except Exception as exc:
        # A dead API or a rate limit must never take search down with it.
        # Not cached either -- this is a temporary failure, not an answer.
        logger.warning("Catalog match failed for %r: %s", query, exc)
        return None

    CatalogMatch.objects.update_or_create(
        query=normalized,
        defaults={"item": item, "source": CatalogMatch.AI},
    )
    return item


def _ask(query, candidates):
    """One round: show the model these candidates, return its pick or None.

    Measures the prompt first and refuses to send an oversized one. A
    request the API will reject still costs the wait and the round trip,
    and a clean miss is a better outcome than a 429.
    """
    if not candidates:
        return None

    prompt = PROMPT.format(query=query, catalog=_catalog_lines(candidates))

    if _estimate_tokens(prompt) > MAX_PROMPT_TOKENS:
        raise BudgetExceeded(
            f"{len(candidates)} candidates estimate at "
            f"{_estimate_tokens(prompt)} tokens, over the "
            f"{MAX_PROMPT_TOKENS} budget")

    return _resolve(_call_model(prompt), candidates)


def _resolve(raw, candidates):
    """Turn the model's reply into one of the candidates, or None.

    Takes the last number in the reply, because a reasoning model talks
    through its options before answering and earlier numbers are ids it
    considered and rejected.

    The id has to be one we offered. Anything else -- prose with no number,
    an id from outside the shortlist, an empty reply -- is treated as no
    match.
    """
    if not raw:
        return None

    numbers = re.findall(r"\d+", raw)
    if not numbers:
        if raw.strip().upper() != "NONE":
            logger.warning("Catalog match returned no id: %r", raw[:200])
        return None

    chosen = int(numbers[-1])

    allowed = {item.id: item for item in candidates}
    if chosen not in allowed:
        logger.warning("Catalog match returned id %s, which was not offered",
                       chosen)
        return None

    return allowed[chosen]