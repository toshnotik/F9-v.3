import os

from aiohttp import web

WS_FILE = os.path.join(os.path.dirname(__file__), "websocket.html")

# Список новостей (упрощенный аналог БД)
postList = []


# Функция, выполняющая запуск сессий, тест соединения, передачу клиенту стартовой html страницы
async def wshandler(request: web.Request):
    resp = web.WebSocketResponse()
    available = resp.can_prepare(request)
    if not available:
        with open(WS_FILE, "rb") as fp:
            return web.Response(body=fp.read(), content_type="text/html")

    await resp.prepare(request)

# при подключении клиента высылает ему список сохраненных в postList новостей
    for post in postList:
        await resp.send_str(post)

    try:
        print("Someone joined.")
        request.app["sockets"].append(resp)

        async for msg in resp:
            if msg.type == web.WSMsgType.TEXT:
                # Если получено сообщение Test - отсылаем клиенту ответное сообщение (своеобразная проверка соединения)
                if msg.data == "test":
                    print("Testing connection")
                    await resp.send_str("test checked")
                else:
                    # Если с клиента пришло сообщение - помещаем его в список новостей и рассылаем ее всем клиентам
                    postList.append(msg.data)
                    for ws in request.app["sockets"]:
                        await ws.send_str(msg.data)
            else:
                return resp
        return resp

    finally:
        request.app["sockets"].remove(resp)


# Функция обрабатывающая post запрос от клиента (сохраняет новость и рассылает её всем клиентам)
async def wspost(request: web.Request):
    new_post = request.query['text']
    print("post message", new_post)
    resp = web.WebSocketResponse()
    async for msg in resp:
        if msg.type == web.WSMsgType.TEXT:
            postList.append(new_post)
            for ws in request.app["sockets"]:
                await ws.send_str(msg.data)
    return resp


async def on_shutdown(app: web.Application):
    for ws in app["sockets"]:
        await ws.close()


def init():
    app = web.Application()
    app["sockets"] = []
    app.router.add_get("/", wshandler)
    app.router.add_post("/news", wspost)
    app.on_shutdown.append(on_shutdown)
    return app


web.run_app(init())