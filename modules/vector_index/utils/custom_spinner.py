from __future__ import annotations

import contextlib
import threading
import time
from typing import Iterator, List

import streamlit as st
from streamlit.runtime.scriptrunner import add_script_run_ctx
from streamlit.proto.Spinner_pb2 import Spinner as SpinnerProto
from streamlit.string_util import clean_text

@contextlib.contextmanager
def message_spinner(texts=None, *, _cache: bool = False) -> Iterator[None]:
    """Temporarily displays a message while executing a block of code."""
    if texts is None:
        texts = ["In progress..."]

    message = st.empty()
    display_message = threading.Event()
    display_message.set()

    def set_message():
        i = 0
        while display_message.is_set():
            spinner_proto = SpinnerProto()
            spinner_proto.text = clean_text(texts[i])
            spinner_proto.cache = _cache
            message._enqueue("spinner", spinner_proto)
            i = (i + 1) % len(texts)
            time.sleep(2)

    thread = threading.Thread(target=set_message)
    add_script_run_ctx(thread)
    thread.start()

    try:
        yield
    finally:
        display_message.clear()
        thread.join()
        if "chat_message" in set(message._active_dg._ancestor_block_types):
            message.container()
        else:
            message.empty()
