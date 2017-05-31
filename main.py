from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty
from kivy.network.urlrequest import UrlRequest
from kivy.uix.listview import ListItemButton
from kivy.properties import ObjectProperty, ListProperty, StringProperty, NumericProperty

class LocationButton(ListItemButton):
	location = ListProperty()

class WeatherRoot(BoxLayout):

	current_weather = ObjectProperty()

	def show_current_weather(self, location=None):
		self.clear_widgets()

		if self.current_weather is None:
			self.current_weather = CurrentWeather()

		if location is not None:
			self.current_weather.location = location 

		self.current_weather.update_weather()
		self.add_widget(self.current_weather)

	def show_add_location_form(self):
		self.clear_widgets()
		self.add_widget(AddLocationForm())

class WeatherApp(App):
	pass

class CurrentWeather(BoxLayout):
	location = ListProperty(['New York', 'US'])
	conditions = StringProperty()
	temp = NumericProperty()
	temp_min = NumericProperty()
	temp_max = NumericProperty()

	def update_weather(self):
		weather_template = "http://api.openweathermap.org/data/2.5/" + "weather?q={},{}&units=imperial&appid=c8f1502f31609bd338a5a87be7c5b41f"
		weather_url = weather_template.format(*self.location)
		request = UrlRequest(weather_url, self.weather_retrieved)

	def weather_retrieved(self, request, data):
		data = json.loads(data.decode()) if not isinstance(data, dict) else data
		self.conditions = data['weather'][0]['description']
		self.temp = data['main']['temp']
		self.temp_min = data['main']['temp_min']
		self.temp_max = data['main']['temp_max']

class AddLocationForm(BoxLayout):
	search_input = ObjectProperty()

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

	def args_converter(self, index, data_item):
		city, country = data_item
		return {'location': (city, country)}


if __name__ == '__main__':
	WeatherApp().run()