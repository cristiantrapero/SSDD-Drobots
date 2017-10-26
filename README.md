# Sistemas Distribuidos, DROBOTS: CROBOTS distribuido

## Enunciado
La descripción completa del juego Drobots se encuentra ilustrada en el fichero **Enunciado.pdf**

## Instalación de dependencias
Manual cortesía de [Jose Luis Segura Lucas](https://www.linkedin.com/in/joseluissegura/).

### Instrucciones para Debian 8/9:
1. $ sudo su
2. # echo "deb http://pike.esi.uclm.es/arco sid main" > /etc/apt/sources.list.d/pike.list
3. # wget -O- http://pike.esi.uclm.es/arco/key.asc | apt-key add -
4. # apt-get update
5. # apt-get install python-zeroc-ice36
Si vas a utilizar Python 3 en lugar de Python 2, sustituye el paso 5 por: # apt-get install python3-zeroc-ice36

### Instrucciones para Ubuntu versión anterior a 16.04 (14.04, 14.10, 15.04 y 15.10):

1. Descargar los ficheros DEB de http://arco.esi.uclm.es/~joseluis.segura/python-zeroc-ice/ubuntu/14.04/
2. $ sudo su
3. # dpkg -i python-zeroc-ice36*.deb
Si se va a utilizar Python 3, sustituir paso 3 por:  # dpkg -i python3-zeroc-ice36*.deb

### Instrucciones para Ubuntu 16.04 o posterior:

1. Descargar los ficheros DEB de http://arco.esi.uclm.es/~joseluis.segura/python-zeroc-ice/ubuntu/16.04/
2. $ sudo su
3. # dpkg -i python-zeroc-ice36*.deb
Si se va a utilizar Python 3, sustituir paso 3 por:  # dpkg -i python3-zeroc-ice36*.deb

## Ejecución
Para la ejecución del programa, primeramente debemos de estar conectados a la red VPN de la UCLM si no estamos dentro de la red. Para conectarnos a la VPN seguir el siguiente [manual](https://area.tic.uclm.es/-/media/Files/PDF/TIC/Servicios/VPN/Instrucciones-VPN05.ashx).

Para la ejecución del programa simplemente ejecutar la instrucción:
```
$ make
```

## Explicación del programa
Proximamente...
