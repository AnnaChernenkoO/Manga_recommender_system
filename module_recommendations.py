#библиотека для получения чистоты встречающих слов в тексте и очистки текста от слов которые не несут смысловой нагрузки
from rake_nltk import Rake
import nltk
#библиотеки для обработки данных файла CSV
import pandas as pd
import numpy as np
#библиотеки которые и создают матрицу схожести той или иной манги
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer
#библиотека для загрузки слов которые не имеют смысловой нагрузки, чтобы их найти потом в тексте
from nltk.corpus import stopwords
#библиотека для правильного прописания пути к файлу CSV
import pathlib
#подключаем библиотеку для многопоточности и синхронизации потоков
from threading import Lock, Thread

#переменная чтобы синхронизировать поток и нормально вывести рекомендации
lock = Lock()

#при проблеме раскоментировать следующую строку и она загрузить слова без смыцсловой нагрузки
#nltk.download('stopwords')

#создаем переменную в которой далее будут находится все данные из файла manga.csv
df = pd.DataFrame()
#название файла с данными манги, а также путь к нему(находится в папке программы)
FILENAME = pathlib.Path(pathlib.Path.cwd(),"manga_sev.csv") 

#функция handler_recom видо изменяет данные из файла manga.csv и делает их более пригодными для обработки
#и в конце строится матрица схожести манг
def handler_recom():
    #указываем что будет использоваться переменная которая была создана ранее
    global df

    global FILENAME
    #читаем данные из файла manga.csv в переменную df
    df = pd.read_csv(FILENAME,encoding='utf-8')
    #создаем переменую которая будет хранить коллекцию элементов
    ss_Key_words =[]
    #помимо существующих столбцов название, описание и др. создаем столбец Key_words
    #в нем будут храниться ключевые слова из столбца описания
    df['Key_words'] = ''
    #создаем переменную которая будет хранить ключевые слова, но при этом функция stopwords.words удаляет
    #все слова из базы данных которые не имеют смысловой нагрузки именно в русском языке
    r = Rake(stopwords.words('russian'))
    #цикл проходит по всем описаниям манг и оставляет ключевые слова, которые записываем в столбец Key_words
    for index, row in df.iterrows():
        r.extract_keywords_from_text(row['Story'])
        key_words_dict_scores = r.get_word_degrees()
        row['Key_words'] = list(key_words_dict_scores.keys())
        #добавляем обработаные данные в коллекцию
        ss_Key_words.append(row)
        
    #созданую колекцию добавляем в наши данные
    df= pd.DataFrame(ss_Key_words)

    #создаем переменую которая будет хранить коллекцию элементов
    ss_Genre =[]

    #немного редактируем столбец с жанрами
    df['Genre'] = df['Genre'].map(lambda x: str(x).split(' '))
    #цикл проходит по всем жанрам каждой манги и переводит все жанры в нижний регистр
    for index, row in df.iterrows():
        row['Genre'] = [x.lower().replace(' ','') for x in row['Genre']]
        #добавляем изминения в колекцию
        ss_Genre.append(row)

    #созданую колекцию жанров добавляем в наши данные
    df= pd.DataFrame(ss_Genre)

    #создаем переменую которая будет хранить коллекцию элементов
    ss_Bag_of_words =[]
    #помимо существующих столбцов название, описание и др. создаем столбец Bag_of_words
    #в нем будут храниться данные из столбца Key_words и Genre. Далее этот столбец и будет использоваться
    #чтобы определить схожесть манг
    df['Bag_of_words'] = ''
    #создаем колекцию строк которые соответствуют нашим столбцам
    columns = ['Genre', 'Key_words']
    #в цикле у каждой манги объединяем столбец 'Genre', 'Key_words' в столбце Bag_of_words
    for index, row in df.iterrows():
        words = ''
        for col in columns:
            words += ' '.join(row[col]) + ' '
        row['Bag_of_words'] = words
        #временно все данные записываем в колекцию, чтобы потом их уже добавить к основным данным
        ss_Bag_of_words.append(row)
    
    #созданую колекцию добавляем в наши данные
    df= pd.DataFrame(ss_Bag_of_words)

    #удаляем лишние пробелы в столбце Bag_of_words
    df['Bag_of_words'] = df['Bag_of_words'].str.strip().str.replace('   ', ' ').str.replace('  ', ' ')
    
    #оставляем в переменной df только нужные нам столбцы
    df = df[['TitleRus','TitleEng','Bag_of_words','Rating']]

    #следующие 3 строчки создают матрицу схожести для будущей рекомендации манги
    count = CountVectorizer()
    count_matrix = count.fit_transform(df['Bag_of_words'])
    cosine_sim = cosine_similarity(count_matrix, count_matrix)
    
    #возвращаем матрицу схожести из функции
    return cosine_sim

#функция по индексу манги определяет ее название, нужна для того чтобы в матрице определить названия манг
#иначе если вернем индекс пользователь не поймет что это за манга
def get_title_from_index(index):
	return df[df.index == index].TitleRus.values[0]

#функция по индексу манги определяет ее рейтинг
def get_rating_from_index(index):
	return df[df.index == index].Rating.values[0]

#по названию получаем индекс, чтобы узнать под каким индексом в матрице манга название которой мы ввели
def get_index_from_title(title):
    return df[df.TitleRus == title].index.values[0]

#эта функция вызывается в файле gui.py, принимает название манги и используя выше определеные функции 
#предлагает 10 схожих по описанию и жанру манги 
def my_recom(title):
    #получаем матрицу схожести манг используя выше определеную функцию 
    cosine_sim = handler_recom()
  
    #создаем переменую которая хранит коллекцию рекомендованой манги
    recommended_manga = []

    #конструкция try except для отлова ошибок, если ввели мангу которая не существует в базе данных случится ошибка
    #и вызовится конструкция except которая оповестит, что фильм не найден
    try:
        #получаем индекс нашей манги
       movie_index = get_index_from_title(title)
    except:
        print("Манга не найдена")
        return
    
    #находим в матрице нашу мангу
    similar_movies =  list(enumerate(cosine_sim[movie_index]))

    #сортируем мангу по схожести с нашей
    sorted_similar_movies = sorted(similar_movies,key=lambda x:x[1],reverse=True)
    #переменная для нумерации манги которую мы предлагаем
    i = 0

    #синхранизируем поток для вывода рекомендаций
    lock.acquire()
    #цикл выводит в приложение похожую мангу
    for element in sorted_similar_movies:
        #сначала в списке будет идти наша манга которую мы ввели 
        if i == 0:
            #ее выделяем, чтобы не спутать с рекомендациями
            print('---',get_title_from_index(element[0]),'---')
        else:
            #выводим рекомендации
            print(f'{i}. ',get_title_from_index(element[0]),'[',get_rating_from_index(element[0]),']')
        #увеличиваем переменую на 1
        i+=1
        #после 10 итерации выходим из цикла
        if i > 10:
            break
    #прекращаем синхронизацию
    lock.release()

#функция для изминения файла с данными, используется в файле gui.py
def filename_r(name):
    global FILENAME
    FILENAME = name