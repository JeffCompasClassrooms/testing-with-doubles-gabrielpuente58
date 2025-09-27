import json
import pytest
import squirrel_server
import squirrel_db


def describe_SquirrelServerHandler():

    @pytest.fixture
    def handler_cls():
        return squirrel_server.SquirrelServerHandler

    @pytest.fixture
    def fake_db(mocker):
        db = mocker.Mock(spec=squirrel_db.SquirrelDB)
        db.getSquirrels.return_value = [{"id": 1, "name": "Fluffy", "size": "large"}]
        db.getSquirrel.return_value = {"id": 1, "name": "Fluffy", "size": "large"}
        db.createSquirrel.return_value = None
        db.updateSquirrel.return_value = None
        db.deleteSquirrel.return_value = None
        return db

    @pytest.fixture
    def make_handler(handler_cls, http_harness, mocker, fake_db):

        def _build(method: str, path: str, body: bytes = b"", headers=None):
            req = http_harness(body=body, headers=headers or {})
            h = object.__new__(handler_cls)  # bypass BaseHTTPRequestHandler.__init__
            h.rfile = req.rfile
            h.wfile = req.wfile
            h.headers = req.headers
            h.command = method
            h.path = path

            h.send_response = req.send_response
            h.send_header = req.send_header
            h.end_headers = req.end_headers

            mocker.patch.object(squirrel_server, "SquirrelDB", autospec=True, return_value=fake_db)
            return h, req, fake_db
        return _build

    def it_handleSquirrelsIndex_lists_and_writes_json(make_handler):
        h, req, db = make_handler("GET", "/squirrels")
        h.handleSquirrelsIndex()

        db.getSquirrels.assert_called_once()
        req.send_response.assert_called_once_with(200)
        req.send_header.assert_any_call("Content-Type", "application/json")
        req.end_headers.assert_called_once()

        body = req.wfile.getvalue()
        data = json.loads(body.decode("utf-8"))
        assert isinstance(data, list) and data[0]["id"] == 1

    def it_handleSquirrelsRetrieve_returns_item_when_found(make_handler, fake_db):
        fake_db.getSquirrel.return_value = {"id": 7, "name": "Sandy", "size": "small"}
        h, req, db = make_handler("GET", "/squirrels/7")

        h.handleSquirrelsRetrieve("7")  # note: method receives string id in your code

        db.getSquirrel.assert_called_once_with("7")
        req.send_response.assert_called_once_with(200)
        req.send_header.assert_any_call("Content-Type", "application/json")
        req.end_headers.assert_called_once()
        assert b"Sandy" in req.wfile.getvalue()

    def it_handleSquirrelsRetrieve_404_when_missing(make_handler, fake_db, mocker):
        fake_db.getSquirrel.return_value = None
        h, req, db = make_handler("GET", "/squirrels/999")

        handle404_spy = mocker.spy(h, "handle404")
        h.handleSquirrelsRetrieve("999")

        db.getSquirrel.assert_called_once_with("999")
        handle404_spy.assert_called_once()
        called_codes = [c.args[0] for c in req.send_response.call_args_list]
        assert 404 in called_codes


    def it_handleSquirrelsCreate_reads_body_and_calls_create(make_handler):
        body = b"name=Rex&size=medium"
        headers = {"Content-Length": str(len(body))}
        h, req, db = make_handler("POST", "/squirrels", body=body, headers=headers)

        h.handleSquirrelsCreate()

        db.createSquirrel.assert_called_once_with("Rex", "medium")
        req.send_response.assert_called_once_with(201)
        req.end_headers.assert_called_once()

    def it_handleSquirrelsUpdate_calls_update_when_target_exists(make_handler, fake_db):
        fake_db.getSquirrel.return_value = {"id": "3", "name": "Old", "size": "large"}
        body = b"name=New&size=small"
        headers = {"Content-Length": str(len(body))}
        h, req, db = make_handler("PUT", "/squirrels/3", body=body, headers=headers)

        h.handleSquirrelsUpdate("3")

        db.getSquirrel.assert_called_once_with("3")
        db.updateSquirrel.assert_called_once_with("3", "New", "small")
        req.send_response.assert_called_once_with(204)
        req.end_headers.assert_called_once()

    def it_handleSquirrelsUpdate_404_when_missing(make_handler, fake_db, mocker):
        fake_db.getSquirrel.return_value = None
        h, req, db = make_handler("PUT", "/squirrels/42")

        handle404_spy = mocker.spy(h, "handle404")
        h.handleSquirrelsUpdate("42")

        db.getSquirrel.assert_called_once_with("42")
        handle404_spy.assert_called_once()
        called_codes = [c.args[0] for c in req.send_response.call_args_list]
        assert 404 in called_codes

    def it_handleSquirrelsDelete_calls_delete_when_target_exists(make_handler, fake_db):
        fake_db.getSquirrel.return_value = {"id": "5"}
        h, req, db = make_handler("DELETE", "/squirrels/5")

        h.handleSquirrelsDelete("5")

        db.getSquirrel.assert_called_once_with("5")
        db.deleteSquirrel.assert_called_once_with("5")
        req.send_response.assert_called_once_with(204)
        req.end_headers.assert_called_once()

    def it_handleSquirrelsDelete_404_when_missing(make_handler, fake_db):
        fake_db.getSquirrel.return_value = None
        h, req, db = make_handler("DELETE", "/squirrels/404")

        h.handleSquirrelsDelete("404")

        db.getSquirrel.assert_called_once_with("404")
        called_codes = [c.args[0] for c in h.send_response.call_args_list]
        assert 404 in called_codes

    def it_handle404_sets_headers_and_body(make_handler):
        h, req, _ = make_handler("GET", "/nope")

        h.handle404()

        req.send_response.assert_called_once_with(404)
        req.send_header.assert_any_call("Content-Type", "text/plain")
        req.end_headers.assert_called_once()
        assert b"404 Not Found" in req.wfile.getvalue()
