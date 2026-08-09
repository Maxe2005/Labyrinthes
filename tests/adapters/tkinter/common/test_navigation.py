from labyrinthes.adapters.tkinter.common.navigation import ScreenId
from labyrinthes.app import router as app_router


def test_screen_id_has_exactly_home_builder_player_members():
    assert {member.value for member in ScreenId} == {"home", "builder", "player"}


def test_router_screen_id_is_the_same_object_re_exported_unchanged():
    # `app/router.py` must re-export `common/navigation.py`'s `ScreenId`
    # unchanged -- `from labyrinthes.app.router import ScreenId` (Story 1.7's
    # existing call sites) must keep resolving to the exact same enum, not a
    # look-alike copy.
    assert app_router.ScreenId is ScreenId
