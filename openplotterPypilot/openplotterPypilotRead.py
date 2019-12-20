#!/usr/bin/env python3

# This file is part of Openplotter.
# Copyright (C) 2015 by Sailoog <https://github.com/openplotter/openplotter-pypilot>
# 
# Openplotter is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# any later version.
# Openplotter is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Openplotter. If not, see <http://www.gnu.org/licenses/>.
import socket, time, configparser, os
from signalk.client import SignalKClient

def main():
	try:
		user = os.environ.get('USER')
		if user == 'root': user = os.path.expanduser(os.environ["SUDO_USER"])
		home = '/home/'+user
		conf_file = home+'/.openplotter/openplotter.conf'
		data_conf = configparser.ConfigParser()
		data_conf.read(conf_file)

		mode = data_conf.get('PYPILOT', 'mode')
		try: port = int(data_conf.get('PYPILOT', 'pypilotConn2'))
		except: port = 52000 #default port
		heading = data_conf.get('PYPILOT', 'heading')
		pitch = data_conf.get('PYPILOT', 'pitch')
		roll = data_conf.get('PYPILOT', 'roll')
		rate = data_conf.get('PYPILOT', 'rate')
		translation_rate = float(rate)


		def on_con(client):
			print('conected to pypilot Signal K server')
			if heading == '1': client.watch('imu.heading')
			if pitch == '1':  client.watch('imu.pitch')
			if roll == '1':  client.watch('imu.roll')

		if not mode or mode == '0': return
		if mode == '1':
			if heading != '1' and pitch != '1' and roll != '1': return
			sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			client = False
			tick1 = time.time()
			while True:
				try:
					if not client:
						client = SignalKClient(on_con, 'localhost')
				except:
					time.sleep(3)
					continue
				try:
					result = client.receive()
				except:
					print('disconnected from pypilot Signal K server')
					client = False
					continue

				headingValue = ''
				rollValue = ''
				pitchValue = ''
				values = ''
				for i in result:
					if 'imu.heading' in i: headingValue = result[i]['value']*0.017453293
					if 'imu.roll' in i: rollValue = result[i]['value']*0.017453293
					if 'imu.pitch' in i: pitchValue = result[i]['value']*0.017453293

				if heading == '1': 
					values += '{"path": "navigation.headingMagnetic","value":'+str(headingValue)+'}'
					if pitch == '1' or roll == '1': values += ','
				if pitch == '1' and roll == '1':
					values += '{"path": "navigation.attitude","value":{"roll":'+str(rollValue)+',"pitch":'+str(pitchValue)+',"yaw":null}}'
				elif roll == '1':
					values += '{"path": "navigation.attitude","value":{"roll":'+str(rollValue)+',"pitch":null,"yaw":null}}'
				elif pitch == '1':
					values += '{"path": "navigation.attitude","value":{"roll":null,"pitch":'+str(pitchValue)+',"yaw":null}}'
				SignalK = '{"updates":[{"$source":"OpenPlotter.I2C.pypilot","values":['+values+']}]}\n'
				sock.sendto(SignalK.encode('utf-8'), ('127.0.0.1', port))

				while True:
					dt = translation_rate - time.time() + tick1
					if dt <= 0:
						break
					time.sleep(dt)
				tick1 = time.time()

	except Exception as e: print (str(e))

if __name__ == '__main__':
	main()