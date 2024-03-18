import time
import datetime
import os
import multiprocessing
from multiprocessing import Pool
import requests
from bs4 import BeautifulSoup as Soup
import argparse
import ast
import random
from dotenv import load_dotenv
import re

def sanitize_directory_name(name):
    # remove characters that windows does not allow
    # e.g) \/:*?"<>|
    return re.sub(r'[\\/:*?"<>|]', '', name)

def read(url, args, s):
    # e.g) self.url = https://exhentai.org/((?f_search=.*)|(tag/.*))
    # create a log file
    now = datetime.datetime.now()
    log_dir = os.path.join(args.output, f'{now.strftime("%Y-%m-%d_%H-%M-%S")}-page{args.pages}.log')
    error_dir = os.path.join(args.output, f'{now.strftime("%Y-%m-%d_%H-%M-%S")}-page{args.pages}.error')
    with open(log_dir, "w", encoding='utf-8') as log, open(error_dir, "w", encoding='utf-8') as error:
        log.write(f"URL: {url}\n")
        log.write(f"Pages: {args.pages}\n")
        log.write(f"Tags: {args.tags}\n")
        log.write(f"Filter: {args.filter}\n")

        pages = args.pages
        print('Getting pages')
        page_soup = get_soup(url, s)
        page_number = 1
        while True:
            if page_number >= pages:
                print(f"Getting articles from {page_number} page")
                log.write(f"Getting articles from {page_number} page\n")
                articles_list = get_articles_list(page_soup, s, args)
                for article_and_tags in articles_list:
                    # [soup, tags={"artist": ["artist1", "artist2"], "group": ["group1", "group2"], ...}]
                    # create directorys for each article_and_tags
                    # e.g) title
                    title = get_title(article_and_tags[0])
                    # some of the title will not be able to be used as a directory name
                    title = sanitize_directory_name(title)
                    directory = os.path.join(args.output, title)
                    print("Saving " + title)
                    log.write(f"Saving {title}\n")
                    # if the directory already exists, skip
                    if os.path.exists(directory):
                        print(f"{title} already exists")
                        log.write(f"{title} already exists\n")
                        continue
                    os.makedirs(directory)
                    log.flush()

                    picture_pages = get_picture_pages(article_and_tags[0], s)
                    # save the pictures in a directory in a form of 1, 2, 3, ...
                    save_tags(directory, article_and_tags[1])
                    save_pictures_from_pages_list(picture_pages, directory, s, error)
            # next page if exists
            # page = get_soup(page.find("a", {"id" : "dnext"})["href"])
            next = page_soup.find("a", {"id": "dnext"})
            if next is None:
                break
            page_soup = get_soup(next["href"], s)
            page_number += 1

def save_tags(directory, tags):
    # save tags as a text file in a format of json stringify
    with open(os.path.join(directory, "tags.txt"), "w") as f:
        f.write(str(tags))

def get_title(soup):
    title = soup.find("h1", {"id": "gn"}).text
    return title

def get_tags(soup):
    tags = {}
    tag_table = soup.find("div", {"id": "taglist"})
    tag_types = tag_table.find_all("tr")
    for tag_type in tag_types:
        tag_info = tag_type.find_all("td")
        tag_type_name = tag_info[0].text[:-1] # remove the last character ":"
        tag_type_tags = tag_info[1].find_all("div")
        tag_type_tags = [tag.find("a").text for tag in tag_type_tags]
        tags[tag_type_name] = tag_type_tags
    return tags

def get_articles_list(soup, s, args):
    articles_list = []
    list_items = soup.find_all("td", class_="gl3c glname")
    for list_item in list_items:
        page = list_item.find("a")["href"]
        soup = get_soup(page, s)
        tags = get_tags(soup)
        # e.g) tags = {"artist": ["artist1", "artist2"], "group": ["group1", "group2"], ...}
        # check if the tags satisfy the filter and tags
        is_valid = True
        if args.filter is not None:
            for key, value in args.filter.items():
                if key not in tags:
                    continue
                if not any([v in tags[key] for v in value]):
                    continue
                is_valid = False
                break

        if is_valid and args.tags is not None:
            for key, value in args.tags.items():
                if key in tags:
                    if all([v in tags[key] for v in value]):
                        continue
                is_valid = False
                break

        if is_valid:
            articles_list.append([soup, tags])

    print("Found " + str(len(articles_list)) + " articles on this page.")
    return articles_list

def get_picture_pages(soup, s):
    pages_list = []
    while True:
        list_body = soup.find("div", {"id": "gdt"})
        # find gdtm or gdtl
        list_items = list_body.find_all("div", {"class": ["gdtm", "gdtl"]})
        for list_item in list_items:
            page = list_item.find("a")["href"]
            pages_list.append(page)
        # next page
        table = soup.find("table", class_="ptt")
        tr = table.find("tr")
        td = tr.find_all("td")
        next_page_exists = not ('ptdd' in td[-1].get("class", []))
        if not next_page_exists:
            break
        next_page = td[-1].find("a")["href"]
        soup = get_soup(next_page, s)
    return pages_list

def save_pictures_from_pages_list(urls, dir, s, log):
    for i, url in enumerate(urls):
        # get picture url from the page
        soup = get_soup(url, s)
        img_em = soup.find("img", {"id": "img"})
        ref = img_em["src"]
        ext = ref.split(".")[-1]
        # save the picture with requests.get(url)
        res = get_soup(ref, s, g_soup=False, image=True)
        if res is None:
            onerror = img_em.get("onerror", None)
            if onerror is not None:
                # redirect to the nl page
                # e.g) onerror="this.onerror=null; nl('35279-475179')"
                # function nl(a) {
                #     document.location += (-1 < (document.location + "").indexOf("?") ? "&" : "?") + "nl=" + a;
                #     return !1
                # }
                # get the number from the onerror
                number = onerror.split("'")[1]
                # get the nl page
                url = f"{url}{'&' if '?' in url else '?'}nl={number}"
                soup = get_soup(url, s)
                img_em = soup.find("img", {"id": "img"})
                ref = img_em["src"]
                res = get_soup(ref, s, g_soup=False, image=True)
                if res is None:
                    # log the missing page
                    print(f"Missing page: {url} (i: {i})")
                    log.write(f"Missing page: {url} (i: {i})\n")
                    log.flush()
                    continue
            else:
                # log the missing page
                print(f"Missing page: {url} (i: {i})")
                log.write(f"Missing page: {url} (i: {i})\n")
                log.flush()
                continue

        img_filename = f"{i:04d}.{ext}"
        with open(os.path.join(dir, img_filename), 'wb') as f:
            f.write(res.content)

def arg_as_list(s):
    v = ast.literal_eval(s)
    if type(v) is not list:
        return None
    return v

def arg_as_dict(s):
    v = ast.literal_eval(s)
    if type(v) is not dict:
        return None
    # e.g) "{'artist': ['artist1', 'artist2'], 'group': ['group1', 'group2'], ...}"
    # if there is _ in keys and values, replace it with space
    new_dict = {}
    keys, values = list(v.keys()), list(v.values())
    for key, value in zip(keys, values):
        new_values = []
        for old_value in value:
            new_values.append(old_value.replace("_", " "))
        new_key = key.replace("_", " ")
        new_dict[new_key] = new_values
    return new_dict

def parse_args():
    parser = argparse.ArgumentParser(description='Download from exhentai, e-hentai')
    parser.add_argument('--url', '-u', type=str, help='url', required=True)
    parser.add_argument('--pages', '-p', type=int, help='1', default=1)
    parser.add_argument('--tags', '-t', type=arg_as_dict, help='{"artist": ["artist1", "artist2"], "group": ["group1", "group2"], ...}', default=None)
    parser.add_argument('--filter', '-f', type=arg_as_dict, help='{"artist": ["artist1", "artist2"], "group": ["group1", "group2"], ...}', default=None)
    parser.add_argument('--output', '-o', type=str, default='output')
    return parser.parse_args()

def session():
    load_dotenv()

    id = os.getenv("ID")
    pwd = os.getenv("PWD")
    session = os.getenv("SESSION")

    print("ID: " + id, type(id))
    print("PWD: " + pwd, type(pwd))
    print("SESSION: " + session, type(session))

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0"}
    cookies = {'ipb_member_id': id, 'ipb_pass_hash': pwd, 'ipb_session_id': session}

    return {"headers": headers, "cookies": cookies}

global_time = time.time()
def get_soup(url, s, g_soup=True, image=False):
    global global_time
    # delay the request to avoid being blocked
    #
    curtime = time.time()
    if not image:
        if curtime - global_time < 1000:
            # sleep time with gaussian distribution of mean 3 and std 1 between 1.5 ~ 4.5
            time.sleep(min(max(random.gauss(1.5, 1), 1), 3))
            # time.sleep(random.randint(1000, 3000) / 1000)
    global_time = curtime
    try:
        res = requests.get(url, **s, timeout=30)
    except requests.exceptions.RequestException:
        return None
    if g_soup:
            res = Soup(res.text, "html.parser")
    return res

if __name__ == "__main__":
    args = parse_args()
    s = session()
    read(args.url, args, s)