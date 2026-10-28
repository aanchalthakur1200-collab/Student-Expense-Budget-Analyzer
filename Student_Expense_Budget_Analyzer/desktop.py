import threading

import webview
from werkzeug.serving import make_server

from app import app

WINDOW_TITLE = "Student Expense Analyzer"


def start_local_server():
    server = make_server("127.0.0.1", 0, app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, name="expense-dashboard-server", daemon=True)
    thread.start()
    return server, thread, f"http://127.0.0.1:{server.server_port}"


def main():
    server, _thread, app_url = start_local_server()
    try:
        webview.create_window(
            WINDOW_TITLE,
            app_url,
            width=1280,
            height=820,
            min_size=(900, 620),
            background_color="#f7f6fb",
        )
        webview.start(gui="edgechromium", debug=False)
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
