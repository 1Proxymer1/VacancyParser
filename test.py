import requests as r
from bs4 import BeautifulSoup
import json

# headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.72 Safari/537.36'}
# URL = "https://hh.ru/search/vacancy"
# params = {
#             "L_save_area": "true",
#             "text": "программист",
#             "excluded_text": ["разработчик", "джуниор"],
#             "area": "1438",
#             "salary": 50000,
#             "currency_code": "RUR",
#             "education": ["special_secondary", "higher"],  # тут надо сделать правильный опыт работы для
#             "experience": "between1And3",  # тут сделать правильный опыт работы
#             "employment": ["full", "project"],  # тут сделать правильную занятость
#             "schedule": ["flexible", "remote"],  # тут сделать правильный график
#             "order_by": "relevance",
#             "search_period": "0",
#             "items_oxn_page": "50",
#             "hhtmFrom": "vacancy_search_filter"
#         }
#
#
# # page = r.get(URL, params=params, headers=headers)
# # print(page.url)
# # print(page.status_code)
#
# def getAreas():
#     req = r.get('https://api.hh.ru/areas')
#     data = req.content.decode()
#     req.close()
#     jsObj = json.loads(data)
#     areas = []
#     for k in jsObj:
#         for i in range(len(k['areas'])):
#             if len(k['areas'][i]['areas']) != 0:  # Если у зоны есть внутренние зоны
#                 for j in range(len(k['areas'][i]['areas'])):
#                     areas.append([k['id'],
#                                   k['name'],
#                                   k['areas'][i]['areas'][j]['id'],
#                                   k['areas'][i]['areas'][j]['name']])
#             else:  # Если у зоны нет внутренних зон
#                 areas.append([k['id'],
#                               k['name'],
#                               k['areas'][i]['id'],
#                               k['areas'][i]['name']])
#     return areas
#
# def checkArea(areas, custom_area):
#     id = None
#     for area in areas:
#         if custom_area in area[-1]:
#             id = area[2]
#             break
#     return id
#
# areas = getAreas()
# print(areas)
# print(checkArea(areas, "Россия"))