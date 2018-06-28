"""大概用时 210s"""
from selenium import webdriver
from pyquery import PyQuery as pq
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from time import time
import pymysql
import requests
import re
import random
import os

KEY = '智能机器人'
cid = 16
folder1 = 'smart device/'
folder2 = 'smart robot/'
db = pymysql.connect("localhost", "root", "", port=3306, db='myweb', charset='utf8')
cursor = db.cursor()
table = 'itcast_goods'

chrome_options = Options()
chrome_options.add_argument('--headless')
browser = webdriver.Chrome(chrome_options=chrome_options)
browser.get('https://www.taobao.com')
wait = WebDriverWait(browser, 10)


# browser = webdriver.Chrome()
# browser.get('https://www.taobao.com')
# wait = WebDriverWait(browser, 10)


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


def download_image(item):
    if not os.path.exists(item.get('gid')):
        os.mkdir(item.get('gid'))
    i = 0
    try:
        for url in item.get('imgurl'):
            response = requests.get(url)
            if response.status_code == 200:
                i = i + 1
                file_path = '{0}/{1}.{2}'.format(item.get('gid'), i, 'jpg')
                if not os.path.exists(file_path):
                    with open(file_path, 'wb')as f:
                        f.write(response.content)
                else:
                    print('Already downloaded!!!')
    except requests.ConnectionError:
        print("Downloading failed!!!")


def findimageAndscription(url):
    # print(url)                 #如果出错可以不注释这里，查看出错的具体网页
    html = requests.get(url)
    doc = pq(html.text)
    urls = []
    if not doc('#J_UlThumb').html():
        if len(browser.window_handles) == 1:
            browser.execute_script('window.open()')
        browser.switch_to_window(browser.window_handles[1])
        browser.get(url)
        doc = pq(browser.page_source)
        browser.switch_to_window(browser.window_handles[0])
    html = doc('#J_UlThumb > li').items()
    for i in html:
        if re.search('60q90', str(i('a img').attr('src'))):
            img_url = i('a img').attr('src').strip('//')
            img_url = 'http://' + re.sub('_\d+x\d.+jpg.*?$', '', img_url).strip('//')
        elif re.search('_\d+x\d', str(i('a img').attr('data-src'))):
            img_url = 'https:' + i('a img').attr('data-src')
            img_url = re.sub('_\d+x\d.+jpg.*?$', '', img_url)
        else:
            img_url = ''
        urls.append(img_url)
    description = doc('#J_AttrUL').text()
    if not description:
        description = doc('#attributes > ul').text()
    description = re.sub('\n', '++', description)
    if urls:
        # print(urls)
        data = []
        data.append(urls)
        data.append(description)
        return data
    else:
        return None


def get_products(html):
    doc = pq(html)
    doc('span').remove()
    items = doc('#mainsrp-itemlist  .items .item.J_MouserOnverReq').items()
    for item in items:
        price = item('.price').text().replace('\n', '').replace('¥', '')
        title = item.find('.ctx-box .row-2').text()
        title = re.sub('\\n|\s', "", title)
        url = 'https://' + item.find('.ctx-box .row-2 .J_ClickStat').attr('href').lstrip('https://').lstrip('//')
        if re.search('tmall', url) or (not re.search('simba', url)):
            gid = re.search('id=(\d+)', url).group(1)
            d = findimageAndscription(url)
            if d:
                data = {
                    'gid': gid,
                    'gname': title,
                    'price': price,
                    'thumb': folder1 + folder2 + gid,
                    'status': random.choice(['yes', 'no']),
                    'description': "".join(d.pop(1).split()),
                    'stock': random.randint(1, 100),
                    'cid': cid,
                    'sales': random.randint(1, 100),
                    'imgurl': d.pop(0)
                }
                # print(data)
                yield (data)
            else:
                yield None


def savetoMysql(data):
    keys = ','.join(data.keys())
    values = ','.join(['%s'] * len(data))
    sql2 = 'INSERT INTO {table}({keys}) values ({values})'.format(table=table, keys=keys, values=values)
    try:
        if cursor.execute(sql2, tuple(data.values())):
            print('success')
            db.commit()
    except Exception as e:
        print('erro', repr(e))
        db.rollback()


def save(data):
    download_image(data)
    data.pop('imgurl')
    # print(data)
    savetoMysql(data)
    # print(data)


def main():
    pages = enterANDfindpages(KEY)
    for page in range(1, 2):
        print(page)
        for d in get_products(pagedetail(page)):
            save(d)


if __name__ == '__main__':
    if not os.path.exists(folder2):
        os.mkdir(folder2)
    os.chdir(folder2)
    ago = time()
    main()
    browser.close()
    print("用时", time() - ago)
