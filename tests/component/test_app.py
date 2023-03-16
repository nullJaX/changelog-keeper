import pytest
from pytest_mock import MockerFixture
from changelog_keeper.app import App
from changelog_keeper.model import Config, Operation


class TestApp:
    @pytest.mark.parametrize(
        "error,code", [(error, code) for error, code in App.ERROR_CODES.items()]
    )
    def test_run_internal(self, error, code, capsys, mocker: MockerFixture):
        example_error_message = "Some error occured!"

        def mocked_cli(_):
            return Config(Operation.CHECK, None, None, None, None)

        def mocked_keeper_run():
            raise error(example_error_message)

        mocked_keeper = mocker.MagicMock()
        mocked_keeper.return_value.run = mocked_keeper_run
        mocker.patch("changelog_keeper.app.cli", mocked_cli)
        mocker.patch("changelog_keeper.app.ChangelogKeeper", mocked_keeper)
        assert App([]).run() == code
        assert App.ERROR_MSG.format(example_error_message) in capsys.readouterr().out
