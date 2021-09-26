# Autor: Manuel Saravia Enrech
# ReactiveX (rxpy), Tkinter y AsyncIO.

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import rx
import aiohttp
import asyncio
import threading
from bs4 import BeautifulSoup
from PIL import ImageTk, Image
from io import BytesIO

''' Variables y costantes del modulo '''
DEFAULT_URL = 'https://www.imdb.com/'  # in case no URL introduced
# lista de imagenes de la URL introducida por el usuario
url_imgs = {'url_page': '',
            'list_img_src': [],
            'list_img_names': [],
            'list_img_content': [],
            'img_name_to_index': {}
            }
aio_session = None  # global var for aiohttp client session

''' Class MainWindowObserver: for Observable-observer notifications '''
class MainWindowObserver(rx.core.Observer):
    ''' recibe notificaciones de cada imagen leida para actualizar el GUI '''
    def on_next(self, t):
        index = t.result()  # result of load_one_image task
        if index >= 0:
            src = url_imgs['list_img_src'][index]
            print(f'>>> MainWindowObserver: Loaded photo {index}: {src}')
            app.update_listbox(index)
        app.update_progressbar()  # even if img_src error (index < 0)


''' Class App: for GUI building and handling '''
class App:
    def __init__(self, async_loop):
        self.async_loop = async_loop
        # main window
        self.w_width = 600
        self.w_height = 500
        self.window = tk.Tk()
        self.window.title('MSE-P1 Asyncio')
        self.window.configure(width=self.w_width, height=self.w_height)
        self.window.resizable(False, False)
        # Texto1 de URl a procesar  + casilla input
        self.label1 = ttk.Label(text='URL a procesar')
        self.label1.place(x=80, y=20)
        self.entry = ttk.Entry()
        self.entry.place(x=self.w_width/2-40, y=20, width=self.w_width/2-30)
        # Button to do_tasks
        self.button = ttk.Button(text='Buscar', width=35, command=lambda: do_tasks(self.async_loop))
        self.button.place(x=self.w_width/4, y=50, width=self.w_width/2)
        # Listbox para los nombres de las imagenes con scrollbar
        self.listbox = tk.Listbox(bg='#f3f3f3', fg='black')
        self.listbox.place(x=20, y=120, width=self.w_width/2-60, height=self.w_height/2)
        self.listbox.bind("<<ListboxSelect>>", self.listboxSelected)
        # Canvas and photo
        self.c_width = self.w_width/2-50
        self.c_height = self.c_width
        self.canvas = tk.Canvas(self.window, width=self.c_width, height=self.c_height, bg='white')  # #f3f3f3
        self.canvas.place(x=self.w_width/2+20, y=120)
        self.photo = None
        # progress bar
        self.progressbar = ttk.Progressbar(length=200)
        self.progressbar.place(x=self.w_width/2+20, y=self.w_height-80)
        self.progressbar['value'] = 0
        self.progress_step = 10
        # texto2 con numero de imagenes
        self.label2 = ttk.Label(text='')
        self.label2.place(x=self.w_width/2+20, y=self.w_height-40)
        # Texto3 de lista de imagenes
        self.label3 = ttk.Label(text='Lista de imágenes')
        self.label3.place(x=60, y=120+self.w_height/2+10)

    def mainloop(self):
        self.window.mainloop()

    def get_async_loop(self):
        return self.async_loop

    def get_URL(self):
        return self.entry.get()

    def get_canvas_size(self):
        return self.c_width, self.c_height

    def set_progress_step(self, step):
        self.progress_step = step

    def set_label_num_imgs(self, num_imgs):
        self.label2.configure(text=f'Se encontraron {num_imgs} imágenes')

    def update_listbox(self, index):
        # insertamos img_name in listbox
        self.listbox.insert(tk.END, url_imgs['list_img_names'][index])

    def update_progressbar(self):
        # incrementamos la progressbar
        self.progressbar['value'] += self.progress_step

    def listboxSelected(self, event):
        selection = event.widget.curselection()
        index = selection[0]
        img_name = event.widget.get(index)
        #  mostrar imagen (index) centrada en el canvas
        self.canvas.delete(self.photo)
        index = url_imgs['img_name_to_index'][img_name]
        try:
            self.photo = self.canvas.create_image(0, 0, anchor=tk.NW, image=url_imgs['list_img_content'][index])
        except:
            messagebox.showinfo(message='Error: unable to show the linked picture')
        #print(f'>> listbox selected ({img_name}) -> index {index}')

    def clear_gui(self):
        # empty listbox, reset progressbar, empty label2
        self.listbox.delete(0, tk.END)
        self.progressbar['value'] = 0
        self.label2.configure(text='')
        # remove photo from canvas if any
        if self.photo:
            self.canvas.delete(self.photo)
            self.photo = None
        # reset url_imgs variable
        url_imgs['url_page'] = ''
        url_imgs['list_img_src'] = []
        url_imgs['list_img_content'] = []
        url_imgs['img_name_to_index'] = {}


async def open_aio_session():
    global aio_session
    aio_session = aiohttp.ClientSession()
    return


async def close_aio_session():
    await aio_session.close()
    return


def list_imgs_from_page(page_text):
    def img_name(img):
        if img.get('alt'):
            name = "- " + img.get('alt')[:33]  # maximo 35 chars (primeros)
        else:
            name = "- " + img.get('src').split("/")[-1][-33:]  # max. 35 chars (ultimos)
        return name
    # recuperamos la lista de imagenes de la pagina
    soup = BeautifulSoup(page_text, 'html.parser')
    list_imgs = soup.find_all('img')
    url_imgs['list_img_src'] = [img.get('src') for img in list_imgs]
    url_imgs['list_img_names'] = [img_name(img) for img in list_imgs]
    url_imgs['list_img_content'] = [None for img in list_imgs]
    url_imgs['img_name_to_index'] = {k: i for i, k in enumerate(url_imgs['list_img_names'])}
    return len(url_imgs['list_img_src'])


async def load_page():
    url_imgs['url_page'] = app.get_URL()
    if url_imgs['url_page'] == '':
        messagebox.showinfo(message=(f'>>> URL no introducida. Usaremos DEFAULT_URL: {DEFAULT_URL}'))
        url_imgs['url_page'] = DEFAULT_URL
    print(f'>>> load_page, url: {url_imgs["url_page"]}')
    try:
        async with aio_session.get(url_imgs['url_page']) as content:
            page_text = await content.text()
    except:
        messagebox.showinfo(message='URL open error. Chequee que la URL comience por http:// or https://')
        return -1
    num_imgs = list_imgs_from_page(page_text)
    print(f'>>> load_page, num_imgs: {num_imgs}')
    # actualizamos label con el numero de imagenes
    app.set_label_num_imgs(num_imgs)
    # asignamos el progress step (lineal respecto al total de imagenes)
    if num_imgs != 0:
        app.set_progress_step(100 / float(num_imgs))
    return num_imgs


async def load_one_image(index):
    src = url_imgs['list_img_src'][index]
    print(f'>>> load_one_image {index}: {src}')
    try:
        async with aio_session.get(src) as content:
            picture_read = await content.read()
    except:
        return -1
    # create an image file object
    my_picture = BytesIO(picture_read)
    # use PIL to open image formats like .jpg  .png  .gif  etc.
    try:
        pil_img = Image.open(my_picture)
    except:
        return -2
    # resize picture
    c_width, c_height = app.get_canvas_size()
    img_ratio = min(c_width / float(pil_img.size[0]), c_height / float(pil_img.size[1]))
    wsize = int(pil_img.size[0] * img_ratio)
    hsize = int(pil_img.size[1] * img_ratio)
    pil_img = pil_img.resize((wsize, hsize), Image.ANTIALIAS)
    # convert to an image Tkinter can use and keep it
    url_imgs['list_img_content'][index] = ImageTk.PhotoImage(pil_img)
    return index


async def procesar_url():
    """ app.clear_gui: permite ejecutar con varias URLs sin tener que cerrar y abrir la aplicacion  """
    app.clear_gui()
    """ loading list of images from page asyncly  """
    await open_aio_session()
    num_imgs = await load_page()
    if num_imgs <= 0:
        await close_aio_session()
        return
    """ Creating and starting num_imgs tasks for loading images asyncly and concurrently  """
    results = []
    pending = [load_one_image(i) for i in range(num_imgs)]
    """ notifying main_window_observer when each task is done (img loaded) """
    while pending:
        completed, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
        rx.from_(completed).subscribe(MainWindowObserver())
        results += [task.result() for task in completed]
    await close_aio_session()
    """ A veces hay errores en las img_src de la web. Chequeamos las imagenes que pudieron ser descargadas.
        Si load_one_image ha devuelto un result < 0 es que esa imagen no se pudo cargar. """
    print(f'>>> (procesar_url) results = {results}')
    num_imgs_ok = len(list(filter(lambda x: x >= 0, results)))
    if num_imgs > num_imgs_ok:
        print(f'Imagenes descargadas: {num_imgs_ok} de {num_imgs}.')
    return


def _asyncio_thread(async_loop):
    async_loop.run_until_complete(procesar_url())


def do_tasks(async_loop):
    """ Button-Event-Handler starting the asyncio part. """
    threading.Thread(target=_asyncio_thread, args=(async_loop,)).start()


if __name__ == '__main__':
    async_loop = asyncio.get_event_loop()
    app = App(async_loop)
    app.mainloop()


