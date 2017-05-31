from kivy.network.urlrequest import UrlRequest
import json
import datetime

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.listview import ListItemButton
from kivy.properties import (ObjectProperty, ListProperty, StringProperty, NumericProperty)
from kivy.storage.jsonstore import JsonStore
from kivy.factory import Factory


def locations_args_converter(index, data_item):
	city, country = data_item
	return {'location': (city, country)}


class LocationButton(ListItemButton):
	location = ListProperty()

class WeatherRoot(BoxLayout):

	current_weather = ObjectProperty()
	locations = ObjectProperty()
	forecast = ObjectProperty()

	def __init__(self, **kwargs):
		super(WeatherRoot, self).__init__(**kwargs)
		self.store = JsonStore("weather_store.json")
		if self.store.exists('locations'):
			current_location = self.store.get("locations")["current_location"]
			self.show_current_weather(current_location)

	def show_current_weather(self, location=None):
		self.clear_widgets()

		if self.current_weather is None:
			self.current_weather = CurrentWeather()

		if self.locations is None:
			self.locations = Factory.Locations()
			if (self.store.exists('locations')):
				locations = self.store.get("locations")['locations']
				self.locations.locations_list.adapter.data.extend(locations)

		if location is not None:
			self.current_weather.location = location
			if location not in self.locations.locations_list.adapter.data:
				self.locations.locations_list.adapter.data.append(location)
				self.locations.locations_list._trigger_reset_populate()
				self.store.put("locations", locations=list(self.locations.locations_list.adapter.data),current_location=location)

		self.current_weather.update_weather()
		self.add_widget(self.current_weather)

	def show_forecast(self, location=None):
		self.clear_widgets()

		if self.forecast is None:
			self.forecast = Factory.Forecast()

		if location is not None:
			self.forecast.location = location 

		self.forecast.update_weather()
		self.add_widget(self.forecast)

	def show_add_location_form(self):
		self.clear_widgets()
		self.add_widget(AddLocationForm())

	def show_locations(self):
		self.clear_widgets()
		self.add_widget(self.locations)

class WeatherApp(App):
	def build_config(self, config):
		config.setdefaults('General', {'temp_type': "Imperial"})

	def build_settings(self, settings):
		settings.add_json_panel("Weather Settings", self.config, data="""
			[
				{"type": "options",
					"title": "Temperature System",
					"section": "General",
					"key": "temp_type",
					"options": ["Metric", "Imperial"]
				}
			]"""
			)

	def on_config_change(self, config, section, key, value):
		if config is self.config and key == "temp_type":
			try:
				self.root.children[0].update_weather()
			except AttributeError:
				pass

class CurrentWeather(BoxLayout):
	location = ListProperty(['New York', 'US'])
	conditions = StringProperty()
	temp = NumericProperty()
	temp_min = NumericProperty()
	temp_max = NumericProperty()
	conditions_image = StringProperty()

	def update_weather(self):
		config = WeatherApp.get_running_app().config 
		temp_type = config.getdefault("general", "temp_type", "metric").lower()
		weather_template = "http://api.openweathermap.org/data/2.5/" + "weather?q={},{}&units=Imperial&appid=c8f1502f31609bd338a5a87be7c5b41f"
		weather_url = weather_template.format(self.location[0],self.location[1],temp_type)
		request = UrlRequest(weather_url, self.weather_retrieved)

	def weather_retrieved(self, request, data):
		data = json.loads(data.decode()) if not isinstance(data, dict) else data
		self.conditions = data['weather'][0]['description']
		self.temp = data['main']['temp']
		self.temp_min = data['main']['temp_min']
		self.temp_max = data['main']['temp_max']
		self.conditions_image = "http://openweathermap.org/img/w/{}.png".format(data['weather'][0]['icon'])

class AddLocationForm(BoxLayout):
	search_input = ObjectProperty()
	search_results = ObjectProperty()

	def search_location(self):
		search_template = "http://api.openweathermap.org/data/2.5/" + "find?q={}&appid=c8f1502f31609bd338a5a87be7c5b41f"
		search_url = search_template.format(self.search_input.text)
		request = UrlRequest(search_url, self.found_location)

	def found_location(self, request, data):
		data = json.loads(data.decode()) if not isinstance(data, dict) else data
		cities = [(d['name'], d['sys']['country']) for d in data['list']]
		self.search_results.item_strings = cities
		del self.search_results.adapter.data[:]
		self.search_results.adapter.data.extend(cities)
		self.search_results._trigger_reset_populate()

class Forecast(BoxLayout):
	location = ListProperty(['New York', 'US'])
	forecast_container = ObjectProperty()

	def update_weather(self):
		config = WeatherApp.get_running_app().config
		temp_type = config.getdefault("General", "temp_type", "Imperial").lower()
		weather_template = "http://api.openweathermap.org/data/2.5/forecast/" + "daily?q={},{}&units={}&cnt=3&appid=c8f1502f31609bd338a5a87be7c5b41f"
		weather_url = weather_template.format(self.location[0], self.location[1], temp_type)
		print weather_url
		request = UrlRequest(weather_url, self.weather_retrieved)

	def weather_retrieved(self, request, data):
		data = json.loads(data.decode()) if not isinstance(data, dict) else data
		self.forecast_container.clear_widgets()
		for day in data['list']:
			label = Factory.ForecastLabel()
			label.date = datetime.datetime.fromtimestamp(day['dt']).strftime("%a %b %d")
			label.conditions = day['weather'][0]['description']
			label.conditions_image = "http://openweathermap.org/img/w/{}.png".format(day['weather'][0]['icon'])
			label.temp_min = day['temp']['min']
			label.temp_max = day['temp']['max']
			self.forecast_container.add_widget(label)


if __name__ == '__main__':
	WeatherApp().run()