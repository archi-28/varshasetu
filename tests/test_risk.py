from src.risk.risk_engine import risk_level, overall_risk
from src.risk.onset_detector import detect_onset

def test_risk_bands():
    assert risk_level(20)=="LOW" and risk_level(45)=="MODERATE" and risk_level(70)=="HIGH" and risk_level(90)=="VERY HIGH"

def test_onset_and_false_onset():
    assert detect_onset([0,4,5,3,0,0,0,0,0,0])["false_onset_risk"]
    assert detect_onset([0,0,0])["status"] == "No onset"

def test_overall_bounded():
    assert 0 <= overall_risk(.5,.2,.1) <= 100
