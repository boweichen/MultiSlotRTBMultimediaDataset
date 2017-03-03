# -*- coding: utf-8 -*-

import os
import sys
import json
import time
import nltk
import urllib
import re
import shutil
import copy
import urllib
import urllib2
import shutil
from datetime import datetime
from PIL import Image
from bs4 import BeautifulSoup
##import pyscreenshot as ImageGrab
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

def RestartBrowser():
    browser = None

    # print 'browser restarted!'
    chromedriver = '/usr/local/bin/chromedriver'
    os.environ['webdriver.chrime.driver'] = chromedriver
    options = webdriver.ChromeOptions()
    # options.add_argument('--disable-web-security')
    options.add_argument('--lang=es')
    options.add_argument('--start-maximized')
    options.add_argument('--disable-extensions')
    options.add_argument('-incognito')              ### privacy mode, which disable browsing history and web cache
                                                    ### and also disable the storage data in cookies and flash cookie
    options.add_argument('--disable-popup-blocking')
    # options.add_argument('--test-type')             #### remove the  warning of '--ignore-certificate-errors'
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--dns-prefetch-disable')
    browser = webdriver.Chrome(chromedriver, chrome_options=options)
    browser.set_page_load_timeout(5)
    # browser.get('http://www.msn.com/en-sg/')
    time.sleep(2)
    return browser


def removeNonAlphNumber(s):
    return re.sub('[^0-9a-zA-Z]+', ' ', s)

def remove_html_tags(data):
    p = re.compile(r'<.*?>')
    return p.sub('\n', data)

def remove_img_tags(data):
    p = re.compile(r'<img.*?/>')
    return p.sub('\n', data)

def load_current_webpage_ad_id_from_file():
    current_webpage_id = 2000000
    current_ad_id = 2000000
    file_path = './webpage_ad_id.txt'
    if os.path.isfile(file_path):
        handle = open(file_path, 'r')
        for line in handle:
            line = line.strip('\n').split('\t')
            line = [int(w) for w in line]
            current_webpage_id = line[0]
            current_ad_id = line[1]
        handle.close()
    else:
        pass
    return current_webpage_id, current_ad_id

def prepare_dst_folder(current_folder):
    if os.path.isdir(current_folder):
        print 'Directory already exist...'
        shutil.rmtree(current_folder)
    os.mkdir(current_folder)
    os.mkdir(current_folder + '/ad_image/')
    os.mkdir(current_folder + '/webpage_image/')

def load_webpage_urls(file_path):
    webpage_urls = []
    if os.path.isfile(file_path):
        handle = open(file_path, 'r')
        for line in handle:
            line = line.strip('\n')
            webpage_urls.append(line)
        handle.close()
        return webpage_urls
    else:
        return webpage_urls


def save_collected_webpage_urls(webpage_url):
    dst_file_path = './collected_webpage_urls.txt'
    handle = open(dst_file_path, 'a+')
    text = str(webpage_url) + '\n'
    handle.write(text)
    handle.close()

def find_new_urls_in_current_webpage(browser, to_be_collected_webpage_urls, current_collected_webpage_urls):
    try:
        elems = browser.find_elements_by_xpath("//a[@href]")
        for elem in elems:
            try:
                elem_url = elem.get_attribute("href")
                # print elem_url
                if elem_url.find('www.msn.com/en-sg') != -1:
                    if elem_url not in current_collected_webpage_urls:
                        to_be_collected_webpage_urls.append(elem_url)
            except:
                continue
    except:
        pass
    return to_be_collected_webpage_urls

def check_retangular_overlap(ad_div_location, collected_ad_div_locations):
    # http://stackoverflow.com/questions/9324339/how-much-do-two-rectangles-overlap
    for collected_ad_div_location in collected_ad_div_locations:
        xa1 = ad_div_location[0]
        ya1 = ad_div_location[1]
        xa2 = ad_div_location[2]
        ya2 = ad_div_location[3]
        xb1 = collected_ad_div_location[0]
        yb1 = collected_ad_div_location[1]
        xb2 = collected_ad_div_location[2]
        yb2 = collected_ad_div_location[3]
        SI = max(0, min(xa2, xb2) - max(xa1, xb1)) * max(0, min(ya2, yb2) - max(ya1, yb1))
        if SI * 1.0 / ((xa2-xa1) * (ya2 - ya1)) > 0.2:
            return False
    # if ad_div_location[3] > 1080:
    #     return False
    return True

def getAdImage(browser, dst_path, ad_area):
    webpage_size = browser.get_window_size()
    scroll_size = ad_area[3] - webpage_size['height'] + 96
    if scroll_size < 0:
        scroll_size = 0
    browser.execute_script("window.scrollTo(0, " + str(scroll_size) + ")")
    time.sleep(0.1)
    current_window_snapshot_img_path = './current_window_snapshot_img.png'
    browser.get_screenshot_as_file(current_window_snapshot_img_path)
    time.sleep(0.1)
    current_window_snapshot_img = Image.open(current_window_snapshot_img_path)
    after_scroll_area = [0, 0, 0, 0]
    after_scroll_area[0] = int(ad_area[0])
    after_scroll_area[1] = int(ad_area[1] - scroll_size)
    after_scroll_area[2] = int(ad_area[2])
    after_scroll_area[3] = int(ad_area[3] - scroll_size)
    # print after_scroll_area
    ad_image = current_window_snapshot_img.crop(after_scroll_area)
    ad_image.save(dst_path)

def collectAdInfoInLandingWebpage(soup, ad_url, current_ad_id, ad_area, AD_JSON_PATH):
    ad_location = ad_area
    ad_id = current_ad_id
    ad_url = ad_url
    ad_title = ''
    ad_description = ''
    ad_keywords = ''
    ad_text = ''

    # get title
    try:
        for group in soup.findAll('title'):
            ad_title += group.get_text()
    except:
        pass
    # get description
    try:
        for group in soup.findAll('meta', attrs={'name': "description"}):
            ad_description += group['content']
    except:
        pass
    # get keywords
    try:
        for group in soup.findAll('meta', attrs={'name':"keywords"}):
            ad_keywords += group['content']
    except:
        pass
    # get text
    try:
        for script in soup(["script", "style"]):
            script.extract()  # rip it out
        # get text
        text = remove_html_tags(soup.get_text())
        # break into lines and remove leading and trailing space on each
        lines = (line.strip() for line in text.splitlines())
        # break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # drop blank lines
        text = '\n'.join(chunk for chunk in chunks if chunk)
        # print 'text', ':\t', text
        ad_text = text.encode('utf-8')
    except:
        pass

    ad_info = {}
    ad_info['ad_location'] = ad_location
    ad_info['ad_id'] = ad_id
    ad_info['ad_url'] = ad_url
    ad_info['ad_title'] = ad_title
    ad_info['ad_description'] = ad_description
    ad_info['ad_keywords'] = ad_keywords
    ad_info['ad_text'] = ad_text
    ad_handle = open(AD_JSON_PATH, 'a+')
    json.dump(ad_info, ad_handle)
    ad_handle.write('\n')
    ad_handle.close()

def collectAdInfo(browser, webpage_url, current_webpage_id, current_ad_id, ad_div_area, dynamic_ad_div, AD_JSON_PATH, AD_IMAGE_FOLDER):
    # get ad image
    getAdImage(browser, AD_IMAGE_FOLDER + str(current_ad_id) + '.jpg', ad_div_area)
    # transfer to ad landing webpage and collect ad info
    dynamic_ad_div.click()
    time.sleep(2)
    windows_handles = browser.window_handles
    if browser.current_url == webpage_url and len(windows_handles) == 1:
        return False                    # the ad is unclickable
    current_window_handle = windows_handles[0]
    if len(windows_handles) == 2:
        current_window_handle = windows_handles[1]
    browser.switch_to_window(current_window_handle)
    content = browser.page_source
    soup = BeautifulSoup(content, 'html.parser')
    ad_url = browser.current_url
    collectAdInfoInLandingWebpage(soup, ad_url, current_ad_id, ad_div_area, AD_JSON_PATH)
    while len(browser.window_handles) != 1:
        current_windows_handles = browser.window_handles
        browser.switch_to_window(browser.window_handles[len(current_windows_handles) - 1])
        # browser.find_element_by_tag_name('body').send_keys(Keys.CONTROL + 'w')
        browser.close()
        time.sleep(0.1)
    browser.switch_to_window(browser.window_handles[0])
    return True


def CollectMSNAds(browser, current_webpage_id, current_ad_id, AD_JSON_PATH, AD_IMAGE_FOLDER):
    ad_id_list = []
    ad_location_list = []
    webpage_url = browser.current_url           # for the purpose of check current webpage

    collected_ad_locations = []

    while True:
        all_ad_are_collected_flag = False
        all_dynamic_ad_divs = browser.find_elements_by_class_name('outeradcontainer')
        # for item in all_dynamic_ad_divs:
        #     print item.location, item.size
        # print len(all_dynamic_ad_divs)
        for dynamic_ad_div in all_dynamic_ad_divs:
            ad_div_size = dynamic_ad_div.size
            ad_div_location = dynamic_ad_div.location
            ad_div_area = [0, 0, 0, 0]
            ad_div_area[0] = ad_div_location['x']
            ad_div_area[1] = ad_div_location['y']
            ad_div_area[2] = ad_div_location['x'] + ad_div_size['width']
            ad_div_area[3] = ad_div_location['y'] + ad_div_size['height']
            if ad_div_size['width'] * ad_div_size['height'] <= 2500:
                continue
            if check_retangular_overlap(ad_div_area, collected_ad_locations):
                # print ad_div_area
                if collectAdInfo(browser, webpage_url, current_webpage_id, current_ad_id, ad_div_area, dynamic_ad_div, AD_JSON_PATH, AD_IMAGE_FOLDER):
                    ad_id_list.append(current_ad_id)
                    ad_location_list.append(ad_div_area)
                    current_ad_id += 1
                collected_ad_locations.append(ad_div_area)
                all_ad_are_collected_flag = True
                break
        if all_ad_are_collected_flag == False:
            break

    return current_ad_id, ad_id_list, ad_location_list

def captureWebpage(browser, WEBPAGE_IMAGE_FOLDER, webpage_ID):
    browser.execute_script("window.scrollTo(0, -document.body.scrollHeight);")

    dst_path = WEBPAGE_IMAGE_FOLDER + str(webpage_ID) + '.jpg'
    webpage_size = browser.get_window_size()
    webpage_height = browser.execute_script("return document.body.scrollHeight")
    webpage_width = browser.execute_script("return document.body.scrollWidth")
    result_img = Image.new('RGB', (webpage_width, webpage_height), (255, 255, 255))
    current_window_snapshot_img_path = './current_window_snapshot_img.png'

    browser.get_screenshot_as_file(current_window_snapshot_img_path)
    current_window_snapshot_img = Image.open(current_window_snapshot_img_path)
    result_img.paste(current_window_snapshot_img, (0, 0))

    steps = 1
    while (webpage_height - webpage_size['height']) * 1.0 / steps >= 200:
        steps += 1
    scroll_step = int(((webpage_height - webpage_size['height']) * 1.0) / steps)
    start_x = 0
    start_y = current_window_snapshot_img.size[1] - 1 - scroll_step

    for ii in range(1, steps + 1):
        scroll_script = "window.scrollTo(0, " + str(scroll_step * ii) + ")"
        # print ii, scroll_script
        browser.execute_script(scroll_script)
        time.sleep(0.2)
        browser.get_screenshot_as_file(current_window_snapshot_img_path)
        time.sleep(0.2)
        current_window_snapshot_img = Image.open(current_window_snapshot_img_path)
        crop_top_y = current_window_snapshot_img.size[1] - scroll_step
        crop_btm_y = current_window_snapshot_img.size[1]
        # print (0, crop_top_y, current_window_snapshot_img.size[0], crop_btm_y)
        img_new = current_window_snapshot_img.crop((0, crop_top_y, current_window_snapshot_img.size[0], crop_btm_y))
        # img_new.save('./' + str(ii) + '.jpg')
        start_x = start_x
        start_y = start_y + scroll_step
        # print (start_x, start_y)
        result_img.paste(img_new, (start_x, start_y))
    result_img.save(dst_path)

    return

def collectMSNWebpage(browser, current_webpage_id, WEBPAGE_JSON_PATH, WEBPAGE_IMAGE_FOLDER, ad_id_list, ad_location_list):
    # capture full webpage
    captureWebpage(browser, WEBPAGE_IMAGE_FOLDER, current_webpage_id)

    # collect webpage info
    webpage_id = current_webpage_id
    webpage_url = browser.current_url
    collected_timestamp = time.time()
    webpage_text = ''
    webpage_keywords = ''
    webpage_description = ''
    webpage_title = browser.title
    webpage_ad_id_list = ad_id_list
    webpage_ad_location_list = ad_location_list

    content = browser.page_source
    soup = BeautifulSoup(content, 'html.parser')
    for script in soup(["script", "style"]):
        script.extract()  # rip it out
    # get description
    try:
        for group in soup.findAll('meta', attrs={'name': "description"}):
            webpage_description = group['content']
    except:
        pass
    # get keywords
    try:
        for group in soup.findAll('meta', attrs={'name': "keywords"}):
            webpage_keywords = group['content']
    except:
        pass
        # get the main Content
    try:
        if len(soup.findAll('div', attrs={'id': "Main"})) > 0:
            for group in soup.findAll('div', attrs={'id': "Main"}):
                webpage_text += remove_html_tags(group.get_text())
        elif len(soup.findAll('div', attrs={'class': "yog-col yog-16u yom-primary"})) > 0:
            for group in soup.findAll('div', attrs={'class': "yog-col yog-16u yom-primary"}):
                webpage_text += remove_html_tags(group.get_text())
        elif len(soup.findAll('div', attrs={'class': "leftcol"})):
            for group in soup.findAll('div', attrs={'class': "leftcol"}):
                webpage_text += remove_html_tags(group.get_text())
        elif len(soup.findAll('div', attrs={'id': "ya-center-rail"})):
            for group in soup.findAll('div', attrs={'id': "ya-center-rail"}):
                webpage_text += remove_html_tags(group.get_text())
        else:
            # get text
            text = remove_html_tags(soup.get_text())
            # print 'text', ':\t', text
            # break into lines and remove leading and trailing space on each
            lines = (line.strip() for line in text.splitlines())
            # break multi-headlines into a line each
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            # drop blank lines
            text = '\n'.join(chunk for chunk in chunks if chunk)
            # print 'text', ':\t', text
            webpage_text = text.encode('utf-8')
    except:
        pass

    webpage_info = {}
    webpage_info['webpage_id'] = webpage_id
    webpage_info['webpage_url'] = webpage_url
    webpage_info['collected_timestamp'] = collected_timestamp
    webpage_info['webpage_text'] = webpage_text
    webpage_info['webpage_keywords'] = webpage_keywords
    webpage_info['webpage_description'] = webpage_description
    webpage_info['webpage_title'] = webpage_title
    webpage_info['webpage_ad_id_list'] = webpage_ad_id_list
    webpage_info['webpage_ad_location_list'] = webpage_ad_location_list
    webpage_handle = open(WEBPAGE_JSON_PATH, 'a+')
    json.dump(webpage_info, webpage_handle)
    webpage_handle.write('\n')
    webpage_handle.close()

    return

def load_seed_urls(file_path):
    seed_urls = []
    handle = open(file_path, 'r')
    for line in handle:
        line = line.strip('\n')
        seed_urls.append(line)
    handle.close()
    return seed_urls

def StartCollectMSNAd(browser):
    current_time = datetime.now().strftime('%Y-%m-%d')
    current_dst_folder = os.getcwd() + '/' + str(current_time)
    prepare_dst_folder(current_dst_folder)

    current_webpage_id, current_ad_id = load_current_webpage_ad_id_from_file()
    new_webpage_per_day_threshold = 5000
    MSN_WAITING_TIME = 3
    WEBPAGE_JSON_PATH = current_dst_folder + '/webpage.json'
    WEBPAGE_IMAGE_FOLDER = current_dst_folder + '/webpage_image/'
    AD_JSON_PATH = current_dst_folder + '/ad.json'
    AD_IMAGE_FOLDER = current_dst_folder + '/ad_image/'

    previous_collected_webpage_urls = load_webpage_urls('./collected_webpage_urls.txt')  # we will get all the urls that has been collected by the previous days
    collecting_webpage_urls = load_seed_urls('./seed_urls.txt')  # set seed url
    to_be_collected_webpage_urls = []
    current_collected_webpage_urls = []

    number_fore_rest = 0
    while True:
        for webpage_url in collecting_webpage_urls:
            try:
                if webpage_url in current_collected_webpage_urls:
                    continue
                if webpage_url.find('www.msn.com/en-sg/') == -1:
                    continue

                number_fore_rest += 1
                if number_fore_rest % 10 == 0:
                    if browser:
                        browser.quit()
                    browser = RestartBrowser()

                current_collected_webpage_urls.append(webpage_url)
                save_collected_webpage_urls(webpage_url)

                try:
                    browser.get(webpage_url)
                    time.sleep(MSN_WAITING_TIME)
                except:
                    continue

                # find new urls in current MSN webpage
                to_be_collected_webpage_urls_backup = copy.deepcopy(to_be_collected_webpage_urls)
                try:
                    to_be_collected_webpage_urls = find_new_urls_in_current_webpage(browser, to_be_collected_webpage_urls, \
                                                                                    current_collected_webpage_urls)
                except:
                    to_be_collected_webpage_urls = copy.deepcopy(to_be_collected_webpage_urls_backup)
                ad_id_list = []
                ad_location_list = []
                try:
                    current_ad_id, ad_id_list, ad_location_list = CollectMSNAds(browser, current_webpage_id, current_ad_id, \
                                                                                AD_JSON_PATH, AD_IMAGE_FOLDER)
                except:
                    pass

                # if len(ad_id_list) > 0:
                try:
                    collectMSNWebpage(browser, current_webpage_id, WEBPAGE_JSON_PATH, WEBPAGE_IMAGE_FOLDER, \
                                      ad_id_list, ad_location_list)
                    current_webpage_id += 1
                except:
                    pass
                handle = open('./webpage_ad_id.txt', 'w')
                text = str(current_webpage_id) + '\t' + str(current_ad_id) + '\n'
                handle.write(text)
                handle.close()
                # raw_input('pause')

                if len(set(current_collected_webpage_urls) - set(previous_collected_webpage_urls)) >= new_webpage_per_day_threshold:
                    browser.quit()
                    current_ad_id += 5
                    current_webpage_id += 5
                    handle = open('./webpage_ad_id.txt', 'w')
                    text = str(current_webpage_id) + '\t' + str(current_ad_id) + '\n'
                    handle.write(text)
                    handle.close()
                    return
                if current_webpage_id % 100 == 0:
                    print 'The total number of collected webpages is: \t', current_webpage_id
                    time.sleep(20)
                    if browser:
                        browser.quit()
                    browser = RestartBrowser()
            except:
                if browser:
                    browser.quit()
                browser = RestartBrowser()
                continue
        collecting_webpage_urls = copy.deepcopy(to_be_collected_webpage_urls)
        to_be_collected_webpage_urls = []



if __name__ == '__main__':
    os.chdir('/home/chxiang/PycharmProjects/KDD_BOWEI/crawler_1/msn')
    browser = RestartBrowser()
    StartCollectMSNAd(browser)
    browser.quit()
