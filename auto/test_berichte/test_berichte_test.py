from auto.test_berichte.test_berichte import find_score


def test_find_score_for_vw_golf():
    score = find_score("vw golf 2020")
    assert score["average"] > 0.5
    assert 558 in [s["score"] for s in score["scores"]]


def test_find_score_for_opel_astra():
    score = find_score("opel astra")
    assert score["average"] > 0.5
    assert 517 in [s["score"] for s in score["scores"]]


def test_find_score_for_opel_corsa():
    score = find_score("opel corsa")
    assert score["name"] == "Opel Corsa (2019)"
    assert score["average"] > 0.5
    assert 488 in [s["score"] for s in score["scores"]]


def test_find_score_for_opel_grandland():
    score = find_score("opel grandland")
    assert score["name"] == "Opel Grandland X (2017)"
    assert score["average"] > 0.5
    assert 508 in [s["score"] for s in score["scores"]]


def test_find_score_for_kia_ceed():
    score = find_score("kia ceed")
    assert score["name"] == "Kia Ceed (2018)"
    assert score["average"] > 0.5
    assert 531 in [s["score"] for s in score["scores"]]
