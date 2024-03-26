import time
import datetime
import os
import argparse
import random
import shutil

from tqdm import tqdm

from soup import get_soup
from utils import arg_as_dict, session, sanitize_directory_name
from vpn import VPN, WaitUntilVPNConnected, WaitUntilVPNDisconnected, checkVPNConnected


def read(url, args, s):
    # e.g) self.url = https://exhentai.org/((?f_search=.*)|(tag/.*))
    # create a log file
    global myvpn
    now = datetime.datetime.now()
    if not os.path.exists(args.output):
        os.makedirs(args.output)
    log_dir = os.path.join(args.output, f'{now.strftime("%Y-%m-%d_%H-%M-%S")}-page{args.pages}.log')
    error_dir = os.path.join(args.output, f'{now.strftime("%Y-%m-%d_%H-%M-%S")}-page{args.pages}.error')
    use_vpn = args.myvpn is not None
    if use_vpn:
        myvpn = os.listdir(args.myvpn)
    vpn_connected = None
    with open(log_dir, "w", encoding='utf-8') as log, open(error_dir, "w", encoding='utf-8') as error:
        log.write(f"URL: {url}\n")
        log.write(f"Pages: {args.pages}\n")
        log.write(f"Tags: {args.tags}\n")
        log.write(f"Filter: {args.filter}\n")

        pages = args.pages
        page_soup = get_soup(url, s)
        page_number = 1
        while True:
            if page_number >= pages:
                log.write(f"Getting articles from {page_number} page\n")
                list_items = page_soup.find_all("td", class_="gl3c glname")
                len_articles = len(list_items)
                pbar = tqdm(list_items, total=len_articles, leave=False, position=0, unit="arts",
                                    desc=f"{page_number} page : Title".ljust(60),
                                    bar_format="{desc}{percentage:3.0f}%|{bar:25}{r_bar}")
                for article in pbar:
                    # [soup, tags={"artist": ["artist1", "artist2"], "group": ["group1", "group2"], ...}]
                    # create directorys for each article_and_tags
                    # e.g) title
                    article_url = article.find("a")["href"]
                    article_soup = get_soup(article_url, s)
                    title = get_title(article_soup)
                    desc = f"{page_number} page : {title}".ljust(60)[:60]
                    pbar.set_description(desc)
                    tags = get_tags(article_soup)
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
                    if not is_valid:
                        log.write(f"Skipping {title} because of the tags\n")
                        continue
                    # some of the title will not be able to be used as a directory name
                    title = sanitize_directory_name(title)
                    directory = os.path.join(args.output, title)
                    # if the directory already exists, skip
                    if os.path.exists(directory):
                        continue
                    os.makedirs(directory)
                    log.flush()

                    log.write("Getting pictures from " + title + "\n")
                    picture_pages = get_picture_pages(article_soup, s)
                    len_pictures = len(picture_pages)
                    # save the pictures in a directory in a form of 1, 2, 3, ...
                    log.write(f"Found {len_pictures} pictures\n")
                    save_tags(directory, tags)
                    idx = save_pictures_from_pages_list(title, picture_pages, directory, s, error, len_pictures - 1)
                    if idx != -1:   # bandwidth exceeded
                        log.write("bandwidth exceeded\n")
                        # if use_vpn is False, just remove the directory and return
                        if not use_vpn:
                            # wait for 1 minute and retry
                            time.sleep(120)
                            idx = save_pictures_from_pages_list(title, picture_pages, directory, s, error, idx)
                            if idx != -1:
                                time.sleep(7200)
                                idx = save_pictures_from_pages_list(title, picture_pages, directory, s, error, idx)
                                if idx != -1:
                                    log.write("Why bandwidth exceeded again?\n")
                                    shutil.rmtree(directory)
                                    return
                        else:
                            try:
                                # try 2 times
                                for _ in range(3):
                                    if not checkVPNConnected():
                                        connect_vpn = random.choice(myvpn)
                                        VPN("connect", args.vpn, connect_vpn)
                                        WaitUntilVPNConnected()
                                    else:
                                        VPN("disconnect_all", args.vpn)
                                        WaitUntilVPNDisconnected()
                                    # retry the page
                                    idx = save_pictures_from_pages_list(title, picture_pages, directory, s, error, idx)
                                    if idx == -1:
                                        break
                                if idx != -1:
                                    # wait for 2 hours
                                    if checkVPNConnected():
                                        VPN("disconnect_all", args.vpn)
                                        WaitUntilVPNDisconnected()
                                    time.sleep(7200)
                                    idx = save_pictures_from_pages_list(title, picture_pages, directory, s, error, idx)
                                    if idx != -1:
                                        log.write("Why bandwidth exceeded again?\n")
                                        shutil.rmtree(directory)
                                        return
                            except Exception as e:
                                log.write("VPN connection failed with error: " + str(e) + "\n")
                                shutil.rmtree(directory)
                                return
                pbar.close()
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

def save_pictures_from_pages_list(title, urls, dir, s, log, start):
    global img_em
    len_pics = start + 1
    for i in tqdm(range(start, -1, -1), position=1, unit="pics", leave=False, total=len_pics):
        url = urls[i]
        # get picture url from the page
        success = False
        for _ in range(3):
            try:
                soup = get_soup(url, s)
                img_em = soup.find("img", {"id": "img"})
                success = True
                break
            except AttributeError:
                log.write(f"Missing page: {url} (i: {i})\n")
                log.flush()
                continue
        if not success:
            raise Exception("Missing page: " + url)
        ref = img_em["src"]
        if ref == "https://exhentai.org/img/509.gif":
            # log the bandwidth exceeded page
            log.write(f"Bandwidth exceeded: {url} (i: {i})\n")
            log.flush()
            return i
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
                if ref == "https://exhentai.org/img/509.gif":
                    # log the bandwidth exceeded page
                    log.write(f"Bandwidth exceeded: {url} (i: {i})\n")
                    return i
                res = get_soup(ref, s, g_soup=False, image=True)
                if res is None:
                    # log the missing page
                    log.write(f"Missing page: {url} (i: {i})\n")
                    log.flush()
                    continue
            else:
                # log the missing page
                log.write(f"Missing page: {url} (i: {i})\n")
                log.flush()
                continue

        img_filename = f"{i:04d}.{ext}"
        with open(os.path.join(dir, img_filename), 'wb') as f:
            f.write(res.content)

    return -1


def parse_args():
    parser = argparse.ArgumentParser(description='Download from exhentai, e-hentai')
    parser.add_argument('--url', '-u', type=str, help='url', required=True)
    parser.add_argument('--pages', '-p', type=int, help='1', default=1)
    parser.add_argument('--tags', '-t', type=arg_as_dict, help='{"artist": ["artist1", "artist2"], "group": ["group1", "group2"], ...}', default=None)
    parser.add_argument('--filter', '-f', type=arg_as_dict, help='{"artist": ["artist1", "artist2"], "group": ["group1", "group2"], ...}', default=None)
    parser.add_argument('--output', '-o', type=str, default='output')
    parser.add_argument('--vpn', '-v', type=str, default='C:/Program Files/OpenVPN/bin/openvpn-gui.exe')
    parser.add_argument('--myvpn', '-m', type=str, default=None)
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    s = session()
    read(args.url, args, s)
