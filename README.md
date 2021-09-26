# ReactiveX, Tkinter y AsyncIO

Aplicación combinando tres herramientas: ReactiveX (rxpy), Tkinter y AsyncIO.
La aplicación consistirá en una ventana gráfica en la que el usuario puede introducir
una URL. Al introducirla y pulsar el botón de buscar, descargaremos la página web que se
encuentre en la URL introducida, y de ella, procesaremos todas las imágenes, descargando
sus datos a memoria (no en disco). La descarga de imágenes debe realizarse de forma
concurrente con asyncio utilizando la librería aiohttp, y cada vez que descarguemos una,
notificaremos a la ventana principal de la aplicación por medio de un Observable-
Observer (rxpy).
La ventana principal mostrará tres elementos más: una lista (Listbox), una barra de
progreso (Progressbar) y una imagen (PIL.ImageTk.PhotoImage)
