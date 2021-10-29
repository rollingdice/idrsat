import requests
import tornado.ioloop
import tornado.web
import tornado.httpclient
import tornado.gen
import math
import json

idrpersat = 10

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write(str(idrpersat))

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
    ])

async def refresh_price():
    global idrpersat
    api_root = "https://indodax.com"
    endpoint = "/api/ticker/btcidr"
    api_url = api_root + endpoint

    http_client = tornado.httpclient.AsyncHTTPClient()
    response = await http_client.fetch(api_url)
    response = json.loads(response.body)
    price = int((int(response['ticker']['buy']) + int(response['ticker']['sell']))/2)
    idrpersat = round (price / 100000000, 2)

async def minute_loop():
    while True:
        await refresh_price()
        await tornado.gen.sleep(60)

if __name__ == "__main__":
    app = make_app()
    app.listen(4000)
    io_loop = tornado.ioloop.IOLoop.current()
    io_loop.spawn_callback(minute_loop)
    io_loop.start()