"""Tests for AI catalog matching.

Nothing here touches the network. `_call_model` is the single place the API
is reached, so every test replaces it -- which is most of the reason it is a
separate function.
"""

import pytest
from unittest.mock import patch

from core import ai
from core.models import CatalogMatch, GlobalCatalogItem
from core.views import search_catalog


@pytest.fixture
def peppers(db):
    """FoodKeeper's entry for peppers. The catalog comes from the migration."""
    return GlobalCatalogItem.objects.filter(name="Peppers").first()


# --- the shortlist ---------------------------------------------------------

@pytest.mark.django_db
def test_shortlist_finds_what_literal_search_misses(peppers):
    """Ordinary search needs every word; the shortlist needs only one.

    This is why "bell pepper" can be answered at all: no food contains both
    words, but "pepper" alone finds Peppers.
    """
    assert not search_catalog("bell pepper").exists()
    assert peppers in list(ai._shortlist("bell pepper"))


@pytest.mark.django_db
def test_shortlist_stays_small():
    """A long shortlist would blow the per-minute token budget."""
    assert len(list(ai._shortlist("beef chicken pork cheese milk"))) <= ai.SHORTLIST_SIZE


@pytest.mark.django_db
def test_shortlist_ignores_very_short_words():
    # "a" or "of" would match most of the catalog and tell us nothing
    assert not ai._shortlist("a of").exists()


# --- the normal case -------------------------------------------------------

@pytest.mark.django_db
def test_match_returns_the_food_the_model_picked(peppers):
    with patch.dict("os.environ", {"AI_API_KEY": "test-key"}):
        with patch.object(ai, "_call_model", return_value=str(peppers.id)):
            assert ai.match_to_catalog("bell pepper") == peppers


@pytest.mark.django_db
def test_search_surfaces_the_match_when_literal_search_finds_nothing(peppers):
    # The whole point: a search that used to return nothing returns a food
    assert not search_catalog("bell pepper").exists()

    with patch.dict("os.environ", {"AI_API_KEY": "test-key"}):
        with patch.object(ai, "_call_model", return_value=str(peppers.id)):
            results = search_catalog("bell pepper", use_ai=True)

    assert list(results) == [peppers]


@pytest.mark.django_db
def test_matching_is_off_unless_the_caller_asks(peppers):
    # The search box auto-submits as you type, so an always-on fallback
    # would spend an API call on every prefix -- "bel", "bell p" -- and
    # cache each as a permanent miss. The user asks for it explicitly.
    with patch.dict("os.environ", {"AI_API_KEY": "test-key"}):
        with patch.object(ai, "_call_model") as called:
            assert not search_catalog("bell pepper").exists()

    called.assert_not_called()


@pytest.mark.django_db
def test_reasoning_before_the_answer_is_handled(peppers):
    """Reasoning models talk through the options before answering.

    Earlier numbers are candidates they considered and rejected, so the
    answer is the last one.
    """
    reply = (f"Let me think. Could be 42 or {peppers.id}. "
             f"Hot peppers is a different food. The answer is {peppers.id}")

    with patch.dict("os.environ", {"AI_API_KEY": "test-key"}):
        with patch.object(ai, "_call_model", return_value=reply):
            assert ai.match_to_catalog("bell pepper") == peppers


# --- the cache -------------------------------------------------------------

@pytest.mark.django_db
def test_second_lookup_uses_the_cache(peppers):
    with patch.dict("os.environ", {"AI_API_KEY": "test-key"}):
        with patch.object(ai, "_call_model", return_value=str(peppers.id)) as called:
            ai.match_to_catalog("bell pepper")
            ai.match_to_catalog("bell pepper")

    assert called.call_count == 1
    assert CatalogMatch.objects.filter(query="bell pepper").count() == 1


@pytest.mark.django_db
def test_the_query_is_normalized_before_caching(peppers):
    # "Bell Pepper", "bell pepper" and "  BELL   pepper " are one row
    with patch.dict("os.environ", {"AI_API_KEY": "test-key"}):
        with patch.object(ai, "_call_model", return_value=str(peppers.id)) as called:
            ai.match_to_catalog("Bell Pepper")
            ai.match_to_catalog("  BELL   pepper ")

    assert called.call_count == 1
    assert CatalogMatch.objects.count() == 1


@pytest.mark.django_db
def test_a_miss_is_cached_too(peppers):
    # Without this we would pay for the same hopeless query forever
    with patch.dict("os.environ", {"AI_API_KEY": "test-key"}):
        with patch.object(ai, "_call_model", return_value="NONE") as called:
            assert ai.match_to_catalog("bell pepper") is None
            assert ai.match_to_catalog("bell pepper") is None

    assert called.call_count == 2
    assert CatalogMatch.objects.get(query="bell pepper").item is None


@pytest.mark.django_db
def test_falls_back_to_the_whole_catalog_when_the_shortlist_fails(peppers):
    """The shortlist is word overlap, so it cannot find "hamburger meat".

    "Beef, ground" has keywords "Beef,ground" -- no "hamburger", no "meat"
    -- so no amount of word matching reaches it. When the model says none
    of the shortlist fits, it gets shown everything.
    """
    with patch.dict("os.environ", {"AI_API_KEY": "test-key"}):
        with patch.object(ai, "_call_model",
                          side_effect=["NONE", str(peppers.id)]) as called:
            assert ai.match_to_catalog("bell pepper") == peppers

    assert called.call_count == 2


@pytest.mark.django_db
def test_giving_up_twice_caches_the_miss():
    with patch.dict("os.environ", {"AI_API_KEY": "test-key"}):
        with patch.object(ai, "_call_model", return_value="NONE") as called:
            assert ai.match_to_catalog("bell pepper") is None
            assert ai.match_to_catalog("bell pepper") is None

    # two rounds on the first query, nothing on the second
    assert called.call_count == 2
    assert CatalogMatch.objects.get(query="bell pepper").item is None


@pytest.mark.django_db
def test_nothing_resembling_the_query_still_asks_once():
    """An empty shortlist skips straight to the full catalog."""
    with patch.dict("os.environ", {"AI_API_KEY": "test-key"}):
        with patch.object(ai, "_call_model", return_value="NONE") as called:
            assert ai.match_to_catalog("zzzqqq") is None

    assert called.call_count == 1
    assert CatalogMatch.objects.get(query="zzzqqq").item is None


# --- boundary and error cases ----------------------------------------------

@pytest.mark.django_db
def test_no_api_key_turns_the_feature_off():
    # A teammate without a key, or CI, must still get working search
    with patch.dict("os.environ", {}, clear=True):
        assert ai.match_to_catalog("bell pepper") is None

    # and nothing is cached, because the key may exist next time
    assert CatalogMatch.objects.count() == 0


@pytest.mark.django_db
def test_a_dead_api_does_not_break_search():
    with patch.dict("os.environ", {"AI_API_KEY": "test-key"}):
        with patch.object(ai, "_call_model", side_effect=Exception("rate limit")):
            assert ai.match_to_catalog("bell pepper") is None
            assert not search_catalog("bell pepper").exists()

    # A rate limit is temporary, not an answer -- so it must not be cached
    assert CatalogMatch.objects.count() == 0


@pytest.mark.django_db
def test_an_id_outside_the_shortlist_is_ignored():
    # A model naming a food we did not offer must not be trusted
    with patch.dict("os.environ", {"AI_API_KEY": "test-key"}):
        with patch.object(ai, "_call_model", return_value="999999"):
            assert ai.match_to_catalog("bell pepper") is None


@pytest.mark.django_db
def test_prose_with_no_id_is_ignored():
    with patch.dict("os.environ", {"AI_API_KEY": "test-key"}):
        with patch.object(ai, "_call_model",
                          return_value="I think they meant peppers!"):
            assert ai.match_to_catalog("bell pepper") is None


@pytest.mark.django_db
def test_blank_queries_never_reach_the_model():
    with patch.object(ai, "_call_model") as called:
        assert ai.match_to_catalog("") is None
        assert ai.match_to_catalog("   ") is None

    called.assert_not_called()


# --- a seeded correction ---------------------------------------------------

@pytest.mark.django_db
def test_a_manual_row_overrides_the_model(peppers):
    """Pre-seeding lets us fix a bad match, or prepare demo terms for free."""
    CatalogMatch.objects.create(query="bell pepper", item=peppers,
                                source=CatalogMatch.MANUAL)

    with patch.object(ai, "_call_model") as called:
        assert ai.match_to_catalog("bell pepper") == peppers

    called.assert_not_called()



@pytest.mark.django_db
def test_a_refusal_to_spend_tokens_is_not_cached():
    # A prompt we declined to send says nothing about the food. Caching it
    # would turn a temporary budget into a permanent verdict, and the query
    # would stay dead after the budget was raised.
    with patch.dict("os.environ", {"AI_API_KEY": "test-key"}):
        with patch.object(ai, "MAX_PROMPT_TOKENS", 1):
            with patch.object(ai, "_call_model") as called:
                assert ai.match_to_catalog("bell pepper") is None
 
    called.assert_not_called()
    assert CatalogMatch.objects.count() == 0
 
 
@pytest.mark.django_db
def test_an_oversized_prompt_is_never_sent():
    # Spending the minute's budget on a request the API will reject is
    # worse than not asking: the user waits and still gets nothing.
    with patch.dict("os.environ", {"AI_API_KEY": "test-key"}):
        with patch.object(ai, "MAX_PROMPT_TOKENS", 1):
            with pytest.raises(ai.BudgetExceeded):
                ai._ask("bell pepper", list(GlobalCatalogItem.objects.all()[:5]))
