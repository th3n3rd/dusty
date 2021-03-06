import sys
import logging
import logging.handlers
from .constants import SOCKET_PATH, SOCKET_LOGGER_NAME
from threading import RLock
import contextlib

handler = None
log_to_client_lock = RLock()

class DustySocketHandler(logging.Handler):
    def __init__(self, connection_socket):
        super(DustySocketHandler, self).__init__()
        self.connection_socket = connection_socket
        self.append_newlines = True

    def emit(self, record):
        msg = self.format(record)
        if isinstance(msg, unicode):
            msg = msg.encode('utf-8')
        if self.append_newlines:
            msg = msg.strip()
        self.connection_socket.sendall("{}{}".format(msg, '\n' if self.append_newlines else ''))

class DustyClientTestingSocketHandler(logging.Handler):
    def __init__(self):
        super(DustyClientTestingSocketHandler, self).__init__()
        self.log_to_client_output = ''
        self.append_newlines = True

    def emit(self, record):
        msg = self.format(record)
        self.log_to_client_output += '{}\n'.format(msg.encode('utf-8').strip())

client_logger = logging.getLogger(SOCKET_LOGGER_NAME)

def configure_logging():
    logging.basicConfig(stream=sys.stdout,
                        level=logging.INFO,
                        format='%(asctime)s %(levelname)s:%(name)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    logging.captureWarnings(True)

def make_socket_logger(connection_socket):
    global handler
    logger = logging.getLogger(SOCKET_LOGGER_NAME)
    handler = DustySocketHandler(connection_socket)
    logger.addHandler(handler)

def log_to_client(message):
    with log_to_client_lock:
        client_logger.info(message)

def close_socket_logger():
    global handler
    logger = logging.getLogger(SOCKET_LOGGER_NAME)
    logger.removeHandler(handler)
    handler = None

def configure_client_logging():
    client_logger.addHandler(logging.NullHandler())
    logging.basicConfig(stream=sys.stdout,
                        level=logging.INFO,
                        format='%(message)s')

@contextlib.contextmanager
def streaming_to_client():
    """Puts the client logger into streaming mode, which sends
    unbuffered input through to the socket one character at a time.
    We also disable propagation so the root logger does not
    receive many one-byte emissions. This context handler
    was originally created for streaming Compose up's
    terminal output through to the client and should only be
    used for similarly complex circumstances."""
    for handler in client_logger.handlers:
        if hasattr(handler, 'append_newlines'):
            break
    else:
        handler = None
    old_propagate = client_logger.propagate
    client_logger.propagate = False
    if handler is not None:
        old_append = handler.append_newlines
        handler.append_newlines = False
    yield
    client_logger.propagate = old_propagate
    if handler is not None:
        handler.append_newlines = old_append
