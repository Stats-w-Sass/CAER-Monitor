from scraper.classifier import classify_message


def test_classify_message_with_multiple_categories():
    categories = classify_message("Startup procedures may result in noise, smoke and flaring.")
    assert "Flaring" in categories
    assert "Noise" in categories
    assert "Smoke" in categories


def test_classify_training_drill_message():
    categories = classify_message("*** THIS IS A DRILL *** This is a message from TotalEnergies La Porte.")
    assert "Training/Drills" in categories
