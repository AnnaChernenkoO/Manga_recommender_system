#подключаем наш файл для парсинга и выгрузки в CSV файл
import module_pars as mp
#библиотека для создания интерфейса
import PySimpleGUI as sg
#библиотека для работы с файлами
import os
#библиотека для правильного прописания пути к файлу CSV
import pathlib

import sched, time
#библиотека для создания потоков, чтобы наши функции выполнялись паралельно и не блочили интерфейс
from threading import Thread
#подключаем наш файл для вызова функций рекомендации
import module_recommendations as mr

#коллекция которая хранит номера страниц и передается в индикатор загрузки, при переходе на новую страницу 
#индикатор продвигается
mylist = []
#вызываем нашу функцию из файла module_pars для получения количества страниц
pages = mp.number_of_pages()
#записываем в коллекцию номер каждой страницы
for i in range(1, int(pages)):
    mylist.append(i)

#создаем интерфейс загрузки
progressbar = [
    [sg.ProgressBar(len(mylist), orientation='h', size=(51, 10), key='progressbar')]
]
#интерфейс окна куда будет выводиться рекомендации
outputwin = [
    [sg.Output(size=(92,15),key = 'output')]
]
#окно ввода названия
inputwin = [
    [sg.InputText(size=(94,))]
]

#весь интерфейс программы
layout = [
    [sg.Frame('Прогресс',layout= progressbar,background_color='#27D6DE')],
    [sg.Button('Загрузка данных',key = 'loading',button_color='#277BDE'),sg.Button('Прервать загрузку',key = 'stop',button_color='#277BDE'),sg.Button('Использовать стандартный файл данных',key = 'db',button_color='#277BDE')],
    [sg.Frame('Название манги', layout = inputwin,background_color='#27D6DE')],
    [sg.Button('Получить рекомендации',key = 'recom',button_color='#277BDE')],
    [sg.Frame('Рекомендации', layout = outputwin,background_color='#27D6DE')],
    [sg.Button('Очистить',key = 'clear',button_color='#277BDE')]
]

#переменая для оповещения о том, что выгрузка данных закончена
isp = False

#функция вызывается в файле module_pars и меняет значение переменной isp на False
def isp_fal():
    global isp
    isp = False

#создаем наше окно интерфейса 
window = sg.Window('Рекомендации манги', layout, background_color='#27D6DE')
#переменая для передачи ее в файл module_pars где она будет увеличивать значение загрузки
progress_bar = window['progressbar']


while True:
    event, values = window.read(timeout=10)

    #переменая потока для парсинга и выгрузки данных
    th1 = Thread(target=mp.pars_in_csv, args=(progress_bar,isp_fal, ))
    #переменая потока для рекомендации
    th2 = Thread(target=mr.my_recom, args=(values[0], ))
    #переменая потока для вызова функции остановки выгрузки данных
    th3 = Thread(target=mp.stop_pars)

    if event is None:
        break
    #при нажатие на кнопку загрузки данных сработает это условие
    elif event == 'loading':
        mr.filename_r(pathlib.Path(pathlib.Path.cwd(),"manga.csv"))
        #сигнализирует о запуске функции выгрузки данных
        isp = True
        #запускаем поток th1 который отвечает за парсинг
        th1.start()

    #это условие сработает если мы нажали 'Использовать стандартный файл данных'
    elif event == 'db':
        #это условие сработает если только выгрузка данных запущена 
        if isp:
            isp = False
            #запускаем функцию для остановки выгрузки данных
            th3.start()
        #заменяем выгруженый файл с данными заранее выгружеными данными
        mr.filename_r(pathlib.Path(pathlib.Path.cwd(),"manga_sev.csv"))

    #при нажатие на кнопку получить рекомендации сработает это условие 
    elif event == 'recom':
        #если будет производиться загрузка данных то отработает это условие
        if isp:
            #создаем всплывающее окно для придупреждения пользователя о том что идет загрузка данных
            #и функция рекомендации в этот момент не доступна
            window.FindElement('output').Update('')
            layout2 = [[sg.Text('Производиться загрузка данных!')],[sg.Button('Ok',key = 'ok',button_color='#277BDE')]]
            pop_window = sg.Window('Сообщение', layout2, background_color='#27D6DE')

            while True:
                event2, values2 = pop_window.read(timeout=10)
                if event2 is None:
                    break
                elif event2 == 'ok':
                    break
            #закрываем всплывающее окно
            pop_window.close()
        #если выгрузка данных не запущена то отработает это условие
        else:
            
            try:
                #чистим окно вывода
                window.FindElement('output').Update('')
                #запускаем поток th2 который отвечает за рекомендации
                th2.start()
            except:
                window.FindElement('output').Update('')
                print("Манга не найдена")
    #если нажали на кнопку очистить сработает это условие
    elif event == 'clear':
        #чистим окно вывода
        window.FindElement('output').Update('')
    #если нажали прервать загрузку данных сработает это условие
    elif event == 'stop':
        #это условие сработает если только выгрузка данных запущена 
        if isp:
            isp = False
            #запускаем функцию для остановки выгрузки данных
            th3.start()
#закрываем окно при выходе из приложения
window.close()