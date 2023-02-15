import requests
import time
import json
from tqdm import tqdm
from pprint import pprint
from datetime import datetime

class VkGetPhoto:
    
    def __init__(self, access_token, user_id, version='5.131'):
        self.token = access_token
        self.id = user_id
        self.version = version
        self.params = {'access_token': self.token, 'v': self.version}

    def get_photo_info(self, user_id, qty=5):
        url = 'https://api.vk.com/method/photos.get'
        photo_info_params = {
            'owner_id': user_id,
            'album_id': 'profile',
            'extended': '1',
            'photo_sizes': '1',
            'count': qty
        }
        photo_info = requests.get(url, params={**self.params, **photo_info_params})
        return photo_info.json()

    def files_list(self, file_photo_info):
        files_list = []
        for key, value in file_photo_info.items():
            file_names = []
            for element in value['items']:
                new_element = {'file_name':'', 'size':'', 'url':''}
                if str(element['likes']['count']) in file_names:
                    data = time.localtime(element['date'])
                    data_str = time.strftime('%Y_%m_%d', data)
                    name = str(element['likes']['count']) + '_' + data_str
                else:
                    name = str(element['likes']['count'])
                new_element['file_name'] = name + '.jpg'
                file_names.append(name)
                new_element['size'] = element['sizes'][-1]['type']
                new_element['url'] = element['sizes'][-1]['url']
                files_list.append(new_element)
            print(file_names)
        return files_list


class YaUploader:
    def __init__(self, token: str):
        self.token = token

    def get_headers(self):
        return {
            'Content-Type': 'application/json',
            'Authorization': 'OAuth {}'.format(self.token)
        }

    def get_status(self, operation_url):
        headers = self.get_headers()
        response = requests.get(url=operation_url, headers=headers)
        response.raise_for_status()
        status = response.json().get('status')
        if status != 'success':
            return False
        else:
            return True


    def create_folder(self, folder_name: str):
        url = 'https://cloud-api.yandex.net/v1/disk/resources'
        headers = self.get_headers()
        params = {"path": folder_name}
        response = requests.put(url=url, headers=headers, params=params)
        if response.status_code == 201:
            print(f'Папка {folder_name} создана на Я.Диске.')

    def upload(self, data):
        upload_report = []
        upl_files_qty = 0
        for e in data: 
            upload_url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
            headers = self.get_headers()
            file_path = f'disk:/VK_photo/{e["file_name"]}'
            file_url = e['url']
            params = {'path': file_path, 'url': file_url}
            response = requests.post(upload_url, headers=headers, params=params)
            status_url = response.json()['href']
            with tqdm(total=1) as pbar:
                for i in range(100):
                    time.sleep(.2)
                    self.get_status(status_url)
                    if self.get_status(status_url) == True:
                        pbar.update(1)
                        print(f'Файл {e["file_name"]} успешно загружен')
                        uploaded_file_info = {}
                        uploaded_file_info['file_name'] = e['file_name']
                        uploaded_file_info['size'] = e['size']
                        upload_report.append(uploaded_file_info)
                        upl_files_qty += 1
                        break
        return upload_report
      

if __name__ == '__main__':
    with open('VK_token.txt') as f:
        vk_token = f.readline()
    vk_id = int(input('Введите id пользователя VK: '))
    vk = VkGetPhoto(vk_token, vk_id)

    with open('YA_token.txt') as f:
        ya_token = f.readline()
    ya = YaUploader(ya_token)

    photo_qty = int(input('Введите количество фотографий для загрузки: '))
    photo_info = vk.get_photo_info(vk_id, photo_qty)
    photos_to_upload = vk.files_list(photo_info)

    ya.create_folder('VK_photo')
    uploaded_files = ya.upload(photos_to_upload)

    with open('upload_info.json', 'w') as write_file:
        json.dump(uploaded_files, write_file, indent=2, ensure_ascii=False)

    