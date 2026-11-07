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
   "hamburger meat" should find "Beef, ground", whose keywords are just
   "Beef,ground" -- no "hamburger", no "meat". The shortlist can never
   contain it, so the model has to see everything.

   That prompt is expensive. Measured against Groq's free tier it runs
   about 6,600 tokens, and the budget is 8,000 a minute -- so one of these
   nearly exhausts the minute and starves the cheap queries behind it. Two
   back to back are guaranteed to fail. Worse, which one fails depends on
   what someone searched forty seconds earlier, so the same query succeeds
   or fails for reasons the user cannot see.

   So every prompt is now measured before it is sent. Too large, and we
   drop the descriptions and send names alone. Still too large, and we give
   up without calling the API at all -- better a clean miss than spending
   the whole minute's budget on a request that will be rejected.

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

# How many candidates to put in front of the model. Enough to contain the
# right answer, small enough to stay well inside a per-minute token budget.
SHORTLIST_SIZE = 40

# Reasoning models emit their thinking before the answer, so a tight cap
# truncates them mid-thought and we get nothing usable back.
MAX_OUTPUT_TOKENS = 512

# Groq's free tier allows 8,000 tokens a minute. Cap a single prompt well
# under that so one expensive query cannot starve the cheap ones behind it.
MAX_PROMPT_TOKENS = 4000

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


def _catalog_lines(items, descriptions=True):
    """The candidate list as the prompt shows it.

    Descriptions help the model tell near-identical names apart, but they
    are most of the prompt's size. Dropping them is the first thing we try
    when a prompt is too big.
    """
    if descriptions:
        return "\n".join(f"{i.id}|{i.name}|{i.name_subtitle}" for i in items)
    return "\n".join(f"{i.id}|{i.name}" for i in items)


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

    Tries the full prompt first. If that would blow the per-minute budget,
    drops the descriptions and tries again -- a name alone is usually
    enough to recognise a food. If even that is too large, gives up without
    sending, rather than spending the whole minute's budget on a request
    the API will reject anyway.
    """
    if not candidates:
        return None

    for descriptions in (True, False):
        prompt = PROMPT.format(
            query=query,
            catalog=_catalog_lines(candidates, descriptions=descriptions))
        if _estimate_tokens(prompt) <= MAX_PROMPT_TOKENS:
            return _resolve(_call_model(prompt), candidates)

    logger.info(
        "Catalog match skipped for %r: %d candidates exceed the token "
        "budget even without descriptions", query, len(candidates))
    return None


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