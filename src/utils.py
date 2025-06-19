import json
from pathlib import Path


root = Path.cwd()
path_to_glasses = Path(root, 'glasses.json')
path_to_base = Path(root, 'base.json')


def json_to_dict(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        json_str = file.read()
        dict_list = json.loads(json_str)
    return dict_list

def dict_to_json(data, file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        print(f'Data saved in {file_path}')


def rewriting_database(data):
    dict = {}


    for brand, models in data.items():
        dict[brand] = {}

        for model, gens in models.items():

            values = []
            if model not in dict[brand]:

                dict[brand][model] = {}

            for gen, info in gens.items():
                if gen not in dict[brand][model]:
                    dict[brand][model][gen] = {}


                if info != 'Товар не найден':
                    values.append(info)
                    dict[brand][model][gen] = info

            for gen, info in gens.items():
                if info == 'Товар не найден':
                    if values:
                        first_value = values[0]
                        dict[brand][model][gen] = first_value
                    else:
                        dict[brand][model][gen] = [900, 1550]

    return dict


data = json_to_dict(path_to_glasses)
new_data = rewriting_database(data)
#dict_to_json(new_data, path_to_base)