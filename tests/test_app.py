from streamlit.testing.v1 import AppTest
from coursepilot.catalogue import ROOT

def test_app_load_and_recommend():
    at=AppTest.from_file(ROOT / "app.py",default_timeout=30).run()
    assert not at.exception
    at.selectbox[0].select("AI engineer").run()
    at.button[0].click().run()
    assert not at.exception
    assert at.session_state["result"]["recommendations"]
    assert at.session_state["result"]["method"]=="tfidf"

def test_study_can_prepare_without_showing_ranking():
    at=AppTest.from_file(ROOT / "app.py",default_timeout=30).run()
    at.text_area[0].set_value("search engines")
    at.button[1].click().run()
    assert not at.exception
    assert at.session_state["profile"]["query"]=="search engines"
    assert "result" not in at.session_state


def test_custom_field_reaches_recommender():
    at=AppTest.from_file(ROOT / "app.py",default_timeout=30).run()
    at.text_input(key="field_My own profile").set_value("robotics")
    at.button[0].click().run()
    assert not at.exception
    assert at.session_state["profile"]["query"] == "robotics"
    assert at.session_state["profile"]["completed"] == []
    assert at.session_state["result"]["recommendations"]
