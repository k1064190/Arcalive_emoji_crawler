import ast
import os
import re

from dotenv import load_dotenv


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


def session():
    load_dotenv()

    id = os.getenv("ID")
    pwd = os.getenv("PWD")
    session = os.getenv("SESSION")

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0"}
    cookies = {'ipb_member_id': id, 'ipb_pass_hash': pwd, 'ipb_session_id': session}

    return {"headers": headers, "cookies": cookies}


def sanitize_directory_name(name):
    # remove characters that windows does not allow
    # e.g) \/:*?"<>|
    title = re.sub(r'[\\/:*?"<>|]', '', name)
    title = title.strip(' ')
    title = title.strip('.')
    return title
