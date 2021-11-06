import tornado.ioloop
import tornado.web
import tornado.httpclient
import tornado.gen
import math
import json
import os.path
from mimetypes import guess_type

idrpersat = 10

BASEDIR_NAME = os.path.dirname(__file__)
BASEDIR_PATH = os.path.abspath(BASEDIR_NAME)

FILES_ROOT = os.path.join(BASEDIR_PATH, 'static')

class MainHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
    
    def get(self):
        self.write(str(idrpersat))

class FileHandler(tornado.web.RequestHandler):
    def get(self, path):
        file_location = os.path.join(FILES_ROOT, path)
        if not os.path.isfile(file_location):
            raise tornado.web.HTTPError(status_code=404)
        content_type, _ = guess_type(file_location)
        self.add_header('Content-Type', content_type)
        with open(file_location) as source_file:
            self.write(source_file.read())

def make_app():
    return tornado.web.Application([
        (r"/idrsat", MainHandler),
        tornado.web.url(r"/static/(.+)", FileHandler),
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