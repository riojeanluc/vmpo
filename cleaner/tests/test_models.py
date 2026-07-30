from cleaner_app.models import Action, Target


def test_size_mb_conversion():
    target = Target(category="system", subcategory="temp", path="/tmp/x",
                     description="test", size_bytes=2 * 1024 * 1024)
    assert target.size_mb() == 2.0


def test_default_action_is_delete_file():
    target = Target(category="system", subcategory="temp", path="/tmp/x", description="test")
    assert target.action == Action.DELETE_FILE
