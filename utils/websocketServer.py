import asyncio
import websockets
from websockets.exceptions import ConnectionClosedOK
import threading
from PyQt5.QtCore import pyqtSignal, QObject, QThread

class WebSocket(QThread):
    receivedSignal = pyqtSignal(str)
    aaa = pyqtSignal(str)

    def __init__(self):
        QThread.__init__(self)
        self.record_loop = None
        self.websoc_svr = None
        self.data_rcv = ''


    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        if name == 'data_rcv' and value:
            self.receivedSignal.emit(value)


    def run(self):
        print('WebSocket Server Start')
        self.record_loop = asyncio.new_event_loop()
        self.websoc_svr = websockets.serve(self.accept, host="localhost", port=8089, loop=self.record_loop)
        self.worker()

    def worker(self):
        try:
          asyncio.set_event_loop(self.record_loop)
          self.record_loop.run_until_complete(self.websoc_svr)
          self.record_loop.run_forever()
        except OSError:
          pass


    async def accept(self, websocket, path):
        while True:
            try:
                self.data_rcv = await websocket.recv()
                print("received data-" + self.data_rcv)

                if self.data_rcv == 'window close':
                    break
            except ConnectionClosedOK:
                print('websockets.exceptions.ConnectionClosedOK')
                break

    def toggle_status(self):
        self._status = not self._status
        if self._status:
            self.cond.wakeAll()

    @property
    def status(self):
        return self._status

    def stop(self):
        self.terminate()
