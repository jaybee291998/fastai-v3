import aiohttp
import asyncio
import uvicorn
from fastai import *
from fastai.vision import *
from io import BytesIO
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse, JSONResponse
from starlette.staticfiles import StaticFiles
from pathlib import Path

export_file_url = 'https://www.dropbox.com/s/wuyd1myn5j6chk4/meme_classifierV2.pkl?raw=1'
export_file_name = 'export.pkl'

# classes = ['pepe', 'doge', 'drake hotline bling', 'two buttons', 'running away balloon', 'Left Exit 12 Off Ramp','Buff Doge vs. Cheems', 'Change My Mind', 'Gru\'s Plan', 'Bernie I Am Once Again Asking For Your Support','Woman Yelling At Cat', 'Batman Slapping Robin', 'Waiting Skeleton', 'Expanding Brain', 'Epic Handshake','Disaster Girl', 'Tuxedo Winnie The Pooh', 'Sad Pablo Escobar', 'Boardroom Meeting Suggestion', 'I Bet He\'s Thinking About Other Women', 'Monkey Puppet', 'Panik Kalm Panik', 'Always Has Been','Mocking Spongebob', 'X, X Everywhere', 'Anakin Padme 4 Panel', 'Blank Nut Button', 'Hide the Pain Harold','They\'re The Same Picture', 'Bike Fall', 'Is This A Pigeon', 'Clown Applying Makeup', 'One Does Not Simply','Trade Offer', 'Guy Holding Cardboard Sign', 'Inhaling Seagull', 'This Is Fine', 'Ancient Aliens', 'The Rock Driving','The Scroll Of Truth']
# classes = ['black', 'grizzly', 'teddys']
classes = [i for i in range(40)]
print(classes)
path = Path(__file__).parent

app = Starlette()
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_headers=['X-Requested-With', 'Content-Type'])
app.mount('/static', StaticFiles(directory='app/static'))


async def download_file(url, dest):
    if dest.exists(): return
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.read()
            with open(dest, 'wb') as f:
                f.write(data)


async def setup_learner():
    await download_file(export_file_url, path / export_file_name)
    try:
        learn = load_learner(path, export_file_name)
        return learn
    except RuntimeError as e:
        if len(e.args) > 0 and 'CPU-only machine' in e.args[0]:
            print(e)
            message = "\n\nThis model was trained with an old version of fastai and will not work in a CPU environment.\n\nPlease update the fastai library in your training environment and export your model again.\n\nSee instructions for 'Returning to work' at https://course.fast.ai."
            raise RuntimeError(message)
        else:
            raise


loop = asyncio.get_event_loop()
tasks = [asyncio.ensure_future(setup_learner())]
learn = loop.run_until_complete(asyncio.gather(*tasks))[0]
loop.close()


@app.route('/')
async def homepage(request):
    html_file = path / 'view' / 'index.html'
    return HTMLResponse(html_file.open().read())


@app.route('/analyze', methods=['POST'])
async def analyze(request):
    img_data = await request.form()
    img_bytes = await (img_data['file'].read())
    img = open_image(BytesIO(img_bytes))
    prediction = learn.predict(img)[0]
    return JSONResponse({'result': str(prediction)})


if __name__ == '__main__':
    if 'serve' in sys.argv:
        uvicorn.run(app=app, host='0.0.0.0', port=5000, log_level="info")
