# encoding: utf-8

#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#       
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#       
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.

import datetime
from urllib import quote_plus
from urlparse import urljoin

import lxml.html
import mechanize

__license__ = 'GPLv2'
__version__ = 'a1'
__maintainer__ = 'Nicolas Duhamel'

#TODO: Don't use mechanize

class SearchResultParser:
	def __init__(self, html):
		self.doc = lxml.html.parse(html).getroot()
	
	def parse(self):
		row_data = []
		try:
			table = self.doc.xpath('//*[@id="searchResult"]')[0]
			rows = [row for row in table.iterchildren() if row.tag == 'tr']
			for row in rows:
				columns = row.getchildren()[1:]
				row_data.append(self.parse_row_columns(columns))
		except:
			pass
		return row_data
	
	def parse_row_columns(self, columns):
		"""Parse the columns of a table row.
		
		*Returns*
			a dictionary with parsed data.
		"""
		data = {}
		data["user_type"] = "standard"
		for ele in columns[0].iterchildren():
			if ele.tag == 'div' and ele.get('class') == 'detName':
				a = ele.find('a')
				data["torrent_info_url"] = urljoin(ele.base, a.get('href'))
				data["name"] = a.text_content()
			elif ele.tag == 'a':
				if ele.get('title') == "Download this torrent":
					data["torrent_url"] = ele.get("href")
				elif ele.get('title') == "Download this torrent using magnet":
					data["magnet_url"] = ele.get("href")
				elif ele[0].tag == 'img':
					if ele[0].get('title') == "VIP":
						data["user_type"] = "VIP"
					elif ele[0].get('title') == "Trusted":
						data["user_type"] = "trusted"
					
			elif ele.tag == 'font':
				a = ele.find('a')
				if a is None:
					data['user'] = "Anonymous"
				else:
					data['user'] = urljoin(ele.base, a.get('href'))
				data["uploaded_at"], data["size_of"] = self.process_datetime_string(ele.text_content())
		data['seeders'] = int(columns[1].text_content().strip())
		data['leechers'] = int(columns[2].text_content().strip())
		return data

	def process_datetime_string(self, string):
		"""Process the datetime string from a torrent upload.
	
		*Returns*
			Tuple with (datetime, (size, unit))
		"""
		def process_datetime(part):
			if part.startswith("Today"):
				h, m = part.split()[1].split(':')
				return datetime.datetime.now().replace(
					hour=int(h), minute=int(m))
			elif part.startswith("Y-day"):
				h, m = part.split()[1].split(':')
				d = datetime.datetime.now()
				return d.replace(
					hour=int(h), minute=int(m),
					day=d.day-1
				)
			elif part.endswith("ago"):
				amount, unit = part.split()[:2]
				d = datetime.datetime.now()
				if unit == "mins":
					d = d.replace(minute=d.minute - int(amount))
				return d
			else:
				d = datetime.datetime.now()
				if ':' in part:
					current_date, current_time = part.split()
					h, m = current_time.split(':')
					month, day = current_date.split('-')
					d = d.replace(hour=int(h), minute=int(m), month=int(month), day=int(day))
				else:
					current_date, year = part.split()
					month, day = current_date.split('-')
					d = d.replace(year=int(year), month=int(month), day=int(day))
				return d
		def process_size(part):
			size, unit = part.split()[1:]
			return (float(size), unit)
		string = string.replace(u"\xa0", " ")
		results = [x.strip() for x in string.split(',')]
		date = process_datetime(' '.join(results[0].split()[1:]))
		size = process_size(results[1])
		return (date, size)
		

class ThePirateBay:
	"""Api for the Pirate Bay"""

	name = 'The Pirate Bay'
	
	searchUrl = 'https://thepiratebay.org/search/%s/0/7/%d'
	
	def __init__(self):
		self.browser = mechanize.Browser()
			
	def search(self, term, cat=None):
		if not cat:
			cat = 0
		url = self.searchUrl % (quote_plus(term), cat)
		
		self.browser.open(url)
		html = self.browser.response()
		parser = SearchResultParser(html)
		return parser.parse()

