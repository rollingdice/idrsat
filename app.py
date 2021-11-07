import tornado.ioloop
import tornado.web
import tornado.httpclient
import tornado.gen
import math
import json
import os.path
from mimetypes import guess_type
import config

idrpersat = 10
fxtoken = config.fx_access_key

BASEDIR_NAME = os.path.dirname(__file__)
BASEDIR_PATH = os.path.abspath(BASEDIR_NAME)

FILES_ROOT = os.path.join(BASEDIR_PATH, 'static')
fxrate = 14000

historical_usd = json.load(open(os.path.join(BASEDIR_PATH, 'static/historical.json')))
historical_idr = []

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

class TemplateHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("template.html",idrpersat=str(idrpersat))

class HistoryHandler(tornado.web.RequestHandler):
    def get(self):
        self.write(json.dumps(historical_idr))

def make_app():
    return tornado.web.Application([
        (r"/", TemplateHandler),
        (r"/idrsat", MainHandler),
        (r"/historical", HistoryHandler),
        (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": FILES_ROOT}),
    ],{"template_path":BASEDIR_PATH,
        "static_path":BASEDIR_PATH+"/static"})

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

async def refresh_fxrate():
    global fxrate
    #sample request: http://api.currencylayer.com/live?access_key=1234567890abcdef0123456789abcdef&currencies=IDR&format=1
    api_root = "http://api.currencylayer.com"
    endpoint = "/live?currencies=IDR&format=1"
    access_token = "&access_key=" + fxtoken
    api_url = api_root + endpoint + access_token
    http_client = tornado.httpclient.AsyncHTTPClient()
    response = await http_client.fetch(api_url)
    response = json.loads(response.body)
    fxrate = response['quotes']['USDIDR']

async def refresh_history():
    global historical_usd, historical_idr
    http_client = tornado.httpclient.AsyncHTTPClient()
    response = await http_client.fetch("https://usdsat.com/historical")
    historical_usd = json.loads(response.body)
    for point in historical_usd:
        historical_idr.append({"date":point["date"],
                            "si":round(point["usdsat_rate"]/fxrate,4)})

async def minute_loop():
    while True:
        await refresh_price()
        await tornado.gen.sleep(60)

async def daily_loop():
    while True:
        await refresh_fxrate()
        await refresh_history()
        await tornado.gen.sleep(86400)

if __name__ == "__main__":
    app = make_app()
    app.listen(4000)
    io_loop = tornado.ioloop.IOLoop.current()
    io_loop.spawn_callback(minute_loop)
    io_loop.spawn_callback(daily_loop)
    io_loop.start()