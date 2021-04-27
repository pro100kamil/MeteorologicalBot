from collections import defaultdict

import requests
from discord.ext import commands

TOKEN = ""
headers = {"X-Yandex-API-Key": ''}


def get_coords(toponym):
    """Возвращает координаты топонима"""
    geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/"

    geocoder_params = {
        "apikey": "40d1649f-0493-4b70-98ba-98533de7710b",
        "geocode": toponym,
        "format": "json"
    }

    response = requests.get(geocoder_api_server, params=geocoder_params)

    if response:
        toponym = response.json()["response"]["GeoObjectCollection"][
            "featureMember"][0]["GeoObject"]
        return tuple(map(float, toponym["Point"]["pos"].split(" ")))


def get_weather_response(place):
    """Возвращает результат запроса к апи погоды"""
    lon, lat = get_coords(place)
    weather_api_server = 'https://api.weather.yandex.ru/v1/forecast?'

    weather_params = {
        "lon": lon,
        "lat": lat,
        "lang": "ru_RU"
    }
    response = requests.get(weather_api_server, weather_params,
                            headers=headers)
    return response.json()


class WeatherThings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # ключ - кортеж (сервер, канал), значение - текущий город
        self.cities = defaultdict(lambda: 'Ufa')

    @commands.command(name='help_bot')
    async def help(self, ctx):
        lines = ['Commands:',
                 '\t"#!place {city}" - задает место прогноза',
                 '\t"#!forecast {days}" - сообщает прогноз дневной '
                 'температуры и осадков на указанное количество дней',
                 '\t"#!current" - присылает сообщение о текущей погоде']
        await ctx.send('```' + '\n'.join(lines) + '```')

    @commands.command(name='place')
    async def place(self, ctx, city):
        self.cities[(ctx.guild, ctx.channel)] = city
        await ctx.send(f'Place changed to {city}')

    @commands.command(name='current')
    async def current(self, ctx):
        city = self.cities[(ctx.guild, ctx.channel)]
        response = get_weather_response(city)

        offset = response["info"]["tzinfo"]["offset"] // 3600
        h, m = response["now_dt"][11:13], response["now_dt"][14:16]
        fact = response["fact"]

        lines = [f'Current weather in {city} today {response["now_dt"][:10]} '
                 f'at time {int(h) + offset}:{m}:',
                 f'Temperature: {fact["temp"]},',
                 f'Pressure: {fact["pressure_mm"]} mm,',
                 f'Humidity: {fact["humidity"]}%,',
                 f'{fact["condition"]},',
                 f'Wind {fact["wind_dir"]}, {fact["wind_speed"]} m/s.']
        await ctx.send('\n'.join(lines))

    @commands.command(name='forecast')
    async def forecast_days(self, ctx, days):
        city = self.cities[(ctx.guild, ctx.channel)]
        response = get_weather_response(city)

        forecasts = response["forecasts"]
        res = []
        for forecast in forecasts[1:int(days) + 1]:
            day = forecast["parts"]["day"]
            lines = [f'Weather forecast in {city} for {forecast["date"]}:',
                     f'Temperature: {forecast["parts"]["day"]["temp_avg"]},',
                     f'Pressure: {day["pressure_mm"]} mm,',
                     f'Humidity: {day["humidity"]}%,',
                     f'{day["condition"]},',
                     f'Wind {day["wind_dir"]}, {day["wind_speed"]} m/s.']
            res.append('\n'.join(lines))
        await ctx.send('\n\n'.join(res))


if __name__ == "__main__":
    bot = commands.Bot(command_prefix='#!')
    bot.add_cog(WeatherThings(bot))
    bot.run(TOKEN)
