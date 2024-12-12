import requests as r
from bs4 import BeautifulSoup
import threading as mp
from queue import Queue
from art import tprint
from abc import ABC, abstractmethod
import json
import os
from sys import exit
from transliterate import translit


# Очистить консоль
def clear():
    os.system('cls' if os.name=='nt' else 'clear')

# Объект вакансии для удобного хранения данных по ней
class Vacancy:
    def __init__(self, name, url, salary):
        self.name = name
        self.url = url
        self.salary = salary

# Класс для хранения информации о фильтрах для поиска вакансий
class Filter:
    def __init__(self, key_words="", area=1, area_name="krasnodar", salary=1000, ban_words="", education="", experience_of_work="", employment="", schedule=""):
        self.key_words = key_words
        self.area = area
        self.area_name = area_name
        self.salary = salary
        self.ban_words = ban_words
        self.education = education
        self.experience = experience_of_work
        self.employment = employment
        self.schedule = schedule

    def print_filter(self):
        print("Поиск по фразе:", self.key_words)
        print("Поиск в зоне с ID:", self.area)
        print("Поиск по зарплате:", self.salary)
        print("В поиске не будет слов:", *self.ban_words)
        print("Поиск по уровню образование:", *self.education)
        print("Поиск по опыту работы:", self.experience)
        print("Поиск по занятости:", *self.employment)
        print("Поиск по графику работы:", *self.schedule)

    def copy(self):
        return Filter(self.key_words, self.area, self.area_name, self.salary, self.ban_words, self.education, self.experience, self.employment, self.schedule)

# Общий шаблон о том, как устроен класс парсеров сайтов
class Parser(ABC):
    education = {
        0: "Не требуется или не указано",
        1: "Среднее профессиональное",
        2: "Высшее"
    }
    experience = {
        0: "Не имеет значения",
        1: "Нет опыта",
        2: "От 1 года до 3 лет",
        3: "От 3 до 6 лет",
        4: "Более 6 лет"
    }
    employment = {
        0: "Полная занятость",
        1: "Частичная занятость",
        2: "Проектная работа/разовое задание",
        3: "Волонтерство",
        4: "Стажировка"
    }
    schedule = {
        0: "Полный день",
        1: "Сменный график",
        2: "Гибкий график",
        3: "Удаленная работа",
        4: "Вахтовый метод"
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.72 Safari/537.36'
    }

    @abstractmethod
    def __init__(self, filter, vacancies, lock):
        pass

    @abstractmethod
    def parse(self):
        pass

# Парсер хед хантера
class HeadHunterParser(Parser):
    __education = {
        "Не требуется или не указано": "not_required_or_not_specified",
        "Среднее профессиональное": "special_secondary",
        "Высшее": "higher"
    }
    __experience = {
        "Не имеет значения": "noExperience",
        "Нет опыта": "noExperience",
        "От 1 года до 3 лет": "between1And3",
        "От 3 до 6 лет": "between3And6",
        "Более 6 лет": "moreThan6"
    }
    __employment = {
        "Полная занятость": "full",
        "Частичная занятость": "part",
        "Проектная работа/разовое задание": "project",
        "Волонтерство": "volunteer",
        "Стажировка": "probation"
    }
    __schedule = {
        "Полный день": "fullDay",
        "Сменный график": "shift",
        "Гибкий график": "flexible",
        "Удаленная работа": "remote",
        "Вахтовый метод": "fly_in_fly_out"
    }

    # __headers = {
    #     'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.72 Safari/537.36'
    # }

    __headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
    }

    def __init__(self, filter, vacancies, lock: mp.Lock, request_lock: mp.Lock):
        self.vacancies = vacancies
        self.lock = lock
        self.request_lock = request_lock
        self.filter = filter.copy()
        self.url = "https://hh.ru/search/vacancy"
        # self.params = {
        #     "L_save_area": "true",
        #     "text": self.filter.key_words,
        #     "excluded_text": self.filter.ban_words,
        #     "area": self.filter.area,
        #     "salary": self.filter.salary,
        #     "currency_code": "RUR",
        #     "education": [HeadHunterParser.__education[filter_education] for filter_education in self.filter.education],
        #     "experience": HeadHunterParser.__experience[self.filter.experience],
        #     "employment": [HeadHunterParser.__employment[filter_employment] for filter_employment in
        #                    self.filter.employment],
        #     "schedule": [HeadHunterParser.__schedule[filter_schedule] for filter_schedule in self.filter.schedule],
        #     "order_by": "relevance",
        #     "search_period": "0",
        #     "items_oxn_page": "100",
        #     "page": 0,
        #     "hhtmFrom": "vacancy_search_filter"
        # }
        self.params = {
            "page": 0,
            "per_page": 100,
            "text": self.filter.key_words,
            "area": self.filter.area,
            "salary": self.filter.salary
        }
        if self.filter.experience:
            self.params["experience"] = HeadHunterParser.__experience[self.filter.experience]
        if self.filter.employment:
            self.params["employment"] = [HeadHunterParser.__employment[filter_employment] for filter_employment in
                            self.filter.employment]
        if self.filter.schedule:
            self.params["schedule"] = [HeadHunterParser.__schedule[filter_schedule] for filter_schedule in self.filter.schedule]
        # self.page = r.get(self.url, params=self.params, headers=HeadHunterParser.__headers)

    def get_page(self):
        self.request_lock.acquire()
        page = r.get("https://api.hh.ru/vacancies", params=self.params, headers=HeadHunterParser.__headers)
        self.request_lock.release()
        data = json.loads(page.content.decode())
        page.close()
        return data

    def parse(self):
        while True:
            data = self.get_page()
            # data["items"].keys() = name, area, salary, url, schedule, experience, employment
            for vacancy in data["items"]:
                name = vacancy["name"]
                try:
                    salary = vacancy["salary"]["from"]
                except:
                    salary = ""
                url = vacancy["alternate_url"]
                self.lock.acquire()
                self.vacancies.put(Vacancy(name, url, salary))
                self.lock.release()
            if data["page"] < 15:
                self.params["page"] += 1
            else:
                break

class HabrParser(Parser):
    __education = None # в юле нет фильтрации по уровню образования
    __experience = None
    __employment = { # attributes[vacancy_employment_type][0]
        "Полная занятость": "full_time",
        "Частичная занятость": "part_time"
    }
    __schedule = None

    # __headers = {
    #     'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.72 Safari/537.36'
    # }

    __headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
    }

    def __init__(self, filter: Filter, vacancies, lock, request_lock):
        self.vacancies = vacancies
        self.lock = lock
        self.request_lock = request_lock
        self.filter = filter.copy()
        self.url = "https://career.habr.com/vacancies"
        # self.params = {
        #     "L_save_area": "true",
        #     "text": self.filter.key_words,
        #     "excluded_text": self.filter.ban_words,
        #     "area": self.filter.area,
        #     "salary": self.filter.salary,
        #     "currency_code": "RUR",
        #     "education": [HeadHunterParser.__education[filter_education] for filter_education in self.filter.education],
        #     "experience": HeadHunterParser.__experience[self.filter.experience],
        #     "employment": [HeadHunterParser.__employment[filter_employment] for filter_employment in
        #                    self.filter.employment],
        #     "schedule": [HeadHunterParser.__schedule[filter_schedule] for filter_schedule in self.filter.schedule],
        #     "order_by": "relevance",
        #     "search_period": "0",
        #     "items_oxn_page": "100",
        #     "page": 0,
        #     "hhtmFrom": "vacancy_search_filter"
        # }
        self.params = dict()
        if self.filter.employment in HabrParser.__employment:
            self.params["employment_type"] = HabrParser.__employment[filter.employment[0]]
        self.params["page"] = 1
        self.params["q"] = self.filter.key_words
        self.params["salary"] = self.filter.salary
        self.params["type"] = "all"
        # self.page = r.get(self.url, params=self.params, headers=HeadHunterParser.__headers)

    def parse(self):
        while True:
            self.request_lock.acquire()
            page = r.get(self.url, params=self.params, headers=HabrParser.__headers)
            self.request_lock.release()
            bs = BeautifulSoup(page.text, "html.parser")
            page.close()

            all_titles = bs.findAll(class_="vacancy-card__title")
            all_links = bs.findAll(class_="vacancy-card__icon-link")
            if len(all_titles) == 0:
                break

            for i in range(len(all_titles)):
                url = "https://career.habr.com" + all_links[i]['href']
                name = all_titles[i].text
                with self.lock:
                    self.vacancies.put(Vacancy(name, url, None)) # salary на хабре указан криво, спарсить его не представляется удобным вариантом
            self.params["page"] += 1
        return

# начать парсинг на всех сайтах учитывая filter. Тут запускаются процессы
def startParse(filter):
    clear()
    print_menu_text()

    print("Начинаем поиск!")
    vacancies = Queue()
    lock = mp.Lock()
    request_lock = mp.Lock()

    headhunter = HeadHunterParser(filter, vacancies, lock, request_lock)
    habr = HabrParser(filter, vacancies, lock, request_lock)

    hhp = mp.Thread(target=headhunter.parse)
    h = mp.Thread(target=habr.parse)

    hhp.start()
    h.start()

    h.join()
    hhp.join()

    print("Поиск завершён!")
    save_vacancies(vacancies)
    print("Все найденные вакансии находятся в файле vacancies.txt! (нажмите enter для продолжения)")
    input()

# Сохранить все найденные вакансии
def save_vacancies(vacancies):
    with open("vacancies.txt", mode='w', encoding='utf-8') as f:
        while not vacancies.empty():
            vacancy = vacancies.get()
            result = f"{vacancy.name}"
            if vacancy.salary: result += f" ({vacancy.salary})"
            result += f"\n{vacancy.url}\n\n"
            f.write(result)

# Вводим и проверяем город, который ввёл пользователь для парсинга вакансий в нём
def get_city(areas, filter):
    while True:
        clear()
        print_menu_text()
        area = input("Введите город: ").capitalize()
        id = getId(areas, area)
        if id:
            filter.area = id
            filter.area_name = translit(area.lower(), 'ru', reversed=True)
            return
        print("Введите существующий город!\n")

# получает все доступные области для парсинга вакансий (с их ID и названиями)
def getAreas():
    req = r.get('https://api.hh.ru/areas')
    data = req.content.decode()
    req.close()
    jsObj = json.loads(data)
    areas = []
    for k in jsObj:
        for i in range(len(k['areas'])):
            if len(k['areas'][i]['areas']) != 0:  # Если у зоны есть внутренние зоны
                for j in range(len(k['areas'][i]['areas'])):
                    areas.append([k['id'],
                                  k['name'],
                                  k['areas'][i]['areas'][j]['id'],
                                  k['areas'][i]['areas'][j]['name']])
            else:  # Если у зоны нет внутренних зон
                areas.append([k['id'],
                              k['name'],
                              k['areas'][i]['id'],
                              k['areas'][i]['name']])
    return areas

# получить id конкретного города custom_area из областей areas
def getId(areas, custom_area):
    id = None
    for area in areas: # area = [id of parent area, parent area, id of area, area]
        if custom_area in area[-1]:
            id = area[2]
            break
    return id

# запрашивает у пользователя ключевые слова для поиска вакансий
def get_key_words():
    clear()
    print_menu_text()
    key_words = input("Введите ключевые слова/фразы: ").lower()
    return key_words

# запрашивает исключающие слова, которых не будет в вакансиях при парсинге
def get_ban_words():
    clear()
    print_menu_text()
    ban_words = input("Введите исключающие слова/фразы через запятую: ").split(",")
    return ban_words

# указать ожидаемую зарплату (и выше) при парсинге
def get_salary():
    while True:
        clear()
        print_menu_text()
        try:
            salary = int(input("Введите зарплату: "))
            return salary
        except ValueError:
            print("Принимается только число!\n")

# запрашиваем опыт работы пользователя
def get_experience():
    while True:
        clear()
        print_menu_text()
        for key in Parser.experience:
            print(key, '-', Parser.experience[key])
        try:
            experience_of_work = Parser.experience[int(input("Введите опыт работы: "))]
            return experience_of_work
        except ValueError:
            print("Введите номер опыта работы!\n")
        except KeyError:
            print("Выберите номер из вариантов выше!\n")

# получить тип занятости для фильтрации вакансий
def get_employment():
    while True: # обработка исключений
        clear()
        print_menu_text()
        for key in Parser.employment:
            print(key, '-', Parser.employment[key])
        result = []
        employment_of_work = list(map(int, set(input("Выберите тип занятости (если несколько, укажите варианты без разделителя): "))))
        if len(employment_of_work) > len(Parser.employment):
            print("Не повторяйте значения!\n")
            input()
            continue
        for employment in employment_of_work:
            try:
                result.append(Parser.employment[employment])
            except KeyError:
                print("Укажите существующие варианты!\n")
                input()
                result = []
                continue
        return result

# получить образование пользователя для фильтрации вакансий
def get_education():
    while True:  # обработка исключений
        clear()
        print_menu_text()
        for key in Parser.education:
            print(key, '-', Parser.education[key])
        result = []
        education_of_work = list(
            map(int, set(input("Выберите тип образования (если несколько, укажите варианты без разделителя): "))))
        if len(education_of_work) > len(Parser.education):
            print("Не повторяйте значения!\n")
            input()
            continue
        for education in education_of_work:
            try:
                result.append(Parser.education[education])
            except KeyError:
                print("Укажите существующие варианты!\n")
                input()
                result = []
                continue
        return result

# получить график работы от пользователя для фильтрации вакансий
def get_schedule():
    while True:  # обработка исключений
        clear()
        print_menu_text()
        for key in Parser.schedule:
            print(key, '-', Parser.schedule[key])
        result = []
        schedule_of_work = list(
            map(int, set(input("Выберите график работы (если несколько, укажите варианты без разделителя): "))))
        if len(schedule_of_work) > len(Parser.schedule):
            print("Не повторяйте значения!\n")
            input()
            continue
        for schedule in schedule_of_work:
            try:
                result.append(Parser.schedule[schedule])
            except KeyError:
                print("Укажите существующие варианты!\n")
                input()
                result = []
                continue
        return result

# вывести название проекта и отступ (красиво типо)
def print_menu_text():
    tprint("Vacancy Parser", font='big')
    tprint("="*11, font='big')

def choose_mode(mode, filter, areas):
    match mode:
        case 0: startParse(filter)
        case 1: filter.key_words = get_key_words()
        case 2: filter.ban_words = get_ban_words()
        case 3: get_city(areas, filter)
        case 4: filter.salary = get_salary()
        case 5: filter.experience = get_experience()
        case 6: filter.education = get_education()
        case 7: filter.schedule = get_schedule()
        case 8: filter.employment = get_employment()
        # доделать остальные случаи

# главное меню программы, отсюда всё запускается
def main():
    areas = getAreas()
    filter = Filter()
    while True:
        print("0 - Начать поиск")
        print("1 - Указать ключевые слова поиска")
        print("2 - Указать исключающие слова поиска")
        print("3 - Указать город")
        print("4 - Указать зарплату")
        print("5 - Указать опыт")
        print("6 - Указать образование")
        print("7 - Указать график работы")
        print("8 - Указать занятость работы")
        print("9 - Выйти")
        try:
            mode = int(input("Введите число, означающее ваш выбор: "))
            if mode == 9: break
            choose_mode(mode, filter, areas) # else
        except ValueError:
            print("Введите число из вариантов выше!\n")
            input()
            clear()

# адекватная работа мультипроцессорности
if __name__ == "__main__":
    print_menu_text()
    main()