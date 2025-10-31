from tasklist_app.utils import extract_tags

def test_extract_tags_all():
    text = "hola @dev-team #alldone correo somebody@gmail.com y https://www.google.com"
    tags = extract_tags(text)
    assert "@dev-team" in tags
    assert "#alldone" in tags
    assert "somebody@gmail.com" in tags
    assert "https://www.google.com" in tags
