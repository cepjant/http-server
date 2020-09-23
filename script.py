from http.server import BaseHTTPRequestHandler, HTTPServer
import time
import urllib.parse

hostName = "localhost"
serverPort = 8000




class Server(BaseHTTPRequestHandler):
    def do_GET(self):
        print(self.path)
        if self.path.startswith('/city/'):
            self.get_city_info()
        elif self.path.startswith('/cities/?p='):
            self.get_all_cities()
        elif self.path.startswith('/cities/?compare='):
            self.get_compare()
        else:
            send_headers(404)
            response = {"status": "not fount"}
            self.write_html(str(response))

    def send_headers(self, code): # вынес сюда чтобы не дублировать в каждой функции
        self.send_response(code)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def write_html(self, body): # вынес сюда чтобы не дублировать в каждой функции
        self.wfile.write(bytes("<html><head><meta content='text/html;  \
            charset=utf-8' http-equiv='Content-Type'></head>", "utf-8"))
        self.wfile.write(bytes("<meta content='utf-8' http-equiv='encoding'>  \
            </head>", "utf-8"))
        self.wfile.write(bytes("<body>", "utf-8"))
        self.wfile.write(bytes(body, "utf-8"))
        self.wfile.write(bytes("</body>", "utf-8"))

    def convert_into_json(self, city_info):
        data = {
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
            "admin4 code":  city_info[13],
            "population": city_info[14],
            "elevation": city_info[15],
            "dem": city_info[16],
            "timezone": city_info[17],
            "modification date": city_info[18].strip()
        }
        return data

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

    def get_compare(self):
        cities = self.path[self.path.find('=') + 1:].split(',')
        city_1 = urllib.parse.unquote(cities[0]) # правим кодировку
        city_2 = urllib.parse.unquote(cities[1])
        result = []
        for city in data:
            alternatenames = city[3].split(',')
            if city_1 in alternatenames or city_2 in alternatenames:
                result.append(city)
        if result:
            response_list = []
            for city in result:
                json_data = self.convert_into_json(city)
                json_data.update({
                'is_norther': '-',
                'has_different_tz': '-',
                'tz_diff': '-'})
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









if __name__ == "__main__":
    data = []
    try:
        with open('RU.txt', 'r') as f:
            data_list= f.readlines()
            for d in data_list:
                data.append(d.split('\t'))
            print('Данные загружены')
    except FileNotFoundError: # перепроверить
        print('Ошибка! Файл "RU.txt" с данными не найден в текущей директории.')


    webServer = HTTPServer((hostName, serverPort), Server)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")
