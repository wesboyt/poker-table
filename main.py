from fastapi import FastAPI, WebSocket
import json
import uuid
import uvicorn
from pydantic import BaseModel
from queue import Queue
from fastapi.responses import HTMLResponse
app = FastAPI()
games = {}
players = set()
waitlist = Queue()

def read_root():
    return {"Hello": "World"}

class Item(BaseModel):
    hh: str

@app.post("/map/")
def read_item(hh: Item):
    return {'body': "result"}



app = FastAPI()

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("ws://localhost:8000/ws");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""


@app.get("/")
async def get():
    return HTMLResponse(html)



@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text("taco")



if __name__ == '__main__':
    uvicorn.run(app, host="localhost", port=8000)


