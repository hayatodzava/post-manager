import asyncio
import threading
from PySide6.QtCore import QObject, Signal

_app_loop: asyncio.AbstractEventLoop | None = None

# Class for safely delivering callbacks to the main thread
class CallbackDispatcher(QObject):
    """A dispatcher that executes callbacks on the Qt main thread"""
    success_signal = Signal(object)  # (result)
    error_signal = Signal(object)    # (error)
    
    def __init__(self):
        super().__init__()
        self.on_success = None
        self.on_error = None
        self.success_signal.connect(self._on_success)
        self.error_signal.connect(self._on_error)
    
    def set_callbacks(self, on_success=None, on_error=None):
        self.on_success = on_success
        self.on_error = on_error
    
    def _on_success(self, result):
        if self.on_success:
            self.on_success(result)
    
    def _on_error(self, error):
        if self.on_error:
            self.on_error(error)

# Global Dispatcher
_dispatcher: CallbackDispatcher | None = None

def init_async_loop():
    """Initializes the asyncio event loop"""
    global _app_loop, _dispatcher
    
    # Creating the dispatcher in the main thread
    _dispatcher = CallbackDispatcher()
    
    # Starting the event loop in a separate thread
    _app_loop = asyncio.new_event_loop()
    
    def run_loop():
        asyncio.set_event_loop(_app_loop)
        _app_loop.run_forever()
    
    thread = threading.Thread(target=run_loop, daemon=True)
    thread.start()

def run_async(coro):
    """Launches a coroutine on a background thread"""
    global _app_loop
    if _app_loop is None:
        raise RuntimeError("Async loop not initialized. Call init_async_loop() first.")
    return asyncio.run_coroutine_threadsafe(coro, _app_loop)

def safe_run_async(coro, on_success=None, on_error=None):
    global _dispatcher
    
    if _dispatcher is None:
        raise RuntimeError("Dispatcher not initialized. Call init_async_loop() first.")

    _dispatcher.set_callbacks(on_success, on_error)
    
    def done_callback(future):
        try:
            result = future.result()
            _dispatcher.success_signal.emit(result)
        except Exception as e:
            _dispatcher.error_signal.emit(e)
    
    future = run_async(coro)
    future.add_done_callback(done_callback)
    return future