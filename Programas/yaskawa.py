import os
import threading
import serial
import time
import datetime
#import sys
#import terminalsize
#import MySQLdb
import ConfigParser
#import string
from math import trunc

def crc16(buff, crc = 0xffff, poly = 0xa001):
    l = len(buff)
    i = 0
    while i < l:
        ch = ord(buff[i])
        uc = 0
        while uc < 8:
            if (crc & 1) ^ (ch & 1):
                crc = (crc >> 1) ^ poly
            else:
                crc >>= 1
            ch >>= 1
            uc += 1
        i += 1
    return crc

def lo(st):
        return st & 0xff

def hi(st):
        return (st & 0xff00) >> 8

def handle_data(data):
	global comentario
	global datos
	global contenido

	display=''
	valores=''
	ahora=''

	if len(data)>0:
		if len(data) == 7:
			datos=data
		if len(data) < 7:
			datos=datos + data
		if len(datos) > 7:
			datos=''
		if len(datos) == 7:
			ahora=str(datetime.datetime.now().isoformat()).ljust(26)
			if ord(datos[5]) == lo(crc16(datos[:5])) and ord(datos[6]) == hi(crc16(datos[:5])) :
				for i in range(0, len(datos)):
					display = display + str(ord(datos[i])).rjust(4) + ' '
					valores = valores + str(ord(datos[i])).rjust(4) + ','
				print ahora + ' | ' + comentario.ljust(10) + ' | ' + str(len(datos)) + ' | ' + display
				valores = ahora + ',' + valores + comentario 
				contenido.append(valores)
			datos=''
def escribir_en_puertos(cadena):
	global puertos
	for ser in puertos:
		puertos[ser].write(cadena)

def read_from_kb():
	global comentario
	while comentario <> 'salir':
		comentario = raw_input('Comentario: ')

def read_from_port():
    global puertos
    while comentario <> 'salir':
	for ser in puertos:
	        reading = puertos[ser].read(7)
        	handle_data(reading)

def getsetting(sSeccion,sClave,sDefault=''):
	sSetting=''
	cfg = ConfigParser.RawConfigParser()
	cfg.read('yaskawa.ini')
	try:
		sSetting=cfg.get(sSeccion,sClave)
	except:
		if not cfg.has_section(sSeccion):
			cfg.add_section(sSeccion)
		if not cfg.has_option(sSeccion,sClave):
			cfg.set(sSeccion,sClave,sDefault)
		with open('yaskawa.ini', 'w') as configfile:
			cfg.write(configfile)		
		sSetting=sDefault
	return sSetting

comentario=''
datos=''
puertos={}
contenido=[]

i=0

for i in range(0,10):
	try:
		
		sPuerto=getsetting('ports','port'+str(i),'')
		print 'Puerto ' + str(i) + ' ' + sPuerto
		if len(sPuerto):
			puertos[i]=serial.Serial(sPuerto, 9600, timeout=0.1)
			
	except:
		time.sleep(1)

pausallamadas=float(getsetting('ports','pause','1'))


thread = threading.Thread(target=read_from_port)
thread.start()

t = threading.Thread(target=read_from_kb)
t.start()



while comentario <> 'salir' :
	m=chr(1) + chr(3) + chr(0) + chr(35) + chr(0) + chr(1)
	escribir_en_puertos(m + chr(lo(crc16(m))) + chr(hi(crc16(m))))
	time.sleep(pausallamadas)

file = open( str(datetime.datetime.now().strftime('%Y%m%d%H%M%S')) + '.csv','w')
for l in contenido:
	file.write(l + '\n')
file.close()
