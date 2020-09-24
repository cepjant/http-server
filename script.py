from http.server import BaseHTTPRequestHandler, HTTPServer
import time
import urllib.parse
import pytz
from datetime import datetime
from itertools import groupby

hostName = "localhost"
serverPort = 8000


class Server(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/city/'):
            self.get_city_info()
        elif self.path.startswith('/cities/?p='):
            self.get_all_cities()
        elif self.path.startswith('/cities/?compare='):
            self.get_compared()
        elif self.path.startswith('/cities/?search='):
            self.search()
        else:
            self.send_headers(404)
            response = {"status": "not found"}
            self.write_html(str(response))

    def send_headers(self, code):  # вынес сюда чтобы не дублировать в каждой функции
        self.send_response(code)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def write_html(self, body):  # вынес сюда чтобы не дублировать в каждой функции
        self.wfile.write(bytes("<html><head><meta content='text/html;  \
            charset=utf-8' http-equiv='Content-Type'></head>", "utf-8"))
        self.wfile.write(bytes("<meta content='utf-8' http-equiv='encoding'>  \
            </head>", "utf-8"))
        self.wfile.write(bytes("<body>", "utf-8"))
        self.wfile.write(bytes(body, "utf-8"))
        self.wfile.write(bytes("</body>", "utf-8"))

    def convert_into_json(self, city_info):
        json_data = {
            "geonameid": city_info[0],
            "name": city_info[1],
            "asciiname": city_info[2],
            "alternatenames": city_info[3],
            "latitude": city_info[4],
            "longitude": city_info[5],
            "feature class": city_info[6],
            "feature code": city_info[7],
            "country code": city_info[8],
            "cc2": city_info[9],
            "admin1 code": city_info[10],
            "admin2 code": city_info[11],
            "admin3 code": city_info[12],
            "admin4 code": city_info[13],
            "population": city_info[14],
            "elevation": city_info[15],
            "dem": city_info[16],
            "timezone": city_info[17],
            "modification date": city_info[18].strip(),
        }
        if len(city_info) > 19:
            json_data.update({
                'is_norther': city_info[19],
                'has_different_tz': city_info[20],
                'tz_diff': city_info[21]
            })
        return json_data

    def get_city_info(self):
        city_id = self.path.split('/')[-1]
        city_info = None
        for i in data:
            if i[0] == city_id:
                city_info = i
        if city_info:
            response = {
                'data': self.convert_into_json(city_info),
                'status': 'ok'}
            self.send_headers(200)
            self.write_html(str(response))
        else:
            response = {
                'status': 'not found'}
            self.send_headers(404)
            self.write_html(str(response))

    def get_all_cities(self):
        if int(self.path.split('=')[-1]) < 1:
            page = 0
        page = int(self.path.split('=')[-1]) - 1
        result = data[page * 10: page * 10 + 10]
        if result:
            response = {
                "data": [self.convert_into_json(city) for city in result],
                "status": "ok"}
            self.send_headers(200)
            self.write_html(str(response))
        else:
            response = {
                "status": "not found"}
            self.send_headers(404)
            self.write_html(str(response))

    def get_compared(self):
        cities = self.path[self.path.find('=') + 1:].split(',')
        city_1_req = urllib.parse.unquote(cities[0]).strip()  # правим кодировку
        city_2_req = urllib.parse.unquote(cities[1]).strip()
        result = []
        city_1_matches = []
        city_2_matches = []
        for city in data:
            alternatenames = city[3].split(',')
            if city_1_req.lower() in [i.lower() for i in alternatenames]:
                city_1_matches.append(city.copy())
            if city_2_req.lower() in [i.lower() for i in alternatenames]:
                city_2_matches.append(city.copy())
        if city_2_matches and city_1_matches:
            city_1 = sorted(city_1_matches, key=lambda i: int(i[14]), reverse=True)[0] # сорт по population
            city_2 = sorted(city_2_matches, key=lambda i: int(i[14]), reverse=True)[0]
            if float(city_1[4]) > float(city_2[4]):
                city_1.append("True")
                city_2.append('False')
            elif float(city_1[4]) < float(city_2[4]):
                city_1.append("False")
                city_2.append('True')

            if city_1[17] != city_2[17]:
                city_1.append('True')
                city_2.append('True')
                IST_1 = pytz.timezone(city_1[17])
                IST_2 = pytz.timezone(city_2[17])
                time_in_city_1 = datetime.now(IST_1)
                time_in_city_2 = datetime.now(IST_2)
                first_tz = int(str(time_in_city_1).split(' ')[1][-5:-3])
                second_tz = int(str(time_in_city_2).split(' ')[1][-5:-3])
                if first_tz > second_tz:
                    time_difference = first_tz - second_tz
                    city_1.append('+' + str(time_difference))
                    city_2.append('-' + str(time_difference))
                else:
                    time_difference = second_tz - first_tz
                    city_1.append('-' + str(time_difference))
                    city_2.append('+' + str(time_difference))
            else:
                city_1.append('False')
                city_1.append(0)
                city_2.append('False')
                city_2.append(0)
            result += city_1, city_2

            response_list = []
            for city in result:
                json_data = self.convert_into_json(city)
                response_list.append(json_data)
            response = {
                "data": response_list,
                "status": "ok"}
            self.send_headers(200)
            self.write_html(str(response))
        else:
            response = {
                "status": "not found"}
            self.send_headers(404)
            self.write_html(str(response))

    def search(self):
        request = urllib.parse.unquote(self.path.split('=')[-1])
        matches = []
        for city in data:
            alternatenames = city[3].split(',')
            for name in alternatenames:
                if name.lower().startswith(request.lower()):
                    matches.append(city)
        if matches:
            result = []
            for city in sorted(matches, key=lambda i: int(i[14]), reverse=True):
                alternatenames = city[3].split(',')
                print(alternatenames)
                for name in alternatenames:
                    if name.lower().startswith(request.lower()) and name not in result:
                        result.append(name)
                        break
            response = {
                'data': result[:20],
                'status': 'ok'}
            self.send_headers(200)
            self.write_html(str(response))
        else:
            response = {
                'status': 'not found'}
            self.send_headers(404)
            self.write_html(str(response))


if __name__ == "__main__":
    data = []
    try:
        with open('RU.txt', 'r') as f:
            data_list = f.readlines()
            for d in data_list:
                data.append(d.split('\t'))
            print('Данные загружены')

    except FileNotFoundError:  # перепроверить
        print('Ошибка! Файл "RU.txt" с данными не найден в текущей директории.')

    webServer = HTTPServer((hostName, serverPort), Server)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")
