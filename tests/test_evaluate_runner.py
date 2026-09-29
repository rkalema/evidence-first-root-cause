from scripts.evaluate_runner import prompt_packet,user_prompt,load_case

def test_gold_expectations_not_exposed():
    p=prompt_packet("insufficient-evidence","baseline")
    assert "expected" not in p["user"].lower()
    assert "pass_score" not in p["user"].lower()

def test_user_prompt_same_between_modes():
    a=prompt_packet("price-vs-stockout","baseline")
    b=prompt_packet("price-vs-stockout","evidence-first")
    assert a["user"]==b["user"]
    assert a["system"]!=b["system"]
