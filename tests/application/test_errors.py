import pytest

from labyrinthes.application.errors import MazeNotFoundError, SettingNotFoundError
from labyrinthes.domain.errors import LabyrinthesError


@pytest.mark.parametrize("error_type", [MazeNotFoundError, SettingNotFoundError])
def test_application_errors_subclass_labyrinthes_error(error_type):
    assert issubclass(error_type, LabyrinthesError)


def test_maze_not_found_error_and_setting_not_found_error_are_distinct():
    assert MazeNotFoundError is not SettingNotFoundError
