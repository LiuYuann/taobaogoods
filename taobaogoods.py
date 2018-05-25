"""大概用时 166.28715705871582s"""
from selenium import webdriver
from pyquery import PyQuery as pq
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from time import time
import re

CLIENT = MongoClient()
DB = CLIENT['taobao']
COLLECTION = DB['taobao']
KEY = '书'

chrome_options = Options()
chrome_options.add_argument('--headless')
browser = webdriver.Chrome(chrome_options=chrome_options)
browser.get('https://www.taobao.com')
wait = WebDriverWait(browser, 10)


def enterANDfindpages(key):
    try:
        pages = 0
        global brower
        global wait
        input = wait.until(EC.presence_of_element_located((By.ID, 'q')))
        input.send_keys(key)
        button = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'btn-search')))
        button.click()
        doc = pq(browser.page_source)
        pages0 = doc('.total').text()
        try:
            pages = re.search(r'\d+', pages0).group(0)
        except AttributeError:
            print('关键词未找到')
        return int(pages)
    except TimeoutException:
        enterANDfindpages(key)


def pagedetail(page):
    try:
        input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.form > input')))
        input.clear()
        input.send_keys(page)
        button = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.form > span.btn.J_Submit')))
        button.click()
        pp = browser.find_element_by_css_selector('#mainsrp-pager li.item.active > span').text
        wait.until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR, '#mainsrp-pager li.item.active > span'), str(page)))
        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-itemlist  .items .item.J_MouserOnverReq')))
        return browser.page_source
    except Exception as ex:
        # print('ccl', ex.reason())
        pagedetail(page)


def get_products(html):
    # print(html)
    doc = pq(html)
    doc('span').remove()
    items = doc('#mainsrp-itemlist  .items .item.J_MouserOnverReq').items()
    for item in items:
        img_url = item.find('.pic .J_ItemPic.img').attr('src')
        price = item('.price').text().replace('\n', '').replace('¥', '')
        store = item.find('.ctx-box .row-3 .shopname').text()
        location = item.find('.ctx-box .row-3 .location').text()
        title = item.find('.ctx-box .row-2').text()
        data = {
            'img_url': img_url,
            'price': price,
            'store': store,
            'location': location,
            'title': title,
        }
        # print(data)
        yield (data)


def save_to_mongo(result):
    try:
        if COLLECTION.insert(result):
            print('Saved to Mongo')
    except DuplicateKeyError as e:
        print('Error', e.args)


def main():
    pages = enterANDfindpages(KEY)
    for page in range(1, pages + 1):
        print(page)
        for d in get_products(pagedetail(page)):
            save_to_mongo(d)



if __name__ == '__main__':
    ago = time()
    main()
    browser.close()
    print("用时", time() - ago)
