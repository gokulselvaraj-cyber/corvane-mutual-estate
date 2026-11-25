from corvane_fraud.llm_triage import build_prompt

TEMPLATE = "{claim_id}|{claimant_name}|{injury_notes}|{narrative}"


def test_prompt_contains_injury_notes(make_request):
    req = make_request(injury_notes="whiplash, neck brace 3 weeks")
    prompt = build_prompt(req, TEMPLATE)
    # Documents current behaviour (FRAUD-412): injury notes and the name are sent unmasked.
    assert "whiplash" in prompt
    assert "Test Person" in prompt


def test_prompt_is_truncated(make_request):
    req = make_request(narrative="x" * 10000)
    assert len(build_prompt(req, TEMPLATE)) == 6000
