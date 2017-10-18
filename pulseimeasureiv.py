#!/usr/bin python
import visa
import csv
import numpy as np

def exportFile(filename, data):
  with open(filename, 'wt') as csvfile:
    csvfile.write(data)
 
limitv = 0.9 #Maximum voltage limit (in volts)
limiti = 0.001 #Maximum current limit (in amperes)
v = '' #Will hold the voltage readings
i = '' #Will hold the current readings
pulses = 100 #Number of pulses per train
loops = 10 #Number of pulse trains
delay = 0.02 #Delay before measuring voltage (in seconds)
milliamps = 0.308  #Current level of the pulses (in milliamps)
nplc = 0.005  #Number of power cycles for integration

#Open communication ports
rm = visa.ResourceManages('@py')
instr = rm.open_resource('TCPIP::169.254.0.1::INSTR')

#Initialise SMU A
instr.write("smua.reset()")
instr.write("smua.source.func = smua.OUTPUT_DCAMPS") #SMU A will act as a current source and voltmeter
instr.write("smua.source.limitv = " + str(limitv)+ "")
instr.write("smua.nvbuffer1.appendmode = 1")  #New readings are appended to the existing data
instr.write("smua.measure.delay = " + str(delay) + "")
instr.write("smua.measure.nplc = " + str(nplc) + "")

#Initialise SMU B
instr.write("smub.reset()")
instr.write("smub.source.func = smua.OUTPUT_DCVOLTS")  #SMU B will act as ampmeter, but it is important to initialise it as a voltage source, so the impedance is low
instr.write("smub.source.limiti = " + str(limiti)+ "")
instr.write("smub.nvbuffer1.appendmode = 1")  #New readings are appended to the existing data
instr.write("smub.measure.nplc = " + str(nplc) + "")

#Turn both sources on
instr.write("smua.source.output = smua.OUTPUT_ON")
instr.write("smub.source.output = smub.OUTPUT_ON")

for l in range(0, loops):
  #Clear data buffers each loop
  instr.write("smua.nvbuffer1.clear()")
  instr.write("smub.nvbuffer1.clear()")
  instr.write("waitcomplete()") #Wait for the buffers to be cleared. Not sure if necessary
  
  #For loop creating the pulse train at a fixed current. Horribly long.
  instr.write("for a = 1,100 do smua.source.leveli=" + str(milliamps) + "e-3 smua.measurev(smua.nvbuffer1) smub.measurei(smub.nvbuffer1) smua.source.leveli=0 end"))
  instr.write("waitcomplete()") #Again, not sure if necessary 
  
  v = v + instr.query("x = printbuffer(1,smua.nvbuffer1.n,smua.nvbuffer1.readings)")
  i = i + instr.query("x = printbuffer(1,smub.nvbuffer1.n,smub.nvbuffer1.readings)")
  exportfile(filename + "-" + str(l) + ".txt", v + i)
  
#Turn both sources off
instr.write("smua.source.output = smua.OUTPUT_OFF")
instr.write("smub.source.output = smub.OUTPUT_OFF")
instr.close()
