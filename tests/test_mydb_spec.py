import builtins
import os
import pickle
import pytest
import mydb


def describe_MyDB():

    @pytest.fixture
    def dbfile(tmp_path):
        return str(tmp_path / "test.db")

    def it_calls_saveStrings_in___init___when_file_absent(dbfile, mocker):
        mocker.patch.object(os.path, "isfile", autospec=True, return_value=False)
        save_mock = mocker.patch.object(mydb.MyDB, "saveStrings", autospec=True)

        obj = mydb.MyDB(dbfile)

        save_mock.assert_called_once_with(obj, [])
        assert obj.fname == dbfile

    def it_does_not_call_saveStrings_in___init___when_file_exists(dbfile, mocker):
        mocker.patch.object(os.path, "isfile", autospec=True, return_value=True)
        save_mock = mocker.patch.object(mydb.MyDB, "saveStrings", autospec=True)

        obj = mydb.MyDB(dbfile)

        save_mock.assert_not_called()
        assert obj.fname == dbfile

    def it_loadStrings_reads_via_open_and_pickle_load(dbfile, mocker, fake_fs):
        mocker.patch.object(builtins, "open", side_effect=fake_fs.open)
        load_stub = mocker.patch.object(pickle, "load", autospec=True, return_value=["x", "y"])

        obj = mydb.MyDB(dbfile)
        mocker.patch.object(os.path, "isfile", return_value=True)

        result = obj.loadStrings()

        assert result == ["x", "y"]
        load_stub.assert_called_once()

    def it_saveStrings_writes_via_open_and_pickle_dump(dbfile, mocker, fake_fs):
        mocker.patch.object(builtins, "open", side_effect=fake_fs.open)
        dump_mock = mocker.patch.object(pickle, "dump", autospec=True)

        obj = mydb.MyDB(dbfile)
        mocker.patch.object(os.path, "isfile", return_value=True)

        payload = ["a", "b"]
        obj.saveStrings(payload)

        dump_mock.assert_called_once()
        args, kwargs = dump_mock.call_args
        assert args[0] == payload
        assert hasattr(args[1], "write")  # file-like

    def it_saveString_appends_and_saves(dbfile, mocker):
        obj = mydb.MyDB(dbfile)
        mocker.patch.object(os.path, "isfile", return_value=True)

        load_mock = mocker.patch.object(mydb.MyDB, "loadStrings", autospec=True, return_value=["a"])
        save_mock = mocker.patch.object(mydb.MyDB, "saveStrings", autospec=True)

        obj.saveString("b")

        load_mock.assert_called_once_with(obj)
        save_mock.assert_called_once_with(obj, ["a", "b"])
