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
from PIL import Image
from datetime import datetime
from bs4 import BeautifulSoup
# import pyscreenshot as ImageGrab
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

def RestartBrowser():
    while True:
        try:
            # print 'browser restarted!'
            chromedriver = 'D:/KDD_BOWEI/crawler_2/yahoo/chromedriver'
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
            browser = webdriver.Chrome(chromedriver, chrome_options=options)
            browser.set_page_load_timeout(20)
            # browser.get('https://sg.yahoo.com/')
            time.sleep(2)

            return browser
        except:
            time.sleep(5)
            continue

def removeNonAlphNumber(s):
    return re.sub('[^0-9a-zA-Z]+', ' ', s)

def remove_html_tags(data):
    p = re.compile(r'<.*?>')
    return p.sub('\n', data)

def remove_img_tags(data):
    p = re.compile(r'<img.*?/>')
    return p.sub('\n', data)

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
    if not os.path.isfile(dst_file_path):
        src_file_path = './exclude_webpage_url_from_other_country.txt'
        shutil.copy(src_file_path, dst_file_path)
    handle = open(dst_file_path, 'a+')
    text = str(webpage_url) + '\n'
    handle.write(text)
    handle.close()

def load_current_webpage_ad_sponsor_id_from_img_folder(img_folder):
    current_id = 0
    img_list = os.listdir(img_folder)
    if len(img_list) == 0:
        current_id = 0
    else:
        img_name_list = [int(w.split('.')[0]) for w in img_list]
        current_id = max(img_name_list) + 1
    return current_id

def findNewURLsInCurrentWebpage(browser, to_be_collected_webpages, collected_webpages):
    try:
        elems = browser.find_elements_by_xpath("//a[@href]")
        for elem in elems:
            try:
                elem_url = elem.get_attribute("href")
                # print elem_url
                if elem_url.find('yahoo') != -1:
                    if elem_url not in collected_webpages:
                        to_be_collected_webpages.append(elem_url)
            except:
                continue
    except:
        pass
    return to_be_collected_webpages

def groupDivs(all_ad_div_id_dic):
    grouped_ad_divs_dic = {}
    for ad_div_id in all_ad_div_id_dic:
        # print 'start'
        # for key in grouped_ad_divs_dic:
        #     print key, grouped_ad_divs_dic[key]
        # print 'end'
        current_ad_div_location = all_ad_div_id_dic[ad_div_id]
        grouped_ad_div_keys = grouped_ad_divs_dic.keys()
        select_flag = True
        for grouped_ad_div_id in grouped_ad_div_keys:
            grouped_ad_div_location = grouped_ad_divs_dic[grouped_ad_div_id]
            if check_retangular_overlap(current_ad_div_location, grouped_ad_div_location):
                if (current_ad_div_location[3] - current_ad_div_location[1]) * \
                        (current_ad_div_location[2] - current_ad_div_location[0]) <= \
                                (grouped_ad_div_location[3] - grouped_ad_div_location[1]) * \
                                (grouped_ad_div_location[2] - grouped_ad_div_location[0]):
                    del grouped_ad_divs_dic[grouped_ad_div_id]
                    grouped_ad_divs_dic[ad_div_id] = current_ad_div_location
                else:
                    select_flag = False
        if select_flag:
            grouped_ad_divs_dic[ad_div_id] = current_ad_div_location

    return grouped_ad_divs_dic.keys()


def check_retangular_overlap(ad_div_location, collected_ad_div_location):
    # http://stackoverflow.com/questions/9324339/how-much-do-two-rectangles-overlap
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
        return True
    # if ad_div_location[3] > 1080:
    #     return False
    return False

def ad_image_is_blank(ad_image):
    img = ad_image.convert('L')
    img_size = img.size
    img_hist = img.histogram()
    all_pixels = img_size[0] * img_size[1]
    for value in img_hist:
        if value * 1.0 / all_pixels >= 0.9:
            return True
    return False

def collectAdWebpageInfo(browser, current_ad_ID, ad_area, AD_JSON_PATH):
    try:
        ad_location = ad_area
        ad_ID = current_ad_ID
        ad_URL = browser.current_url
        ad_title = browser.title
        ad_description = ''
        ad_keywords = ''
        ad_text = ''

        content = browser.page_source
        soup = BeautifulSoup(content, 'html.parser')
        # get description
        try:
            for group in soup.findAll('meta', attrs={'name': "description"}):
                ad_description = group['content']
        except:
            pass
        # get keywords
        try:
            for group in soup.findAll('meta', attrs={'name': "keywords"}):
                ad_keywords = group['content']
        except:
            pass
        try:
            for script in soup(["script", "style"]):
                script.extract()  # rip it out
            # get text
            text = remove_img_tags(soup.get_text())
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
        ad_info['ad_ID'] = ad_ID
        ad_info['ad_URL'] = ad_URL
        ad_info['ad_title'] = ad_title
        ad_info['ad_description'] = ad_description
        ad_info['ad_keywords'] = ad_keywords
        ad_info['ad_text'] = ad_text
        ad_handle = open(AD_JSON_PATH, 'a+')
        json.dump(ad_info, ad_handle)
        ad_handle.write('\n')
        ad_handle.close()
    except:
        pass
    return

def collectAdInfo(browser, current_webpage_id, current_ad_ID, ad_div, AD_JSON_PATH, AD_IMG_FOLDER, WEBPAGE_AD_IMAGE_FOLDER):
    ad_location = ad_div.location
    ad_size = ad_div.size
    ad_appeared_text = ''
    # locate the ad
    ad_area = [0, 0, 0, 0]
    ad_area[0] = int(ad_location['x'] + 1)
    ad_area[1] = int(ad_location['y'] + 90)
    ad_area[2] = int(ad_location['x'] + ad_size['width'] + 1)
    ad_area[3] = int(ad_location['y'] + ad_size['height'] + 90)
    # scroll to top of webpage
    browser.execute_script("window.scrollTo(0, -document.body.scrollHeight);")
    after_scroll_area = ad_area
    scroll_size = ad_area[3] - 1080
    if scroll_size > 0:
        scroll_script = "window.scrollTo(0, " + str(scroll_size) + ")"
        browser.execute_script(scroll_script)
        time.sleep(1)
        after_scroll_area[1] -= scroll_size
        after_scroll_area[3] = min(after_scroll_area[3] - scroll_size, 1080)
        #captureWebpage(WEBPAGE_AD_IMAGE_FOLDER, str(current_webpage_id) + '_' + str(current_ad_ID))
    #print after_scroll_area
    ad_img_path = AD_IMG_FOLDER + str(current_ad_ID) + '.jpg'

    ad_image = ImageGrab.grab(after_scroll_area)
    if ad_image_is_blank(ad_image):
        arise_exception = 1 / 0
        return False
    ad_image.save(ad_img_path)

    ad_appeared_text = ad_div.text
    # collect the ad info
    ad_div.click()
    time.sleep(2)
    windows_handles = browser.window_handles
    current_window_handle = windows_handles[0]
    if len(windows_handles) == 2:
        current_window_handle = windows_handles[1]
    browser.switch_to_window(current_window_handle)
    collectAdWebpageInfo(browser, current_ad_ID, ad_appeared_text, after_scroll_area, AD_JSON_PATH)
    if len(windows_handles) == 2:
        browser.find_element_by_tag_name('body').send_keys(Keys.CONTROL + 'w')
        browser.switch_to_window(windows_handles[0])
        time.sleep(1)
    else:
        browser.back()
        time.sleep(2)
    if len(browser.window_handles) != 1:
        arise_exception = 1/0
    browser_title = browser.title

    return True

def getAdImage(browser, dst_path, ad_area):
    webpage_size = browser.get_window_size()
    scroll_size = ad_area[3] - webpage_size['height'] + 96
    if scroll_size <= 0:
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
    ad_image = current_window_snapshot_img.crop(after_scroll_area)
    ad_image.save(dst_path)

def collectYahooAd(browser, current_webpage_ID, current_ad_ID, AD_JSON_PATH, AD_IMAGE_FOLDER, WEBPAGE_AD_IMAGE_FOLDER):
    ad_id_list = []
    ad_location_list = []
    css_filter_list = ["div[id*='ad']", "div[id*='Ad']", "div[id*='LDRB']", "div[id*='LREC']",\
                       "div[id*='SKY']", "div[id*='MON']", "div[id*='HB']", "div[id*='NP']", "div[id*='ET']",
                       "div[id*='MNTL']", "div[id*='HB']", "div[id*='MAST']"]
    # collected_ad_div_locations = []
    webpage_url = browser.current_url
    all_ad_div_id_dic = {}
    for css_filter in css_filter_list:
        current_ad_divs = browser.find_elements_by_css_selector(css_filter)
        for current_ad_div in current_ad_divs:
            current_ad_div_id = current_ad_div.get_attribute('id')
            current_ad_div_size = current_ad_div.size
            current_ad_div_location = current_ad_div.location
            ad_area = [0, 0, 0, 0]
            ad_area[0] = int(current_ad_div_location['x'])
            ad_area[1] = int(current_ad_div_location['y'])
            ad_area[2] = int(current_ad_div_location['x'] + current_ad_div_size['width'])
            ad_area[3] = int(current_ad_div_location['y'] + current_ad_div_size['height'])
            if (current_ad_div_size['width'] * current_ad_div_size['height'] <= 200*50) or \
                    (current_ad_div_size['width'] * current_ad_div_size['height'] >= 1000*300) or \
                    current_ad_div_location['x'] <= 50 or current_ad_div_location['y'] <= 50:
                continue
            all_ad_div_id_dic[current_ad_div_id] = ad_area
    # for key in all_ad_div_id_dic:
    #     print key, all_ad_div_id_dic[key], all_ad_div_id_dic[key][3] - all_ad_div_id_dic[key][1], \
    #         all_ad_div_id_dic[key][2] - all_ad_div_id_dic[key][0]
    # print 'start grouping...'
    ad_div_ids = groupDivs(all_ad_div_id_dic)
    # print len(ad_div_ids), ad_div_ids
    for ad_div_id in ad_div_ids:
        if browser.current_url != webpage_url:
            break  # current ad is not clickable
        current_ad_div = browser.find_element_by_id(ad_div_id)
        ad_div_size = current_ad_div.size
        ad_div_location = current_ad_div.location
        ad_area = [0, 0, 0, 0]
        ad_area[0] = int(ad_div_location['x'])
        ad_area[1] = int(ad_div_location['y'])
        ad_area[2] = int(ad_div_location['x'] + ad_div_size['width'])
        ad_area[3] = int(ad_div_location['y'] + ad_div_size['height'])
        if ad_div_size['width'] * ad_div_size['height'] <= 200:
            continue
        # get ad image
        getAdImage(browser, AD_IMAGE_FOLDER + str(current_ad_ID) + '.jpg', ad_area)
        # get ad info
        current_ad_div.click()
        time.sleep(2)
        windows_handles = browser.window_handles
        if browser.current_url == webpage_url and len(windows_handles) == 1:
            continue                    # current ad is not clickable
        current_window_handle = windows_handles[0]
        if len(windows_handles) == 2:
            current_window_handle = windows_handles[1]
        browser.switch_to_window(current_window_handle)
        # content = browser.page_source
        # soup = BeautifulSoup(content, 'html.parser')
        # ad_url = browser.current_url
        collectAdWebpageInfo(browser, current_ad_ID, ad_area, AD_JSON_PATH)
        # if len(windows_handles) == 2:
        #     browser.find_element_by_tag_name('body').send_keys(Keys.CONTROL + 'w')
        #     browser.switch_to_window(windows_handles[0])
        #     time.sleep(1)
        # else:
        #     browser.back()
        #     time.sleep(2)
        while len(browser.window_handles) != 1:
            current_windows_handles = browser.window_handles
            browser.switch_to_window(browser.window_handles[len(current_windows_handles) - 1])
            # browser.find_element_by_tag_name('body').send_keys(Keys.CONTROL + 'w')
            browser.close()
            time.sleep(0.1)
        browser.switch_to_window(browser.window_handles[0])

        ad_id_list.append(current_ad_ID)
        ad_location_list.append(ad_area)
        current_ad_ID += 1
    # while True:
    #     ad_div_s = []
    #     for css_filter in css_filter_list:
    #         current_ad_divs = browser.find_elements_by_css_selector(css_filter)
    #         for current_ad_div in current_ad_divs:
    #             ad_div_s.append(current_ad_div)
    #             # print current_ad_div.get_attribute('id')
    #     ad_div_location_s, ad_div_s, ad_div_ids = groupDivs(ad_div_s)
    #     print '@@@@', len(ad_div_s)
    #     for ii in range(len(ad_div_s)):
    #         try:
    #             ad_div = ad_div_s[ii]
    #             ad_div_location = ad_div_location_s[ii]
    #             if check_retangular_overlap(ad_div_location, collected_ad_div_locations):
    #                 if collectAdInfo(browser, current_webpage_id, current_ad_id, ad_div, AD_JSON_PATH, \
    #                                  AD_IMAGE_FOLDER, WEBPAGE_AD_IMAGE_FOLDER):
    #                     ad_id_list.append(current_ad_id)
    #                     ad_location_list.append(ad_div_location)
    #                     current_ad_id += 1
    #             collected_ad_div_locations.append(ad_div_location)
    #         except:
    #             continue
    #     break
    return current_ad_ID, ad_id_list, ad_location_list

def getSponsorInfo(ori_sponsor_url, current_sponsor_id, sponsor_text, sponsor_location, SPONSOR_JSON_PATH):
    sponsor_url = ''
    sponsor_id = current_sponsor_id
    sponsor_appear_text = sponsor_text
    sponsor_location = sponsor_location
    sponsor_title = ''
    sponsor_keywords = ''
    sponsor_description = ''
    sponsor_webpage_text = ''
    sponsor_timestamp = time.time()

    try:
        response = urllib2.urlopen(ori_sponsor_url, timeout=3)
        sponsor_url = response.geturl()
        content = response.read()
        soup = BeautifulSoup(content)
        # get title
        sponsor_title = soup.title.string
        # get description
        for group in soup.findAll('meta', attrs={'name': "description"}):
            sponsor_description = group['content']
        # get keywords
        for group in soup.findAll('meta', attrs={'name': "keywords"}):
            sponsor_keywords = group['content']
        for script in soup(["script", "style"]):
            script.extract()  # rip it out
        # get text
        text = remove_img_tags(soup.get_text())
        # break into lines and remove leading and trailing space on each
        lines = (line.strip() for line in text.splitlines())
        # break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # drop blank lines
        text = '\n'.join(chunk for chunk in chunks if chunk)
        # print 'text', ':\t', text
        sponsor_webpage_text = text.encode('utf-8')
    except:
        sponsor_url = ori_sponsor_url

    sponsor_info = {}
    sponsor_info['sponsor_url'] = sponsor_url
    sponsor_info['sponsor_id'] = sponsor_id
    sponsor_info['sponsor_appear_text'] = sponsor_appear_text
    sponsor_info['sponsor_location'] = sponsor_location
    sponsor_info['sponsor_title'] = sponsor_title
    sponsor_info['sponsor_keywords'] = sponsor_keywords
    sponsor_info['sponsor_description'] = sponsor_description
    sponsor_info['sponsor_text'] = sponsor_webpage_text
    sponsor_info['sponsor_timestamp'] = sponsor_timestamp
    handle = open(SPONSOR_JSON_PATH, 'a+')
    json.dump(sponsor_info, handle)
    handle.write('\n')
    handle.close()
    # except:
    #     pass

    return

def collectYahooSponsor(browser, current_webpage_id, current_sponsor_id, SPONSOR_JSON_PATH, SPONSOR_IMAGE_FOLDER, WEBPAGE_SPONSOR_IMAGE_FOLDER):
    sponsor_id_list = []
    sponsor_location_list = []
    sponsor_url_list = []
    sponsor_text_list = []
    sponsor_number = 0

    sponsored_div_s = browser.find_elements_by_xpath("//li[contains(.,'Sponsored')]")
    sponsor_number = len(sponsored_div_s)
    webpage_size = browser.get_window_size()

    for sponsored_div in sponsored_div_s:
        # find sponsor location
        sponsored_size = sponsored_div.size
        sponsored_location = sponsored_div.location
        sponsored_area = [0, 0, 0, 0]
        sponsored_area[0] = int(sponsored_location['x'])
        sponsored_area[1] = int(sponsored_location['y'])
        sponsored_area[2] = int(sponsored_location['x'] + sponsored_size['width'] )
        sponsored_area[3] = int(sponsored_location['y'] + sponsored_size['height'] )

        # get displayed sponsored in Yahoo
        scroll_size = sponsored_area[3] - webpage_size['height'] + 96
        if scroll_size < 0:
            scroll_size = 0
        browser.execute_script("window.scrollTo(0, " + str(scroll_size) + ")")
        time.sleep(0.2)
        current_window_snapshot_img_path = './current_window_snapshot_img.png'
        browser.get_screenshot_as_file(current_window_snapshot_img_path)
        time.sleep(0.2)
        current_window_snapshot_img = Image.open(current_window_snapshot_img_path)
        after_scroll_area = [0, 0, 0, 0]
        after_scroll_area[0] = sponsored_area[0]
        after_scroll_area[1] = sponsored_area[1] - scroll_size
        after_scroll_area[2] = sponsored_area[2]
        after_scroll_area[3] = sponsored_area[3] - scroll_size
        sponsor_image = current_window_snapshot_img.crop(after_scroll_area)
        sponsor_image.save(WEBPAGE_SPONSOR_IMAGE_FOLDER + str(current_sponsor_id) + '.jpg')

        sponsor_text = sponsored_div.text
        sponsor_text_list.append(sponsor_text)
        sponsor_location_list.append(sponsored_area)

        # find sponsor image url
        sponsor_str = sponsored_div.get_attribute('outerHTML')
        IMAGE_EXTENTIONS = ['.jpg', 'jpeg', '.JPG', '.JPEG', '.png', '.bmp']
        for image_extention in IMAGE_EXTENTIONS:
            try:
                div_source = sponsor_str
                jpg_index = div_source.find(image_extention)
                start_index = max(jpg_index - 100, 0)
                end_index = jpg_index + len(image_extention)
                div_source = div_source[start_index:end_index]
                jpg_start = div_source.find('http')
                jpg_end = div_source.find(image_extention) + len(image_extention)
                sponsor_image_url = div_source[jpg_start:jpg_end]
                dst_sponsor_img_path = SPONSOR_IMAGE_FOLDER + str(current_sponsor_id) + '.jpg'
                urllib.urlretrieve(sponsor_image_url, dst_sponsor_img_path)
                break
            except:
                continue

        # find sponsor url
        elems = sponsored_div.find_elements_by_css_selector('a')
        for elem in elems:
            try:
                elem_url = elem.get_attribute('href')
                if str(elem_url).find('beap.gemini') != -1:
                    sponsor_url_list.append(elem_url)
                    sponsor_url = elem_url
                    getSponsorInfo(sponsor_url, current_sponsor_id, sponsor_text, sponsored_area, SPONSOR_JSON_PATH)
                    break
            except:
                continue

        sponsor_id_list.append(current_sponsor_id)
        current_sponsor_id += 1



    return current_sponsor_id, sponsor_id_list, sponsor_location_list


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

def collectYahooWebpage(browser, current_webpage_id, WEBPAGE_JSON_PATH, WEBPAGE_IMAGE_FOLDER, ad_id_list, \
                        ad_location_list, sponsor_id_list, sponsor_location_list):
    # capture webpage image
    captureWebpage(browser, WEBPAGE_IMAGE_FOLDER, current_webpage_id)

    webpage_id = current_webpage_id
    webpage_url = browser.current_url
    collected_timestamp = time.time()
    webpage_text = ''
    webpage_keywords = ''
    webpage_description = ''
    webpage_title = browser.title
    webpage_ad_id_list = ad_id_list
    webpage_ad_location_list = ad_location_list
    webpage_sponsor_id_list = sponsor_id_list
    webpage_sponsor_location_list = sponsor_location_list

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
            text = remove_img_tags(soup.get_text())
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
    webpage_info['webpage_sponsor_id_list'] = webpage_sponsor_id_list
    webpage_info['webpage_sponsor_location_list'] = webpage_sponsor_location_list

    # for key in webpage_info:
    #     print key, ':\t', webpage_info[key]

    webpage_handle = open(WEBPAGE_JSON_PATH, 'a+')
    json.dump(webpage_info, webpage_handle)
    webpage_handle.write('\n')
    webpage_handle.close()
    return

def prepare_dst_folder(current_folder):
    if os.path.isdir(current_folder):
        print 'Directory already exist...'
        shutil.rmtree(current_folder)
    os.mkdir(current_folder)
    os.mkdir(current_folder + '/ad_image/')
    os.mkdir(current_folder + '/webpage_ad_image/')
    os.mkdir(current_folder + '/sponsor_image/')
    os.mkdir(current_folder + '/webpage_image/')
    os.mkdir(current_folder + '/webpage_sponsor_image/')

def load_current_webpage_ad_sponsor_id_from_file():
    current_webpage_id = 0
    current_ad_id = 0
    current_sponsor_id = 0
    file_path = './webpage_ad_sponsor_id.txt'
    if os.path.isfile(file_path):
        handle = open(file_path, 'r')
        for line in handle:
            line = line.strip('\n').split('\t')
            line = [int(w) for w in line]
            current_webpage_id = line[0]
            current_ad_id = line[1]
            current_sponsor_id = line[2]
        handle.close()
    else:
        pass
    return current_webpage_id, current_ad_id, current_sponsor_id

def load_seed_urls(file_path):
    seed_urls = []
    handle = open(file_path, 'r')
    for line in handle:
        line = line.strip('\n')
        seed_urls.append(line)
    handle.close()
    return seed_urls

def StartCollectYahooAd():
    current_time = datetime.now().strftime('%Y-%m-%d')
    current_dst_folder = os.getcwd() + '/' + str(current_time)
    prepare_dst_folder(current_dst_folder)

    # current_webpage_id = load_current_webpage_ad_sponsor_id_from_img_folder('./webpage_image/')
    # current_ad_id = load_current_webpage_ad_sponsor_id_from_img_folder('./ad_image/')
    # current_sponsor_id = load_current_webpage_ad_sponsor_id_from_img_folder('./sponsor_image/')
    current_webpage_id, current_ad_id, current_sponsor_id = load_current_webpage_ad_sponsor_id_from_file()

    new_webpage_per_day_threshold = 500
    TIME_GAP = 5 * 60                       # we collect the ads at these webpages every 5 mins

    YAHOO_WAITING_TIME = 3
    WEBPAGE_JSON_PATH = current_dst_folder + '/webpage.json'                            # textual information about the webpage
    WEBPAGE_IMAGE_FOLDER = current_dst_folder + '/webpage_image/'                       # the full webpage screen.
    AD_JSON_PATH = current_dst_folder + '/ad.json'                                      # store ad textual data with json format
    AD_IMAGE_FOLDER = current_dst_folder + '/ad_image/'                                 # the displayed ad within the webpage
    WEBPAGE_AD_IMAGE_FOLDER = current_dst_folder + '/webpage_ad_image/'                 # currently not in usage
    SPONSOR_JSON_PATH = current_dst_folder + '/sponsor.json'                            # textual information about the sponsored ad
    SPONSOR_IMAGE_FOLDER = current_dst_folder + '/sponsor_image/'                       # the displayed sponsor ad within the webpage
    WEBPAGE_SPONSOR_IMAGE_FOLDER = current_dst_folder + '/webpage_sponsor_image/'       # the origional sponsor image

    previous_collected_webpage_urls = load_webpage_urls('./collected_webpage_urls.txt')

    collecting_webpage_urls = load_seed_urls('./yahoo_seed_urls.txt')

    # number_for_rest = 0

    while True:
        tic = time.time()
        browser = RestartBrowser()
        for webpage_url in collecting_webpage_urls:
            try:
            # if True:
                if False:
                    continue
                else:
                    if webpage_url.find('yahoo') == -1:            # if the webpage does not belong to YAHOO
                        continue
                    if len(browser.window_handles) != 1:
                        browser.quit()
                        browser = RestartBrowser()

                    try:
                        browser.get(webpage_url)
                        time.sleep(YAHOO_WAITING_TIME)
                    except:
                        pass
                        # print 'arise an exception when executing browser.get(webpage_url)'
                        # browser.quit()
                        # browser = RestartBrowser()
                        # continue

                    # try:
                    if True:
                        ad_id_list = []
                        ad_location_list = []
                        try:
                            current_ad_id, ad_id_list, ad_location_list = collectYahooAd(browser, current_webpage_id, current_ad_id, \
                                                                          AD_JSON_PATH, AD_IMAGE_FOLDER, WEBPAGE_AD_IMAGE_FOLDER)
                        except:
                            pass
                        # print 'collect ad...'
                        # raw_input('pause')
                        sponsor_id_list = []
                        sponsor_location_list = []
                        try:
                            current_sponsor_id, sponsor_id_list, sponsor_location_list = collectYahooSponsor(browser, current_webpage_id, \
                                                                                                             current_sponsor_id, \
                                                                                                             SPONSOR_JSON_PATH, \
                                                                                                             SPONSOR_IMAGE_FOLDER, \
                                                                                                             WEBPAGE_SPONSOR_IMAGE_FOLDER)
                        except:
                            pass
                        # print 'collect sponsor...'
                        try:
                            collectYahooWebpage(browser, current_webpage_id, WEBPAGE_JSON_PATH, WEBPAGE_IMAGE_FOLDER, \
                                                ad_id_list, ad_location_list, sponsor_id_list, sponsor_location_list)
                        except:
                            pass
                        print 'collect webpage...'
                        current_webpage_id += 1

                        webpage_ad_id_handle = open('./webpage_ad_sponsor_id.txt', 'w')
                        text = str(current_webpage_id) + '\t' + str(current_ad_id) + '\t' + str(
                            current_sponsor_id) + '\n'
                        webpage_ad_id_handle.write(text)
                        webpage_ad_id_handle.close()
                            # raw_input('pause')

                            # control the number of new webpages
                            # if len(set(current_collected_webpage_urls) - set(previous_collected_webpage_urls)) >= new_webpage_per_day_threshold:
                            #     browser.quit()
                            #     current_ad_id += 5
                            #     current_sponsor_id += 5
                            #     current_webpage_id += 5
                            #     webpage_ad_id_handle = open('./webpage_ad_sponsor_id.txt', 'w')
                            #     text = str(current_webpage_id) + '\t' + str(current_ad_id) + '\t' + str(current_sponsor_id) + '\n'
                            #     webpage_ad_id_handle.write(text)
                            #     webpage_ad_id_handle.close()
                            #     return

                            # arise an exception every 100 webpages
                        if current_webpage_id % 100 == 0:
                            print 'The number of collected webpage is:\t', current_webpage_id
                            time.sleep(20)

                    # except:
                    #     print 'Arise an exception:\t'
                    #     browser.quit()
                    #     browser = RestartBrowser()
            except:
                continue
        # collecting_webpage_urls = copy.deepcopy(to_be_collectd_webpage_urls)
        # to_be_collectd_webpage_urls = []
        if browser:
            browser.quit()
        while time.time() - tic <= TIME_GAP:
            time.sleep(0.1)


if __name__ == '__main__':
    os.chdir('D:/KDD_BOWEI/crawler_2/yahoo/')
    StartCollectYahooAd()

