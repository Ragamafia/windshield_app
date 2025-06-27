import json

from logger import logger


def json_to_dict(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        json_str = file.read()
        dict_list = json.loads(json_str)
    return dict_list

def dict_to_json(data, file_path):
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
        print(f'Data saved in {file_path}')


def save_image(save_dir, img):
    save_dir.mkdir(parents=True, exist_ok=True)
    filename = save_dir / "img.jpg"
    if filename.exists():
        logger.info(f'Image already exists')
    else:
        with open(filename, 'wb') as file:
            file.write(img)
        logger.debug(f'Save new image: {filename}')


def process_gen(year_text, gen_text):
    restyling = False

    years = year_text.split()
    try:
        start = int(years[0])
    except ValueError:
        start = None
    try:
        end = int(years[2])
    except ValueError:
        end = None

    for i in gen_text:
        if i.isdigit():
            gen = int(i)
            if 'рестайлинг' in gen_text:
                restyling = True

            return start, end, gen, restyling