#!/usr/bin/env python
# -⁻- coding: UTF-8 -*-

import urllib2, json, time, sys, codecs, threading

class NpLastFM:
	def __init__(self, api_key, lusers, delay, format):
		self.lusers = lusers
		self.delay = delay
		self.format = format
		self.key = api_key
		self.users = {}
		self.running = True
		self.limiter = { 'rate': 1500, 'per': (5 * 60) }
		self.allowance = self.limiter['rate']
		self.last_check = int( time.time() )
		self.url = "http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&limit=1&user={user}&api_key={key}&format=json"
		
	def request(self, users):
		data = {}
		(true, false, null) = ( str( True ), str( False ), str( None ) )
		for user in users:
			try:
				current = int( time.time() )
				time_passed = (current - self.last_check)
				self.last_check = current
				self.allowance += time_passed * (self.limiter['rate'] / self.limiter['per'])
				if self.allowance > self.limiter['rate']:
					self.allowance = self.limiter['rate']
				if self.allowance < 1:
					print "[-] LastFM rate limit exceeded"
					self.allowance = self.limiter['rate']
					time.sleep(60)
				else:
					url = self.url.format( user = user, key = self.key )
					data.setdefault( user, eval( urllib2.urlopen( urllib2.Request(url, None, {}) ).read() ) )
					self.allowance -= 1
					time.sleep(1)
			except: pass
		return data
		
	def analyze(self, data):
		_data = {}
		for user in data:
			try:
				q = data[ user ]
				if type(q['recenttracks']['track']) == type([]): q = q['recenttracks']['track'][0]
				else: q = q['recenttracks']['track']
				
				if q.get('@attr') and q['@attr'].get('nowplaying'):
					if self.users.get( user ):
						if q['name'] != self.users[user]['name']:
							_data.setdefault( user, { "name": q['name'].decode("unicode-escape"), "artist": q['artist']['#text'].decode("unicode-escape") } )
						
						self.users[ user ] = { 'artist': q['artist']['#text'], 'name': q['name'], 'date': int( time.time() ) }
					else:
						self.users.setdefault(user, { 'artist': q['artist']['#text'], 'name': q['name'], 'date': int( time.time() ) } )
						_data.setdefault( user, { "name": q['name'].decode("unicode-escape"), "artist": q['artist']['#text'].decode("unicode-escape") } )
			except: pass
		return _data
	
	def run(self):
		print "[+] LastFM Now playing started: %s" % ", ".join(self.lusers)
		while self.running:
			data = self.analyze( self.request( self.lusers ) )

			if len( data ) > 0:
				for user in data:
					_form = self.format.format( user = user, song = data[user]['name'], artist = data[user]['artist'])
					with codecs.open("np_%s.txt" % user, 'w', encoding='utf8') as f:
						f.write(_form)
					print _form.encode("utf-8")
			#Delay
			time.sleep(self.delay)
			
	def stop( self ):
		self.running = False
		print "[-] LastFM Now playing stopped"

#Main Script
try: np_config = json.loads( open( "config.json" ).read() )
except Exception, e:
	print "Config File error: " + str( e )
	sys.exit()
	
_config = np_config['LastFM']
Threads = []

np = NpLastFM( _config['key'], _config['users'], _config['delay'], _config['format'] )

Threads.append( threading.Thread( target=np.run ) )

for thr in Threads:
	thr.setDaemon(True)
	thr.start()
	time.sleep(0.5)
	
#Keeps all active
raw_input("")

np.stop()

for thr in Threads: 
	thr.join(1)

print "Script close successful"
sys.exit()
