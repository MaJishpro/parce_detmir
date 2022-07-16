import re

import requests
from bs4 import BeautifulSoup

import asyncio
from pyppeteer import launch, launcher
import pandas


def parse_price_ozon(url_page: str):
    """
     Парсер HTML страниц всех товаров из категории в детском мире
      :param url : ССылка на страницу категории товара
    """
    urls = [url_page + '/page/1']
    url_items = []
    id_list = []
    title_list = []
    price_list = []
    promo_price_list = []
    city_list = []
    list_page = 2
    for url in urls:
        try:
            try:
                loop = asyncio.get_event_loop()  # gets previously set event loop, if possible
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            html = loop.run_until_complete(main(url))  # работа через pyppeteer
            soup = BeautifulSoup(html, 'html.parser')
            div_cards = soup.find('div', {'class': 'xm'}).find_all('div', {'class': re.compile("^vW wa xn")})
            if len(div_cards) > 0:
                urls.append(f'{url_page}/page/' + str(list_page))
                list_page += 1
            for card in div_cards:
                price = card.find('p', {'class': 'RA'})
                price = price.text.replace('\u2009', ' ').replace('\xa0', " ") if price else card.find('div', {
                    'class': 't_6'}).text
                promo = card.find('span', {'class': 'RC'})
                url_item = card.find('a', {'class': re.compile("^Rl RM")}).get('href')
                id_list.append(url_item.split('id/')[-1].replace('/', ''))
                url_items.append(url_item)
                title_list.append(card.find('p', {'class': 'Rp'}).text)
                price_list.append(price if promo is None else promo.text.replace('\u2009', ' ').replace('\xa0', " "))
                city_list.append(soup.find('span', {'class': 'lV'}).text)
                promo_price_list.append(price if promo else "Нет")
        except AttributeError:
            break
    d = pandas.DataFrame({'id': id_list, 'title': title_list, 'price': price_list, 'promo_price': promo_price_list,
                          'city': city_list, "url": url_items})
    d.to_csv('out.csv', encoding='utf-16 ')
    return d


async def main(url):
    # Параметры запуска браузера
    start_parm = {
        # Закройте безголовый браузер
        "headless": True,
        "args": [
            '--disable-infobars',  # Закройте окно подсказки автоматизации
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36',
            # UA
            '--no-sandbox',  # Отключить режим песочницы
            '- proxy-server = http: // localhost: 1080'  # Прокси
        ],
    }
    # объект браузера. Можно передать параметры словаря или оставить пустым
    browser = await launch(**start_parm, handleSIGINT=False, handleSIGTERM=False, handleSIGHUP=False)
    # Создать объект страницы, операции страницы выполняются над объектом
    page = await browser.newPage()
    opt = {"timeout": 0, 'waitUntil': 'networkidle2'}
    await page.goto(url, opt)  # Переход на страницу
    page_text = await page.content()  # Содержание страницы
    await page.close()
    await browser.close()
    # asyncio.get_event_loop().run_until_complete(main())
    return page_text


if __name__ == '__main__':
    res = parse_price_ozon('https://www.detmir.ru/catalog/index/name/lego')
    print(res)
