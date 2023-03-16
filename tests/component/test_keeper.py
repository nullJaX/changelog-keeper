import pytest
from pytest_mock import MockerFixture
from changelog_keeper.keeper import Config, Changelog, ChangelogKeeper, Operation


class TestKeeper:
    @pytest.fixture
    def changelog(self) -> Changelog:
        return Changelog()

    @pytest.mark.parametrize("operation", list(Operation))
    def test_run(
        self, operation: Operation, changelog: Changelog, mocker: MockerFixture
    ):
        mocked_load = mocker.MagicMock()
        mocked_load.return_value = changelog
        mocked_save = mocker.MagicMock()
        mocker.patch("changelog_keeper.keeper.ChangelogParser.load", mocked_load)
        mocker.patch("changelog_keeper.keeper.ChangelogParser.save", mocked_save)
        mocked_methods = {}
        for method in list(Operation):
            mocked_methods[method] = mocker.MagicMock()
            mocker.patch.object(
                ChangelogKeeper, "_" + method.value, mocked_methods[method]
            )
        mocked_methods[Operation.CREATE].return_value = changelog

        config: Config = Config(operation, None, None, None, None)
        keeper = ChangelogKeeper(config)
        keeper.run()

        mocked_save.assert_called_with(changelog, config.file)
        if operation == Operation.CREATE:
            mocked_methods[Operation.CREATE].assert_called_once()
        else:
            mocked_methods[Operation.CHECK].assert_called_once_with(changelog)
            mocked_methods[operation].assert_called_once_with(changelog)
