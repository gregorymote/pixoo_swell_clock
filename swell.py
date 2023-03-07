import requests
import re
from time import sleep
from bs4 import BeautifulSoup
from pixoo import Pixoo
from pixoo.simulator import SimulatorConfig


def get_tide_data(soup):

    table = soup.find('table', attrs={'class':'table-tide'})
    rows = table.find_all('tr')

    data = []
    key = ['type', 'time', 'height']
    for row in rows:
        tide = {}
        cols = row.find_all('td')
        for idx, col in enumerate(cols):
            tide[key[idx]] = col.text.strip()
        data.append(tide)
    return data


def get_swell_data(soup):
    table = soup.find('table', attrs={'class':'msw-js-table'})
    
    data=[]
    keys=['time', 'height_range', 'stars', 'height', 'period', 'direction', 'wind_speed', 'wind_direction', 'weather', 'temperature', 'probability']
    bodies = table.find_all('tbody')
    for body in bodies:
        day = {}
        title = body.find("tr", attrs={'class':'tbody-title'})
        date = title.find(attrs={'class':'table-header-title'})
        day["date"] = date.text.strip()
        rows = body.find_all("tr")
        for row in rows:
            hour = {}
            if 'class' in row.attrs and 'msw-js-tide' not in row.attrs['class']:
                cols = row.find_all("td", class_= lambda x: x != 'tbody-title')
                idx = 0
                for col in cols:
                    if 'class' in col.attrs and 'table-forecast-sub-swells' not in col.attrs['class']:
                        if keys[idx] == 'stars':
                            inactive = len(col.find_all('li', class_="inactive"))
                            active = len(col.find_all('li', class_="active"))
                            value = active + (inactive / 2)
                        elif keys[idx] == 'direction':
                            value = col.attrs['title']
                        elif keys[idx] == 'wind_direction':
                            if 'background-success' in col.attrs['class']:
                                color = 'green'
                            elif 'background-warning' in col.attrs['class']:
                                color = 'orange'
                            else:
                                color = 'red'
                            value = col.attrs['title']
                            hour['color'] = color
                        else:
                            value = col.text.strip()
                        hour[keys[idx]] = value
                        idx+=1
            elif 'class' in row.attrs and 'msw-js-tide' in row.attrs['class']:
                day['tide'] = get_tide_data(row)
            if 'time' in hour:
                day[hour['time']] = hour           
        data.append(day)
    return data


def check_end(x, end):
    if x < end:
        return x
    else:
        return end - 1
    

def clear_screen(pixoo):
    for i in range(0, 64*64):
        pixoo.draw_pixel_at_index(i, (0, 0, 0))
    

if __name__ == "__main__":
    url = "https://magicseaweed.com/Ocean-City-NJ-Surf-Report/391/"
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")
    swell = get_swell_data(soup)
    pixoo = Pixoo('0.0.0.0', simulated=True, simulation_config=SimulatorConfig(10))
    for i in range(0, len(swell)):
        clear_screen(pixoo)
        today = swell[i]
        times = []
        colors = {"green": (60, 179, 113), "orange": (255, 165, 0), "red": (255, 0, 0), "white":(255,255,255), "blue": (0,191,255), "wave": (0,0,255), "silver":(192,192,192)}
        for item in today:
            if item != 'date' and item != 'tide' and item != 'Noon':
                value = re.findall(r'\d+', item)[0]
                if len(value) == 1:
                    value = '0' + value
                times.append(value)
            elif item == 'Noon':
                times.append('12')

        y = 1
        start = 9
        end = 54
        #end = 63     

        for hour in today:
            if hour != 'date' and hour != 'tide' and hour != 'Noon':
                time = re.findall(r'\d+', hour)[0]
                if len(time) == 1:
                    time = '0' + time
            elif hour == 'Noon':
                time = '12'
            else:
                continue
            pixoo.draw_text(time, (1, y), colors['blue'])
            y+=8
            height = int(re.findall(r'\d+', today[hour]['height'])[0])
            period = int(re.findall(r'\d+', today[hour]['period'])[0])
            wind_speeds = re.findall(r'\d+', today[hour]['wind_speed'])
            color = colors[today[hour]['color']]
            i = start
            while i < end:
                x1 = check_end(i, end)
                x2 = check_end(int(i + period/2), end)
                y1 = y - 3 - height
                y2 = y - 3
                pixoo.draw_line((x1, y1), (x2, y2), colors['wave'])
                #pixoo.draw_pixel((i, y - 3 - height), color)
                print(x1, x2)
                i= int(i + period/2)
                x1 = check_end(i, end)
                x2 = check_end(int(i + period/2), end)
                y1 = y - 3
                y2 = y - 3 - height
                pixoo.draw_line((x1, y1), (x2, y2), colors['wave'])
                #pixoo.draw_pixel((i, y - 3), color)
                i= int(i + period/2)
            wind_start = check_end(start + int(wind_speeds[0]), end)
            wind_end = check_end(start + int(wind_speeds[1]), end)
            pixoo.draw_line((start, y-2), (end, y-2), colors['white'])
            #pixoo.draw_line((start, y-2), (wind_start, y-2), colors['silver'])
            pixoo.draw_line((wind_start, y-2), (wind_end, y-2), color)
        pixoo.push()

        sleep(5)

