#!/usr/bin python
import visa
import csv
import numpy as np

def exportFile(filename, data):
  with open(filename, 'wt') as csvfile:
    csvfile.write(data)
    
def openCommPort(IP):
  #Open communication ports
  rm = visa.ResourceManages('@py')
  instr = rm.open_resource('TCPIP::' + IP + '::INSTR')
 
limitv = 0.9 #Maximum voltage limit (in volts)
limiti = 0.001 #Maximum current limit (in amperes)
v = '' #Will hold the voltage readings
i = '' #Will hold the current readings
pulses = 100 #Number of pulses per train
loops = 10 #Number of pulse trains
width = 0.02 #Pulse width (in seconds)
milliamps = 0.308  #Current level of the pulses (in milliamps)
nplc = 0.005  #Number of power cycles for integration

openCommPort('169.254.0.1')


#Initialise SMU A
instr.write("smua.reset()")
instr.write("smua.source.func = smua.OUTPUT_DCAMPS") #SMU A will act as a current source and voltmeter
instr.write("smua.source.limitv = " + str(limitv)+ "")
instr.write("smua.nvbuffer1.appendmode = 1")  #New readings are appended to the existing data
instr.write("smua.measure.nplc = " + str(nplc) + "")
instr.write("smua.measure.autozero = smua.AUTOZERO_ONCE")
instr.write("smua.source.rangei = 1e-3")

#Initialise SMU B
instr.write("smub.reset()")
instr.write("smub.source.func = smua.OUTPUT_DCVOLTS")  #SMU B will act as ampmeter, but it is important to initialise it as a voltage source, so the impedance is low
instr.write("smub.source.limiti = " + str(limiti)+ "")
instr.write("smub.nvbuffer1.appendmode = 1")  #New readings are appended to the existing data
instr.write("smub.measure.nplc = " + str(nplc) + "")
instr.write("smub.measure.autozero = smub.AUTOZERO_ONCE")

#Configure pulse
instr.write("smua.trigger.source.action = smua.ENABLE")
instr.write("smua.trigger.measure.action = smua.ENABLE")
instr.write("smub.trigger.measure.action = smub.ENABLE")
instr.write("smua.trigger.measure.v(smua.nvbuffer1)")

instr.write("trigger.timer[1].count = 1")
instr.write("trigger.timer[1].passthrough = false")
instr.write("trigger.timer[1].stimulus = smua.trigger.ARMED_EVENT_ID")
instr.write("smua.trigger.source.stimulus = 0")
instr.write("smua.trigger.measure.stimulus = trigger.timer[1].EVENT_ID")
instr.write("smub.trigger.measure.stimulus = trigger.timer[1].EVENT_ID")
instr.write("smua.trigger.endpulse.stimulus = trigger.timer[1].EVENT_ID")
instr.write("smua.trigger.endpulse.action = smua.SOURCE_IDLE")
instr.write("smua.trigger.count = 1")
instr.write("smua.trigger.arm.count = 1")
instr.write("smub.trigger.count = 1")
instr.write("smub.trigger.arm.count = 1")

instr.write("smua.source.trigger.listi({" + str(milliamps) + "e-6})")
instr.write("trigger.timer[1].delay = " + str(width) + "")


#Turn both sources on
instr.write("smua.source.output = smua.OUTPUT_ON")
instr.write("smub.source.output = smub.OUTPUT_ON")

for l in range(0, loops):
  #Clear data buffers each loop
  instr.write("smua.nvbuffer1.clear()")
  instr.write("smub.nvbuffer1.clear()")
  instr.write("waitcomplete()") #Wait for the buffers to be cleared. Not sure if necessary
  
  #For loop creating the pulse train at a fixed current. Horribly long.
  instr.write("for a = 1,100 do smub.trigger.initiate() smua.trigger.initiate() waitcomplete() end"))
  instr.write("waitcomplete()") #Again, not sure if necessary 
  
  v = v + instr.query("x = printbuffer(1,smua.nvbuffer1.n,smua.nvbuffer1.readings)")
  i = i + instr.query("x = printbuffer(1,smub.nvbuffer1.n,smub.nvbuffer1.readings)")
  exportfile(filename + "-" + str(milliamps) + "-" + str(l) + ".txt", v + i)
  
#Turn both sources off
instr.write("smua.source.output = smua.OUTPUT_OFF")
instr.write("smub.source.output = smub.OUTPUT_OFF")
instr.close()
