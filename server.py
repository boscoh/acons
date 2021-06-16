import inspect
import logging
import threading
import time
import traceback
import webbrowser
from pathlib import Path
from urllib.request import urlopen

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse

import acons as handlers

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

app = FastAPI()

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


@app.post("/rpc-run")
async def rpc_run(data: dict):
    job_id = data.get("id", None)
    method = data.get("method")
    params = data.get("params", [])
    try:
        if not hasattr(handlers, method):
            raise Exception(f"rpc-run {method} is not found")
        fn = getattr(handlers, method)
        if inspect.iscoroutinefunction(fn):
            result = await fn(*params)
        else:
            result = fn(*params)
        logger.debug(f"rpc-run {method}")
        return {"result": result, "jsonrpc": "2.0", "id": job_id}
    except Exception as e:
        print(traceback.format_exc())
        return {
            "error": {"code": -1, "message": str(e)},
            "jsonrpc": "2.0",
            "id": job_id,
        }


index = Path(__file__).resolve().parent / "index.html"


@app.get("/")
async def serve_index_htm(request: Request):
    return FileResponse(str(index))


def open_url_when_ready(url, sleep_in_s=1):
    """
    Polls server in background thread to open webpage
    """

    def inner():
        elapsed = 0
        while True:
            try:
                response_code = urlopen(url).getcode()
                if response_code < 400:
                    logger.info(f"open_url_in_background success")
                    webbrowser.open(url)
                    return
            except:
                time.sleep(sleep_in_s)
                elapsed += sleep_in_s
                logger.info(f"open_url_in_background waiting {elapsed}s")

    threading.Thread(target=inner).start()


open_url_when_ready("http://127.0.0.1:5200")
