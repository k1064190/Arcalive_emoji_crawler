import webbrowser
import selenium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import moviepy
from moviepy.editor import VideoFileClip
import requests
import sys
import time
import os
import multiprocessing
from multiprocessing import Pool
import bs4 as bs

emoticon_url = 'https://arca.live/e/?target=title&keyword=%EC%A7%AD%EC%B0%BD%EA%B3%A0&sort=rank&p='
savepath = 'store'
login_url = 'https://arca.live/u/login/'

def get_images_from_page(page):
    paged_emoticon_url = emoticon_url + str(page)
    res = requests.get(paged_emoticon_url)
    soup = bs.BeautifulSoup(res.text, 'html.parser')

    # get all a tags in div[class=emoticon-list]
    a_tags = soup.select('div[class=emoticon-list]>a')

    if len(a_tags) == 0:
        # no more emoticon pages
        return

    # get href of each a tag
    emoticon_urls = []
    for a in a_tags:
        emoticon_urls.append('https://arca.live' + a['href'])

    count = 0
    for emo_p, emo_url in enumerate(emoticon_urls):
        emotions_page_res = requests.get(emo_url)
        emotions_page_soup = bs.BeautifulSoup(emotions_page_res.text, 'html.parser')

        # get all img tags in div[class=emoticons-wrapper]
        emoticons_wrapper = emotions_page_soup.find('div', attrs={'class': 'emoticons-wrapper'})
        img_tags = emotions_page_soup.select('div[class=emoticons-wrapper]>img')

        # get src of each img tag and download it
        img_urls = []
        for img_tag in img_tags:
            # example src is
            # src="//ac-p1.namu.la/20220706sac2/d32268a8f632622b6ceee4044e806f4451ad6070bbe3704515365f85330a840b.png?expires=1706749200&key=eu5RMXU8H2AyKYH0Ed52pw"
            src = img_tag['src']
            img_urls.append('https:' + src)

        for i, img_url in enumerate(img_urls):
            # download img
            response = requests.get(img_url)
            img_filename = f"{page:02d}_{count:08d}.png"
            count += 1
            with open(os.path.join(savepath, img_filename), 'wb') as f:
                f.write(response.content)

        print(f"page {page}, emo_p {emo_p} done")
    return


def main():
    # get current dir
    current_dir = os.getcwd()
    # add dirname to current dir
    dirname = os.path.join(current_dir, savepath)
    # if dirname does not exist in current dir, make it
    if not os.path.exists(dirname):
        os.mkdir(dirname)

    max_page = 34
    pool = Pool()
    pool.map(get_images_from_page, range(1, max_page + 1))

    pool.close()
    pool.join()


if __name__ == '__main__':
    main()
