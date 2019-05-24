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

def handle_data(datos):
	global comentario
	global contenido

	display=''
	valores=''
	ahora=''
	if len(datos)>0:
		#if len(datos)>1:
		#	respuestas.append('\0\033[1;36m' + str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))+ '\0\033[1;37m' + ' '+str(ord(datos[1])).center(5) + str(len(datos)).center(5))
		if len(datos) >= 7:
			#print '* ' + str(len(datos))
			for iter in range(0,len(datos)-6):
				#try:
				#print str(ord(datos[iter + 5])) +'=='+ str(lo(crc16(datos[:iter + 5]))) 
				#print str(ord(datos[iter + 6])) +'=='+ str(hi(crc16(datos[:iter + 5])))
				if ord(datos[iter + 5]) == lo(crc16(datos[:iter + 5])) and ord(datos[iter + 6]) == hi(crc16(datos[:iter + 5])) :

					ahora=str(datetime.datetime.now().isoformat()).ljust(26)
					datos=datos[iter:]
					#print '+' + str(len(datos))
					for i in range(0, len(datos)):
						display = display + str(ord(datos[i])).rjust(4) + ' '
						valores = valores + str(ord(datos[i])).rjust(4) + ','
					print ahora + ' | ' + comentario.ljust(10) + ' | ' + str(len(datos)) + ' | ' + display
					valores = ahora + ',' + valores + comentario 
					contenido.append(valores)

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
	global comentario
	while comentario <> 'salir':
		for ser in puertos:
			reading = puertos[ser].read(7)
			handle_data(reading)

def guardarcontenido():
	global contenido
	global nombrearchivo

	file = open(nombrearchivo,'a+')
	for l in contenido:
		file.write(l + '\n')
	file.close()
	contenido=[]


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
lecturas=int(getsetting('archivo','autoguardar','1000'))

nombrearchivo=str(datetime.datetime.now().strftime('%Y%m%d%H%M%S')) + '.csv'
print 'Archivo '+ nombrearchivo

print 'Autoguardar '+ str(lecturas)

thread = threading.Thread(target=read_from_port)
thread.start()

t = threading.Thread(target=read_from_kb)
t.start()


while comentario <> 'salir' :
	m=chr(1) + chr(3) + chr(0) + chr(36) + chr(0) + chr(1)
	#m=chr(1) + chr(8) + chr(0) + chr(0) + chr(165) + chr(55)
	escribir_en_puertos(m + chr(lo(crc16(m))) + chr(hi(crc16(m))))
	#print 'Escribiendo'
	if len(contenido) >= lecturas:
		guardarcontenido()
	else:
		time.sleep(pausallamadas)
guardarcontenido()
