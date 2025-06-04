import json
from pathlib import Path


root = Path.cwd()
path_to_json = Path(root, 'glasses.json')


def json_to_dict(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        json_str = file.read()
        dict_list = json.loads(json_str)
    return dict_list

def dict_to_json(data, file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        print(f'Data saved in {file_path}')
